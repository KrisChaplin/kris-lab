# Agent Guide — Devantech ETH008-B Relay Board

> Instrument-specific entry point for AI coding agents. For the lab
> overview, see [../AGENTS.md](../AGENTS.md).

Eight-channel Ethernet relay board at `192.168.0.200`, TCP port 17494.

## Hard rules

1. **Never switch a relay faster than 3 Hz.** The contacts are wired to
   powered lab equipment. `relayctl.py` sleeps to enforce a 333 ms
   minimum between state changes; do not pass `--no-rate-limit`.
2. **Read `status` first, and restore what you found.** Other equipment
   depends on the current mask. Probe on a relay that is already off.
3. **Do not change board configuration** — network settings, TCP/IP
   password, HTTP authentication, latched outputs, MQTT, or ping
   actions — unless explicitly asked. Config changes need a module reset.
4. **Never commit a password** read from `config.htm` or `mqtt.htm`.
5. Prefer the binary TCP command set. It is the only one that
   acknowledges every command.

## TL;DR — copy these

```bash
cd devantech-eth008b
python relayctl.py status            # 0x0d  00001101  1:ON 2:off ...
python relayctl.py on 3
python relayctl.py off 3
python relayctl.py on 3 --pulse 2.5  # auto-release after 2.5 s
python relayctl.py set 1,3,4         # whole mask in one command
python relayctl.py watch             # print state changes
```

Library use:

```python
from relayctl import ETH008B

with ETH008B() as board:
    original = board.states()
    board.on(8, pulse_s=2.0)
```

## Protocol facts (verified on this board)

- Binary commands go to TCP 17494. All bytes of a command must be sent
  in one write.
- `0x24` returns one byte; **bit 0 is relay 1**. The board reported
  `0x0d` while relays 1, 3 and 4 were energised.
- `0x20 <relay> <units>` energises, `0x21 <relay> <units>` de-energises.
  `units` is 100 ms steps, 1–255, or 0 for permanent. Ack is `0` for
  success, `1` for failure (relay 0 and relay 9 both return `1`).
- A non-zero `units` on `0x21` means *de-energise for that long, then
  re-energise* — it is a pulse in the opposite direction, not a delay.
- `0x23 <mask>` sets all eight relays in one acknowledged command. Use
  it to restore state rather than eight separate calls.
- `0x25` (get inputs) and `0x30` (analogue) return nothing. This model
  has no inputs.
- `0x78` returns supply volts × 10 (`119` → 11.9 V).
- `0x7A` returns `255` here, meaning the TCP/IP password is not enabled.

## Gotchas

- **Closing the socket immediately after `sendall` drops the command.**
  Always read the acknowledgement. A 0 ms close loses the command; a
  50 ms delay was enough, but reading the ack is the only reliable fix.
- **Only five concurrent TCP connections.** The sixth connects but never
  replies, so it surfaces as a read timeout, not a refused connection.
  Reuse one socket; `ETH008B` keeps a persistent connection.
- **ASCII commands return no acknowledgement.** `:DOA,8,20` works but
  you cannot tell success from failure without re-reading `0x24`.
- `io.cgi` prints relay state **LSB first** (`relays 10110001` means
  relays 1, 3, 4 and 8 are on) — the opposite order to the web page's
  8…1 labelling and to the `0x24` bitmask when written as binary.
- The web page rounds the supply voltage; `0x78` is the raw value.

See [docs/INDEX.md](docs/INDEX.md) for the full command sets.
