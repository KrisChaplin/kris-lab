#!/usr/bin/env python3
"""Control a Devantech ETH008-B eight-channel Ethernet relay board.

Speaks the native binary command set on TCP port 17494. The HTTP and ASCII
command sets are documented in docs/protocol.md but are not used here -- the
binary set is the only one that acknowledges every command.

Relay switching is rate limited to RELAY_RATE_LIMIT_HZ because the contacts
drive live lab equipment.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import time
from dataclasses import dataclass

DEFAULT_HOST = "192.168.0.200"
DEFAULT_PORT = 17494

RELAY_COUNT = 8
MODULE_ID_ETH008B = 19

#: Contacts drive powered equipment; never switch faster than this.
RELAY_RATE_LIMIT_HZ = 3.0
MIN_SWITCH_INTERVAL = 1.0 / RELAY_RATE_LIMIT_HZ

#: Pulse durations are a byte of 100 ms units.
PULSE_UNIT_S = 0.1
PULSE_MAX_UNITS = 255

CMD_MODULE_INFO = 0x10
CMD_DIGITAL_ACTIVE = 0x20
CMD_DIGITAL_INACTIVE = 0x21
CMD_SET_OUTPUTS = 0x23
CMD_GET_OUTPUTS = 0x24
CMD_ASCII = 0x3A
CMD_SERIAL_NUMBER = 0x77
CMD_GET_VOLTS = 0x78
CMD_PASSWORD = 0x79
CMD_UNLOCK_TIME = 0x7A
CMD_LOGOUT = 0x7B

UNLOCK_TIME_LOCKED = 0
UNLOCK_TIME_NO_PASSWORD = 255


class RelayError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModuleInfo:
    module_id: int
    hardware_version: int
    firmware_version: int

    @property
    def model(self) -> str:
        return "ETH008-B" if self.module_id == MODULE_ID_ETH008B else f"module {self.module_id}"


class ETH008B:
    """Persistent client for one ETH008-B board.

    The board drops a command if the socket closes before the acknowledgement
    is read, so every command here reads its full reply.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        *,
        timeout: float = 5.0,
        rate_limit: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.rate_limit = rate_limit
        self._sock: socket.socket | None = None
        self._last_switch = 0.0

    def __enter__(self) -> ETH008B:
        self.connect()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def connect(self) -> None:
        if self._sock is not None:
            return
        try:
            self._sock = socket.create_connection(
                (self.host, self.port), timeout=self.timeout
            )
        except OSError as exc:
            raise RelayError(f"Cannot reach {self.host}:{self.port}: {exc}") from exc
        self._sock.settimeout(self.timeout)

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def _command(self, payload: bytes, reply_len: int) -> bytes:
        self.connect()
        assert self._sock is not None
        try:
            self._sock.sendall(payload)
            buf = b""
            while len(buf) < reply_len:
                chunk = self._sock.recv(reply_len - len(buf))
                if not chunk:
                    raise RelayError("Board closed the connection mid-reply")
                buf += chunk
        except socket.timeout as exc:
            raise RelayError(
                f"No reply to command 0x{payload[0]:02x} "
                "(board allows only 5 concurrent connections)"
            ) from exc
        except OSError as exc:
            raise RelayError(f"Socket error on command 0x{payload[0]:02x}: {exc}") from exc
        return buf

    def _switch(self, payload: bytes) -> None:
        if self.rate_limit:
            wait = MIN_SWITCH_INTERVAL - (time.monotonic() - self._last_switch)
            if wait > 0:
                time.sleep(wait)
        ack = self._command(payload, 1)
        self._last_switch = time.monotonic()
        if ack[0] != 0:
            raise RelayError(f"Board rejected command 0x{payload[0]:02x} (ack {ack[0]})")

    def info(self) -> ModuleInfo:
        reply = self._command(bytes([CMD_MODULE_INFO]), 3)
        return ModuleInfo(reply[0], reply[1], reply[2])

    def serial_number(self) -> str:
        return ":".join(f"{b:02x}" for b in self._command(bytes([CMD_SERIAL_NUMBER]), 6))

    def volts(self) -> float:
        return self._command(bytes([CMD_GET_VOLTS]), 1)[0] / 10.0

    def states(self) -> int:
        """Bitmask of energised relays; bit 0 is relay 1."""
        return self._command(bytes([CMD_GET_OUTPUTS]), 1)[0]

    def is_on(self, relay: int) -> bool:
        return bool(self.states() & (1 << (_check_relay(relay) - 1)))

    def on(self, relay: int, pulse_s: float = 0.0) -> None:
        """Energise a relay, permanently or for `pulse_s` seconds."""
        self._switch(bytes([CMD_DIGITAL_ACTIVE, _check_relay(relay), _pulse_units(pulse_s)]))

    def off(self, relay: int, pulse_s: float = 0.0) -> None:
        """De-energise a relay; a non-zero `pulse_s` re-energises it afterwards."""
        self._switch(bytes([CMD_DIGITAL_INACTIVE, _check_relay(relay), _pulse_units(pulse_s)]))

    def toggle(self, relay: int) -> bool:
        """Invert one relay and return its new state."""
        relay = _check_relay(relay)
        if self.states() & (1 << (relay - 1)):
            self.off(relay)
            return False
        self.on(relay)
        return True

    def set_mask(self, mask: int) -> None:
        """Set all eight relays at once from a bitmask."""
        if not 0 <= mask <= 0xFF:
            raise ValueError(f"Mask must be 0-255, got {mask}")
        self._switch(bytes([CMD_SET_OUTPUTS, mask]))

    def all_off(self) -> None:
        self.set_mask(0x00)

    def unlock_time(self) -> int:
        """0 = locked, 1-30 = seconds left, 255 = no TCP password configured."""
        return self._command(bytes([CMD_UNLOCK_TIME]), 1)[0]

    def login(self, password: str) -> None:
        reply = self._command(bytes([CMD_PASSWORD]) + password.encode("ascii"), 1)
        if reply[0] != 1:
            raise RelayError("TCP/IP password rejected")

    def logout(self) -> None:
        self._command(bytes([CMD_LOGOUT]), 1)


def _check_relay(relay: int) -> int:
    if not 1 <= relay <= RELAY_COUNT:
        raise ValueError(f"Relay must be 1-{RELAY_COUNT}, got {relay}")
    return relay


def _pulse_units(pulse_s: float) -> int:
    if pulse_s <= 0:
        return 0
    units = round(pulse_s / PULSE_UNIT_S)
    if not 1 <= units <= PULSE_MAX_UNITS:
        raise ValueError(
            f"Pulse must be {PULSE_UNIT_S}-{PULSE_MAX_UNITS * PULSE_UNIT_S}s, got {pulse_s}s"
        )
    return units


def format_states(mask: int) -> str:
    return " ".join(f"{n}:{'ON ' if mask & (1 << (n - 1)) else 'off'}" for n in range(1, RELAY_COUNT + 1))


def _parse_mask(text: str) -> int:
    """Accept 0x0d, 0b00001101, 13, or a relay list such as 1,3,4."""
    text = text.strip()
    if "," in text:
        mask = 0
        for part in text.split(","):
            mask |= 1 << (_check_relay(int(part)) - 1)
        return mask
    return int(text, 0)


def _connect(args: argparse.Namespace) -> ETH008B:
    board = ETH008B(args.host, args.port, rate_limit=not args.no_rate_limit)
    board.connect()
    password = args.password or os.environ.get("ETH008B_PASSWORD")
    if password:
        board.login(password)
    return board


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--password",
        help="TCP/IP password; also read from ETH008B_PASSWORD",
    )
    parser.add_argument(
        "--no-rate-limit",
        action="store_true",
        help=f"Disable the {RELAY_RATE_LIMIT_HZ} Hz switching guard (use with care)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="Module id, versions, MAC and supply voltage")
    sub.add_parser("status", help="Print the state of all eight relays")
    sub.add_parser("volts", help="Print the relay supply voltage")

    p_on = sub.add_parser("on", help="Energise a relay")
    p_on.add_argument("relay", type=int)
    p_on.add_argument("--pulse", type=float, default=0.0, metavar="SECONDS")

    p_off = sub.add_parser("off", help="De-energise a relay")
    p_off.add_argument("relay", type=int)
    p_off.add_argument("--pulse", type=float, default=0.0, metavar="SECONDS")

    p_toggle = sub.add_parser("toggle", help="Invert a relay")
    p_toggle.add_argument("relay", type=int)

    p_set = sub.add_parser("set", help="Set all relays from a mask or relay list")
    p_set.add_argument("mask", help="0x0d, 0b00001101, 13, or 1,3,4")

    sub.add_parser("all-off", help="De-energise every relay")

    p_watch = sub.add_parser("watch", help="Poll and print state changes")
    p_watch.add_argument("--interval", type=float, default=0.5)

    args = parser.parse_args(argv)

    try:
        board = _connect(args)
    except (RelayError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        match args.command:
            case "info":
                i = board.info()
                print(f"Model:      {i.model} (module id {i.module_id})")
                print(f"Hardware:   v{i.hardware_version}")
                print(f"Firmware:   v{i.firmware_version}")
                print(f"MAC:        {board.serial_number()}")
                print(f"Supply:     {board.volts():.1f} V")
                unlock = board.unlock_time()
                if unlock == UNLOCK_TIME_NO_PASSWORD:
                    print("TCP passwd: not enabled")
                elif unlock == UNLOCK_TIME_LOCKED:
                    print("TCP passwd: enabled, locked")
                else:
                    print(f"TCP passwd: enabled, unlocked for {unlock}s")
            case "status":
                mask = board.states()
                print(f"0x{mask:02x}  {mask:08b}  {format_states(mask)}")
            case "volts":
                print(f"{board.volts():.1f}")
            case "on":
                board.on(args.relay, args.pulse)
            case "off":
                board.off(args.relay, args.pulse)
            case "toggle":
                print("on" if board.toggle(args.relay) else "off")
            case "set":
                board.set_mask(_parse_mask(args.mask))
            case "all-off":
                board.all_off()
            case "watch":
                previous: int | None = None
                while True:
                    mask = board.states()
                    if mask != previous:
                        print(f"{time.strftime('%H:%M:%S')}  {mask:08b}  {format_states(mask)}")
                        previous = mask
                    time.sleep(args.interval)
    except KeyboardInterrupt:
        return 130
    except (RelayError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        board.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
