#!/usr/bin/env python3
"""FNIRSI DPO-F1204 control library.

Wire protocol (ws://<ip>/ws_control):

  * Every text frame the client sends is acknowledged with exactly one frame.
  * Replies are JSON of the form
        {"cmd":"scpi_control","code":0,"data":"...","msgId":N,
         "ts":<epoch_ms>,"type":"response","version":1}
    where `msgId` increments monotonically per session.
  * Some replies are **plain text** (not JSON) - most commonly the literal
    string ``deadline has elapsed`` when the firmware did not process the
    command (unsupported / busy / dropped). Treat those as soft errors.
  * Writes (e.g. ``:RUN``, ``:CHAN2:SCAL 1``) also get an ack frame. Failing
    to drain it causes the next query's reply to be lost. This client always
    drains.

Known SCPI dialect quirks on V1.0.1.26020603:
  * Channel arg is ``C1`` / ``C2`` (NOT ``CHAN1``).
  * Query form of ``:CHAN<n>:DISP`` is unsupported (write works).
  * ``:MEAS:VPP? C2`` etc. are unreliable; only ``:MEAS:FREQ? C<n>``
    returns a number, and even that returns a bogus ~1e-38 when the
    measurement isn't enabled on screen.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass
from typing import Any, Optional
import websocket


@dataclass
class Reply:
    """A reply from the scope. `ok` is False if the firmware returned the
    text 'deadline has elapsed' or any non-JSON frame."""
    ok: bool
    data: str
    code: int
    msg_id: int
    raw: Any


class Scope:
    def __init__(self, host: str = "192.168.0.75",
                 timeout: float = 5.0,
                 debug: bool = False):
        self.host = host
        self.url = f"ws://{host}/ws_control"
        self.timeout = timeout
        self.debug = debug
        self.ws: Optional[websocket.WebSocket] = None
        self.last_msg_id: int = -1

    def open(self) -> "Scope":
        ws = websocket.WebSocket()
        ws.settimeout(self.timeout)
        ws.connect(self.url, origin=f"http://{self.host}")
        self.ws = ws
        # Drain any frames already queued on the socket from a previous
        # client session. The send-with-flush exchange handles the rest.
        self._drain_stale(settle=0.4)
        return self

    def _drain_stale(self, settle: float = 0.2) -> int:
        """Drain any unread replies left over from previous sends/sessions.
        The firmware keeps queued replies across reconnects, so a brand-new
        socket can return data from a previous client's commands. Even
        within a single session, replies arrive after a small delay so we
        also briefly settle before sending a new command.

        Returns the number of frames drained."""
        assert self.ws is not None
        n = 0
        old_to = self.ws.gettimeout()
        try:
            self.ws.settimeout(settle)
            while True:
                try:
                    self.ws.recv()
                    n += 1
                except (websocket.WebSocketTimeoutException, OSError):
                    break
        finally:
            self.ws.settimeout(old_to)
        if self.debug and n:
            print(f"(drained {n} stale frames)")
        return n

    def _send(self, obj: dict) -> None:
        assert self.ws is not None, "not connected"
        if self.debug:
            print(f"--> {obj}")
        self.ws.send(json.dumps(obj))

    def close(self) -> None:
        if self.ws is not None:
            try:
                self.ws.close()
            finally:
                self.ws = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *_):
        self.close()

    def _recv_one(self, expect_cmd: Optional[str] = None,
                  max_discard: int = 6) -> Reply:
        """Read one matching reply.

        If ``expect_cmd`` is given (e.g. ``scpi_control`` or
        ``get_dev_info``), this discards up to ``max_discard`` mismatched
        frames before returning. The firmware sometimes delivers stale
        replies left over from earlier sends; ``expect_cmd`` lets us
        re-align.

        Empty / non-JSON frames are returned immediately regardless of
        ``expect_cmd`` since they have no ``cmd`` field to match against."""
        assert self.ws is not None
        for _ in range(max_discard + 1):
            try:
                raw = self.ws.recv()
            except websocket.WebSocketTimeoutException:
                return Reply(False, "<timeout>", -1, -1, None)
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8", errors="replace")
            if self.debug:
                print(f"<-- {raw!r}")
            raw_stripped = raw.strip() if isinstance(raw, str) else ""
            if not raw_stripped:
                return Reply(True, "", 0, -1, raw)
            try:
                j = json.loads(raw_stripped)
            except (json.JSONDecodeError, TypeError):
                return Reply(False, raw_stripped, -1, -1, raw)
            code = int(j.get("code", -1))
            data = str(j.get("data", ""))
            msg_id = int(j.get("msgId", -1))
            reply_cmd = j.get("cmd", "")
            if msg_id > self.last_msg_id:
                self.last_msg_id = msg_id
            if expect_cmd is not None and reply_cmd != expect_cmd:
                if self.debug:
                    print(f"(discarding stale {reply_cmd!r} reply)")
                continue
            return Reply(code == 0, data, code, msg_id, raw)
        return Reply(False, "<no-matching-reply>", -1, -1, None)

    def _exchange(self, obj: dict, expect_cmd: Optional[str] = None) -> Reply:
        """Send a command then a trailing dummy of a *different opcode*,
        read both reply frames and return the one matching ``expect_cmd``.

        The firmware buffers one pending reply and only releases it when
        the next command arrives, so a trailing dummy is needed to flush.
        It also reorders replies relative to send order, so we pair the
        real command with a dummy whose reply has a different ``cmd``
        field — that lets us identify our real reply unambiguously
        regardless of processing order.

        We use ``get_dev_info`` as the dummy (reply cmd ``get_dev_info``)
        which differs from ``scpi_control`` / ``mouse_event`` /
        ``web_indicator``. To avoid mutual recursion, when the user IS
        calling ``get_dev_info`` we fall back to ``web_indicator`` as the
        dummy.
        """
        if obj.get("cmd") == "get_dev_info":
            dummy = {"cmd": "web_indicator", "data": "off"}
            dummy_cmd = "web_indicator"
        else:
            dummy = {"cmd": "get_dev_info", "data": ""}
            dummy_cmd = "get_dev_info"
        # Default expected cmd inferred from the request if the caller
        # didn't pass one.
        if expect_cmd is None:
            expect_cmd = {
                "scpi": "scpi_control",
                "mouse_event": "mouse_event",
                "get_dev_info": "get_dev_info",
                "web_indicator": "web_indicator",
            }.get(obj.get("cmd", ""), None)
        self._send(obj)
        self._send(dummy)
        a = self._recv_one()
        b = self._recv_one()
        if expect_cmd is not None:
            for r in (a, b):
                if r.raw and isinstance(r.raw, str) and _cmd_of(r.raw) == expect_cmd:
                    return r
            # Neither reply has the expected cmd. Likely one is an empty
            # ack (write) and the other is the dummy. Return the empty.
            for r in (a, b):
                if not (isinstance(r.raw, str) and r.raw.strip()):
                    return r
        # Fall back: return the one that isn't the dummy.
        for r in (a, b):
            if r.raw and isinstance(r.raw, str) and _cmd_of(r.raw) != dummy_cmd:
                return r
        return a

    def send_scpi(self, cmd: str) -> Reply:
        """Send a SCPI command and read back its reply (with flush)."""
        return self._exchange({"cmd": "scpi", "data": cmd},
                              expect_cmd="scpi_control")

    def touch(self, x: int, y: int, hold_ms: int = 80) -> bool:
        """Emulate a touchscreen tap at (x,y) via a down+up sequence. A
        single `clicked` event is acked but does NOT trigger UI actions like
        channel toggles; the down+up pair does."""
        r1 = self._exchange(
            {"cmd": "mouse_event",
             "data": json.dumps({"event": "down", "x": x, "y": y})},
            expect_cmd="mouse_event")
        time.sleep(hold_ms / 1000.0)
        r2 = self._exchange(
            {"cmd": "mouse_event",
             "data": json.dumps({"event": "up", "x": x, "y": y})},
            expect_cmd="mouse_event")
        return r1.ok and r2.ok

    # Approximate centres of the right-side channel buttons (800x480 frame).
    # These defaults are overridden if a ``clickmap.json`` file is found
    # next to this module (see ``_load_clickmap``).
    CHANNEL_BUTTON_XY = {
        1: (760, 145),
        2: (760, 220),
        3: (760, 295),
        4: (760, 370),
    }

    @classmethod
    def _load_clickmap(cls) -> dict:
        """Load clickmap.json from this module's directory, if present.
        Returns the parsed dict (or {} on failure)."""
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "clickmap.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def click(self, label: str, hold_ms: int = 80) -> bool:
        """Tap a labelled UI element from clickmap.json. Raises KeyError if
        the label is not in the map."""
        m = self._load_clickmap()
        if label not in m:
            raise KeyError(f"clickmap.json has no entry for {label!r}")
        x, y = m[label]
        return self.touch(int(x), int(y), hold_ms=hold_ms)

    def channel_toggle(self, ch: int) -> bool:
        """Toggle channel display. Each call flips state. SCPI
        ``:CHAN<n>:DISP`` is silently ignored on this firmware so we use
        the touchscreen passthrough. Uses clickmap.json if available."""
        m = self._load_clickmap()
        key = f"ch{ch}_toggle"
        if key in m:
            x, y = m[key]
        else:
            x, y = self.CHANNEL_BUTTON_XY[ch]
        return self.touch(int(x), int(y))

    def channel_is_on(self, ch: int) -> bool:
        """Returns True iff channel ``ch`` is currently displayed. Detected
        by sampling the channel badge colour on the right edge of the
        screen (uses /ws_image; opens a fresh image socket each call)."""
        from screen import capture  # local import to avoid hard PIL dep
        from channel_state import detect
        import tempfile, os
        raw = capture(self.host)
        # Cheap: write to temp PNG, then run detect; saves duplicating logic.
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            from screen import save_png
            save_png(raw, tmp)
            return detect(tmp)[ch]
        finally:
            os.unlink(tmp)

    def channel_set(self, ch: int, on: bool, retries: int = 2) -> bool:
        """Idempotent channel display set. Toggles iff current state differs
        from desired; verifies via screenshot and retries on failure."""
        for _ in range(retries + 1):
            if self.channel_is_on(ch) == on:
                return True
            self.channel_toggle(ch)
            time.sleep(0.35)
        return self.channel_is_on(ch) == on

    def query(self, cmd: str, retries: int = 2) -> str:
        for attempt in range(retries + 1):
            r = self.send_scpi(cmd)
            if r.ok:
                return r.data.strip()
            if attempt < retries:
                time.sleep(0.2)
        return ""

    def write(self, cmd: str) -> bool:
        return self.send_scpi(cmd).ok

    # high-level helpers ---------------------------------------------------
    def idn(self) -> str:
        return self.query("*IDN?")

    def run(self)    -> bool: return self.write(":RUN")
    def stop(self)   -> bool: return self.write(":STOP")
    def single(self) -> bool: return self.write(":SING")
    def auto(self)   -> bool: return self.write(":AUT")

    def trig_status(self) -> str:
        return self.query(":TRIG:STAT?")

    def sample_rate(self) -> float:
        return _to_float(self.query(":ACQ:SRAT?"))

    def channel_on(self, ch: int, on: bool = True) -> bool:
        """Toggle channel display. There is no reliable SCPI query for the
        current state, so the caller must track on/off itself (or visually
        check via ``screen.py``). The ``on`` argument is unused (kept for
        API symmetry) — each call flips the state."""
        del on  # toggle-only firmware behaviour
        return self.channel_toggle(ch)

    def channel_scale(self, ch: int, volts_per_div: float | None = None) -> float:
        if volts_per_div is None:
            return _to_float(self.query(f":CHAN{ch}:SCAL?"))
        self.write(f":CHAN{ch}:SCAL {_fmt(volts_per_div)}")
        return _to_float(self.query(f":CHAN{ch}:SCAL?"))

    def channel_offset(self, ch: int, volts: float | None = None) -> float:
        if volts is None:
            return _to_float(self.query(f":CHAN{ch}:OFFS?"))
        self.write(f":CHAN{ch}:OFFS {_fmt(volts)}")
        return _to_float(self.query(f":CHAN{ch}:OFFS?"))

    def channel_coupling(self, ch: int, coupling: str | None = None) -> str:
        if coupling is None:
            return self.query(f":CHAN{ch}:COUP?")
        self.write(f":CHAN{ch}:COUP {coupling.upper()}")
        return self.query(f":CHAN{ch}:COUP?")

    def channel_probe(self, ch: int, ratio: float | None = None) -> float:
        if ratio is None:
            return _to_float(self.query(f":CHAN{ch}:PROB?"))
        self.write(f":CHAN{ch}:PROB {_fmt(ratio)}")
        return _to_float(self.query(f":CHAN{ch}:PROB?"))

    def timebase(self, seconds_per_div: float | None = None) -> float:
        if seconds_per_div is None:
            return _to_float(self.query(":TIM:SCAL?"))
        self.write(f":TIM:SCAL {_fmt(seconds_per_div)}")
        return _to_float(self.query(":TIM:SCAL?"))

    def trigger_source(self, ch: int | None = None) -> str:
        if ch is None:
            return self.query(":TRIG:EDGE:SOUR?")
        self.write(f":TRIG:EDGE:SOUR C{ch}")
        return self.query(":TRIG:EDGE:SOUR?")

    def trigger_level(self, volts: float | None = None) -> float:
        if volts is None:
            return _to_float(self.query(":TRIG:EDGE:LEV?"))
        self.write(f":TRIG:EDGE:LEV {_fmt(volts)}")
        return _to_float(self.query(":TRIG:EDGE:LEV?"))

    def trigger_slope(self, slope: str | None = None) -> str:
        if slope is None:
            return self.query(":TRIG:EDGE:SLOP?")
        m = {"RISE": "RISing", "FALL": "FALLing", "BOTH": "ALTernation"}
        s = m.get(slope.upper(), slope)
        self.write(f":TRIG:EDGE:SLOP {s}")
        return self.query(":TRIG:EDGE:SLOP?")

    def trigger_coupling(self, mode: str | None = None) -> str:
        """Edge-trigger input coupling: 'AC' or 'DC'."""
        if mode is None:
            return self.query(":TRIG:EDGE:COUP?")
        self.write(f":TRIG:EDGE:COUP {mode.upper()}")
        return self.query(":TRIG:EDGE:COUP?")

    def trigger_noise_reject(self, on: bool | None = None) -> str:
        """Edge-trigger noise reject (write-only on this FW; query always
        times out so we return the requested state for chaining)."""
        if on is None:
            # No working query; report 'unknown'.
            return "?"
        self.write(f":TRIG:EDGE:NREJ {'ON' if on else 'OFF'}")
        return "ON" if on else "OFF"

    def trigger_holdoff(self) -> str:
        """Return the trigger holdoff setting (e.g. 'OFF' or seconds as str).
        Write side appears non-functional on this FW; setting via the on-
        screen Trigger dialog is the reliable path."""
        return self.query(":TRIG:EDGE:HOLDOFF?")

    # --- Cursors --------------------------------------------------------
    # All cursor SCPI commands are routed through the firmware's working
    # path. The :CURS:MODE? query is broken (always returns 'X') but the
    # setter does drive the on-screen mode change, so callers should treat
    # mode as write-only.
    def cursor_source(self, ch: int | None = None) -> int:
        """Cursor source channel (1..4)."""
        if ch is None:
            return int(self.query(":CURS:SOUR?"))
        self.write(f":CURS:SOUR {ch}")
        return int(self.query(":CURS:SOUR?"))

    def cursor_mode(self, mode: str | None = None) -> str:
        """Cursor type: 'OFF' | 'X' | 'Y' | 'XY'. Query is broken on this FW
        (always returns 'X' regardless of actual state)."""
        if mode is None:
            return self.query(":CURS:MODE?")
        self.write(f":CURS:MODE {mode.upper()}")
        return mode.upper()

    def cursor_x1(self, t: float | None = None) -> float:
        """Cursor X1 (time, seconds). With no argument, return current value."""
        if t is None:
            return _to_float(self.query(":CURS:X1?"))
        self.write(f":CURS:X1 {_fmt(t)}")
        return _to_float(self.query(":CURS:X1?"))

    def cursor_x2(self, t: float | None = None) -> float:
        if t is None:
            return _to_float(self.query(":CURS:X2?"))
        self.write(f":CURS:X2 {_fmt(t)}")
        return _to_float(self.query(":CURS:X2?"))

    def cursor_y1(self, v: float | None = None) -> float:
        """Cursor Y1 (voltage). With no argument, return current value."""
        if v is None:
            return _to_float(self.query(":CURS:Y1?"))
        self.write(f":CURS:Y1 {_fmt(v)}")
        return _to_float(self.query(":CURS:Y1?"))

    def cursor_y2(self, v: float | None = None) -> float:
        if v is None:
            return _to_float(self.query(":CURS:Y2?"))
        self.write(f":CURS:Y2 {_fmt(v)}")
        return _to_float(self.query(":CURS:Y2?"))

    def cursor_xdelta(self) -> float:
        """Δt = X2 - X1, seconds."""
        return _to_float(self.query(":CURS:XDEL?"))

    def cursor_ydelta(self) -> float:
        """ΔV = Y2 - Y1, volts (sign depends on Y1/Y2 ordering)."""
        return _to_float(self.query(":CURS:YDEL?"))

    def cursor_state(self) -> dict:
        """Return all cursor positions and deltas as a dict."""
        return {
            "source": self.cursor_source(),
            "x1": self.cursor_x1(),
            "x2": self.cursor_x2(),
            "xdelta": self.cursor_xdelta(),
            "y1": self.cursor_y1(),
            "y2": self.cursor_y2(),
            "ydelta": self.cursor_ydelta(),
        }

    def cursor_show(self, on: bool, close_dialog: bool = True) -> bool:
        """Drive the on-screen Cursor toggle to make cursor markers visible
        (or hide them). Idempotent — samples the toggle pill colour to read
        the current state and only taps if a change is needed.

        Parameters
        ----------
        on : True to enable cursor display, False to disable.
        close_dialog : if True (default), close the Cursor Measurement dialog
            after toggling so the cursor readouts (X1/X2/Δ) remain visible on
            top of the waveform view. The dialog's X glyph at (665, 68) is
            functional (unlike Measure's).

        Returns the new on-screen state read back from the pixel sample.
        """
        import os
        import tempfile
        from PIL import Image
        from screen import capture, save_png

        def _snapshot() -> Image.Image:
            raw = capture(self.host)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp = f.name
            try:
                save_png(raw, tmp)
                return Image.open(tmp).copy()
            finally:
                os.unlink(tmp)

        def _toggle_is_on(im: Image.Image) -> bool:
            # Sample inside the toggle pill at (150, 113). ON = saturated blue
            # (~16,134,173); OFF = mid-grey (~140,142,140).
            r, g, b = im.getpixel((150, 113))[:3]
            return b > r + 60 and b > 120

        def _any_dialog_open(im: Image.Image) -> bool:
            r, g, b = im.getpixel((300, 68))[:3]
            return 50 < r < 90 and 50 < g < 90 and 50 < b < 90

        def _cursor_dialog_open(im: Image.Image) -> bool:
            # Cursor Measurement title extends past x=100. Discriminates from
            # Measure (title ends near x=80) and Math (ends near x=40).
            if not _any_dialog_open(im):
                return False
            return sum(
                1 for x in range(90, 130, 2)
                if sum(im.getpixel((x, 68))[:3]) > 300
            ) >= 4

        im = _snapshot()
        if not _cursor_dialog_open(im):
            self.click("cursor_button"); time.sleep(0.5)
            im = _snapshot()
        current = _toggle_is_on(im)
        if current != on:
            self.touch(160, 113); time.sleep(0.5)
            im = _snapshot()
        actual = _toggle_is_on(im)
        if close_dialog:
            # Cursor dialog's X close at (665, 68) — works.
            self.touch(665, 68); time.sleep(0.4)
        return actual

    # --- Acquisition ----------------------------------------------------
    def acq_type(self, mode: str | None = None) -> str:
        """Acquisition mode. Only 'NORM' and 'PEAK' actually take on this
        firmware -- 'HRES' and 'AVER' are silently rejected."""
        if mode is None:
            return self.query(":ACQ:TYPE?")
        self.write(f":ACQ:TYPE {mode}")
        return self.query(":ACQ:TYPE?")

    def memory_depth(self) -> str:
        """Memory depth as the device reports it, e.g. '7M'."""
        return self.query(":ACQ:MDEP?")

    # --- Non-SCPI opcodes -----------------------------------------------
    def dev_info(self) -> dict:
        """Return the device's get_dev_info payload as a dict."""
        r = self._exchange({"cmd": "get_dev_info", "data": ""},
                           expect_cmd="get_dev_info")
        if not r.ok or not r.data:
            return {}
        try:
            return json.loads(r.data)
        except (json.JSONDecodeError, TypeError):
            return {}

    def indicator(self, on: bool) -> bool:
        """Toggle the 'web client connected' indicator. The firmware acks
        with '操作成功' (success) for either 'on' or 'off'."""
        r = self._exchange({"cmd": "web_indicator",
                            "data": "on" if on else "off"},
                           expect_cmd="web_indicator")
        return "成功" in (r.data or "") or r.ok

    # --- Local state save/restore (workaround for broken *SAV/*RCL) -----
    STATE_QUERIES = {
        "ch1.scale":   ":CHAN1:SCAL?",
        "ch1.offset":  ":CHAN1:OFFS?",
        "ch1.coup":    ":CHAN1:COUP?",
        "ch1.probe":   ":CHAN1:PROB?",
        "ch2.scale":   ":CHAN2:SCAL?",
        "ch2.offset":  ":CHAN2:OFFS?",
        "ch2.coup":    ":CHAN2:COUP?",
        "ch2.probe":   ":CHAN2:PROB?",
        "ch3.scale":   ":CHAN3:SCAL?",
        "ch3.offset":  ":CHAN3:OFFS?",
        "ch3.coup":    ":CHAN3:COUP?",
        "ch3.probe":   ":CHAN3:PROB?",
        "ch4.scale":   ":CHAN4:SCAL?",
        "ch4.offset":  ":CHAN4:OFFS?",
        "ch4.coup":    ":CHAN4:COUP?",
        "ch4.probe":   ":CHAN4:PROB?",
        "tim.scale":   ":TIM:SCAL?",
        "trig.source": ":TRIG:EDGE:SOUR?",
        "trig.level":  ":TRIG:EDGE:LEV?",
        "trig.slope":  ":TRIG:EDGE:SLOP?",
        "acq.type":    ":ACQ:TYPE?",
    }

    # Order matters on restore: e.g. probe ratio affects valid scale values.
    STATE_WRITES = [
        ("ch1.probe",   ":CHAN1:PROB {v}"),
        ("ch2.probe",   ":CHAN2:PROB {v}"),
        ("ch3.probe",   ":CHAN3:PROB {v}"),
        ("ch4.probe",   ":CHAN4:PROB {v}"),
        ("ch1.coup",    ":CHAN1:COUP {v}"),
        ("ch2.coup",    ":CHAN2:COUP {v}"),
        ("ch3.coup",    ":CHAN3:COUP {v}"),
        ("ch4.coup",    ":CHAN4:COUP {v}"),
        ("ch1.scale",   ":CHAN1:SCAL {v}"),
        ("ch2.scale",   ":CHAN2:SCAL {v}"),
        ("ch3.scale",   ":CHAN3:SCAL {v}"),
        ("ch4.scale",   ":CHAN4:SCAL {v}"),
        ("ch1.offset",  ":CHAN1:OFFS {v}"),
        ("ch2.offset",  ":CHAN2:OFFS {v}"),
        ("ch3.offset",  ":CHAN3:OFFS {v}"),
        ("ch4.offset",  ":CHAN4:OFFS {v}"),
        ("tim.scale",   ":TIM:SCAL {v}"),
        ("trig.source", ":TRIG:EDGE:SOUR {v}"),
        ("trig.level",  ":TRIG:EDGE:LEV {v}"),
        ("trig.slope",  ":TRIG:EDGE:SLOP {v}"),
        ("acq.type",    ":ACQ:TYPE {v}"),
    ]

    def state_dump(self, include_channels_on: bool = True) -> dict:
        """Return a dict of the current scope state via SCPI queries plus
        (optionally) the on/off state of each channel via screenshot."""
        out: dict = {"_idn": self.idn()}
        for key, cmd in self.STATE_QUERIES.items():
            out[key] = self.query(cmd)
        if include_channels_on:
            # One screenshot, four detections.
            from screen import capture, save_png
            from channel_state import detect
            import tempfile, os
            raw = capture(self.host)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp = f.name
            try:
                save_png(raw, tmp)
                st = detect(tmp)
            finally:
                os.unlink(tmp)
            out["channels_on"] = {f"ch{n}": bool(st[n]) for n in (1, 2, 3, 4)}
        return out

    def state_save(self, path: str) -> dict:
        """Dump state to a JSON file. Returns the dict that was written."""
        import os
        s = self.state_dump()
        with open(path, "w") as f:
            json.dump(s, f, indent=2, sort_keys=True)
            f.write("\n")
        return s

    def state_load(self, path: str) -> int:
        """Restore state from a JSON file produced by state_save(). Returns
        the number of successfully applied settings."""
        with open(path) as f:
            s = json.load(f)
        applied = 0
        for key, tmpl in self.STATE_WRITES:
            v = s.get(key)
            if not v:
                continue
            if self.write(tmpl.format(v=v)):
                applied += 1
        # Channel on/off last so user sees the final scene immediately.
        chs = s.get("channels_on") or {}
        for n in (1, 2, 3, 4):
            want = chs.get(f"ch{n}")
            if want is None:
                continue
            self.channel_set(n, bool(want))
            applied += 1
        return applied

    # ----------------------------------------------------------------- #
    # Touchscreen-driven Trigger dialog                                 #
    # ----------------------------------------------------------------- #
    def trigger_ui(self,
                   ttype: str | None = None,
                   source: int | None = None,
                   slope: str | None = None,
                   mode: str | None = None,
                   close: bool = True) -> None:
        """Open the Trigger dialog and apply the requested changes by tapping.

        Use this for trigger Type changes that lack working SCPI on this
        firmware. For simple Edge-trigger source/level/slope changes, the
        SCPI ``trigger_source/level/slope`` setters are faster.

        Parameters
        ----------
        ttype  : one of the keys in ``trigger.TRIG_TYPES`` (edge, pulse, slope, …)
        source : 1..4
        slope  : 'rising'|'falling'|'either' (only valid for edge-like types)
        mode   : 'auto'|'normal'|'single'
        close  : tap the dialog close button when finished.
        """
        from trigger import (
            TRIG_OPEN_BUTTON, TRIG_DIALOG_CLOSE,
            TRIG_TYPE_DROPDOWN, TRIG_SOURCE_DROPDOWN,
            TRIG_TYPES, TRIG_SOURCE_CHANNELS, TRIG_SLOPE, TRIG_MODE,
        )

        if ttype is not None and ttype.lower() not in TRIG_TYPES:
            raise ValueError(f"unknown trigger type {ttype!r}; "
                             f"choose one of {sorted(TRIG_TYPES)}")
        if source is not None and source not in TRIG_SOURCE_CHANNELS:
            raise ValueError(f"source must be 1..4, got {source}")
        if slope is not None and slope.lower() not in TRIG_SLOPE:
            raise ValueError(f"slope must be one of {list(TRIG_SLOPE)}")
        if mode is not None and mode.lower() not in TRIG_MODE:
            raise ValueError(f"mode must be one of {list(TRIG_MODE)}")

        self.touch(*TRIG_OPEN_BUTTON); time.sleep(0.45)
        if ttype is not None:
            self.touch(*TRIG_TYPE_DROPDOWN); time.sleep(0.3)
            self.touch(*TRIG_TYPES[ttype.lower()]); time.sleep(0.4)
        if source is not None:
            self.touch(*TRIG_SOURCE_DROPDOWN); time.sleep(0.3)
            self.touch(*TRIG_SOURCE_CHANNELS[source]); time.sleep(0.3)
        if slope is not None:
            self.touch(*TRIG_SLOPE[slope.lower()]); time.sleep(0.2)
        if mode is not None:
            self.touch(*TRIG_MODE[mode.lower()]); time.sleep(0.2)
        if close:
            self.touch(*TRIG_DIALOG_CLOSE); time.sleep(0.4)

    # ----------------------------------------------------------------- #
    # Touchscreen-driven Math / FFT dialog                              #
    # ----------------------------------------------------------------- #
    def math_ui(self,
                operator: str | None = None,
                source: int | None = None,
                source_b: int | None = None,
                on: bool | None = None,
                fft_unit: str | None = None,
                fft_display: str | None = None,
                auto_setup: bool = False,
                close: bool = True) -> None:
        """Open the Math dialog and apply requested changes by tapping.

        Parameters
        ----------
        operator   : key of ``math.MATH_OPERATORS`` ('+', '-', '*', '/',
                     'FFT', 'd/dt', 'intdt', 'sqrt')
        source     : 1..4 — Source A
        source_b   : 1..4 — Source B (ignored for FFT/d-dt/intdt/sqrt)
        on         : True to turn the Operation toggle on, False to turn off.
                     None leaves it alone. The current state isn't queried,
                     so call once with the value you want.
        fft_unit   : 'dBVrms' | 'Vrms' | 'dBm' (FFT only)
        fft_display: 'full' | 'exclusive' (FFT only)
        auto_setup : if True and operator=='FFT', tap Auto Setup button.
        close      : tap the dialog close button when finished.
        """
        from mathui import (  # noqa: WPS433 (intentional local import)
            GEAR_BUTTON, FUNCTION_MENU_MATH, MATH_DIALOG_CLOSE,
            MATH_OPERATION_TOGGLE, MATH_OPERATOR_DROPDOWN,
            MATH_SOURCE_A_DROPDOWN, MATH_SOURCE_B_DROPDOWN,
            MATH_OPERATORS, MATH_SOURCE_CHANNELS, MATH_SOURCE_B_CHANNELS,
            MATH_AUTO_SETUP,
            MATH_FFT_UNIT_DBVRMS, MATH_FFT_UNIT_VRMS, MATH_FFT_UNIT_DBM,
            MATH_FFT_DISPLAY_FULL, MATH_FFT_DISPLAY_EXCLUSIVE,
        )

        if operator is not None and operator not in MATH_OPERATORS:
            raise ValueError(f"unknown operator {operator!r}; "
                             f"choose one of {sorted(MATH_OPERATORS)}")
        if source is not None and source not in MATH_SOURCE_CHANNELS:
            raise ValueError(f"source must be 1..4, got {source}")
        if source_b is not None and source_b not in MATH_SOURCE_B_CHANNELS:
            raise ValueError(f"source_b must be 1..4, got {source_b}")
        if fft_unit is not None and fft_unit.lower() not in (
                "dbvrms", "vrms", "dbm"):
            raise ValueError(f"fft_unit must be dBVrms|Vrms|dBm")
        if fft_display is not None and fft_display.lower() not in (
                "full", "exclusive"):
            raise ValueError("fft_display must be 'full' or 'exclusive'")

        # Open Function Menu, then Math.
        self.touch(*GEAR_BUTTON); time.sleep(0.5)
        self.touch(*FUNCTION_MENU_MATH); time.sleep(0.5)

        # Operator first (changes the dialog layout for FFT).
        if operator is not None:
            self.touch(*MATH_OPERATOR_DROPDOWN); time.sleep(0.35)
            self.touch(*MATH_OPERATORS[operator]); time.sleep(0.45)

        if source is not None:
            self.touch(*MATH_SOURCE_A_DROPDOWN); time.sleep(0.35)
            self.touch(*MATH_SOURCE_CHANNELS[source]); time.sleep(0.35)

        if source_b is not None:
            self.touch(*MATH_SOURCE_B_DROPDOWN); time.sleep(0.35)
            self.touch(*MATH_SOURCE_B_CHANNELS[source_b]); time.sleep(0.35)

        if fft_display is not None:
            self.touch(*(MATH_FFT_DISPLAY_FULL if fft_display.lower() == "full"
                         else MATH_FFT_DISPLAY_EXCLUSIVE)); time.sleep(0.25)

        if fft_unit is not None:
            xy = {"dbvrms": MATH_FFT_UNIT_DBVRMS,
                  "vrms":   MATH_FFT_UNIT_VRMS,
                  "dbm":    MATH_FFT_UNIT_DBM}[fft_unit.lower()]
            self.touch(*xy); time.sleep(0.25)

        if auto_setup:
            self.touch(*MATH_AUTO_SETUP); time.sleep(0.5)

        if on is not None:
            # Toggle does not query state. We assume caller knows the desired
            # state; double-call if needed.
            self.touch(*MATH_OPERATION_TOGGLE); time.sleep(0.4)

        if close:
            self.touch(*MATH_DIALOG_CLOSE); time.sleep(0.5)
            # Function Menu sometimes lingers behind the Math dialog;
            # dismiss it too if visible (tapping its X is harmless if not).
            from mathui import FUNCTION_MENU_CLOSE
            self.touch(*FUNCTION_MENU_CLOSE); time.sleep(0.3)

    # ----------------------------------------------------------------- #
    # OCR-based measurement readback                                    #
    # ----------------------------------------------------------------- #
    def fft_peak(self, debug_dir: str | None = None) -> float | None:
        """OCR the top-right FFT peak frequency readout (e.g. ``999.992 Hz``)
        shown when the FFT trace is active. Returns the peak frequency in
        Hz, or None if no numeric value parsed.

        The readout occupies roughly x=700..800, y=68..125 on the main
        waveform view (not inside the Math dialog).
        """
        import os
        import re
        import tempfile
        from PIL import Image
        import pytesseract
        from screen import capture, save_png
        from measure import _preprocess_for_ocr, SI_SUFFIXES

        raw = capture(self.host)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            save_png(raw, tmp)
            if debug_dir:
                os.makedirs(debug_dir, exist_ok=True)
                save_png(raw, os.path.join(debug_dir, "fft_peak_full.png"))
            crop = Image.open(tmp).crop((700, 68, 800, 125))
            prepped = _preprocess_for_ocr(crop)
            if debug_dir:
                prepped.save(os.path.join(debug_dir, "fft_peak_ocr.png"))
            text = pytesseract.image_to_string(prepped, config="--psm 6")
        finally:
            os.unlink(tmp)

        m = re.search(
            r"(?P<num>\d+(?:\.\d+)?)\s*[^A-Za-z0-9]*\s*(?P<prefix>[pnuμmkKMG]?)Hz",
            text,
        )
        if not m:
            return None
        return float(m.group("num")) * SI_SUFFIXES.get(m.group("prefix"), 1.0)

    def measure(self,
                ch: int,
                kinds=("Vpp",),
                tab: str = "vertical",
                ch_b: int | None = None,
                clear_first: bool = True,
                debug_dir: str | None = None) -> dict:
        """Enable the requested measurements on `ch`, close the dialog, take
        a screenshot, OCR the readout strip, and return a dict like
        ``{'Vpp': {'value': 0.44, 'unit': 'V', 'raw': 'Vpp:440.00mV'}, ...}``.

        Parameters
        ----------
        ch        : 1..4 (source channel A)
        kinds     : iterable of measurement names. Must be keys of the tab's
                    tile dict (see ``measure.MEAS_*_TILES``).
        tab       : 'vertical' (default), 'horizontal', or 'others'
        ch_b      : 1..4 — second source for the ``others`` tab (required if
                    ``tab='others'``)
        clear_first : if True, tap the Clear button first so the readout strip
                      only contains the newly-enabled items.
        debug_dir : if given, save intermediate screenshots there.
        """
        import os
        import tempfile
        from screen import capture, save_png
        from measure import (
            MEAS_SOURCE_A_DROPDOWN, MEAS_SOURCE_B_DROPDOWN,
            MEAS_SOURCE_CHANNELS, MEAS_SOURCE_B_CHANNELS,
            MEAS_VERTICAL_TILES, MEAS_HORIZONTAL_TILES, MEAS_OTHERS_TILES,
            MEAS_TAB_VERTICAL, MEAS_TAB_HORIZONTAL, MEAS_TAB_OTHERS,
            MEAS_DIALOG_CLOSE, MEAS_CLEAR_BUTTON,
            ocr_readouts,
        )

        if ch not in MEAS_SOURCE_CHANNELS:
            raise ValueError(f"channel must be 1..4, got {ch}")
        if tab == "vertical":
            tiles, tab_xy = MEAS_VERTICAL_TILES, MEAS_TAB_VERTICAL
        elif tab == "horizontal":
            tiles, tab_xy = MEAS_HORIZONTAL_TILES, MEAS_TAB_HORIZONTAL
        elif tab == "others":
            tiles, tab_xy = MEAS_OTHERS_TILES, MEAS_TAB_OTHERS
            if ch_b is None or ch_b not in MEAS_SOURCE_B_CHANNELS:
                raise ValueError("tab='others' requires ch_b in 1..4")
        else:
            raise ValueError(f"unsupported tab {tab!r}")
        unknown = [k for k in kinds if k not in tiles]
        if unknown:
            raise ValueError(f"unknown measurement names for tab {tab!r}: {unknown}")

        def _dump(name: str):
            if not debug_dir:
                return
            os.makedirs(debug_dir, exist_ok=True)
            save_png(capture(self.host), os.path.join(debug_dir, name))

        def _dialog_open() -> bool:
            """Detect specifically the Measure dialog (not Math/FFT or others).
            The dialog's title text 'Measure' draws bright pixels at y=68 in
            roughly x=40..80. The shorter 'Math' title leaves that range dark,
            so this discriminates between Measure-open and Math-open."""
            from PIL import Image
            raw = capture(self.host)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp = f.name
            try:
                save_png(raw, tmp)
                im = Image.open(tmp)
                bright = sum(
                    1 for x in range(40, 81, 2)
                    if sum(im.getpixel((x, 68))[:3]) > 300
                )
                return bright >= 3
            finally:
                os.unlink(tmp)

        def _math_dialog_open() -> bool:
            """Detect the Math dialog (title 'Math' at x≈10..38, y=68).
            We require bright pixels in that short range AND no bright pixels
            beyond x=40 (which would indicate the longer 'Measure' title)."""
            from PIL import Image
            raw = capture(self.host)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp = f.name
            try:
                save_png(raw, tmp)
                im = Image.open(tmp)
                near = sum(1 for x in range(10, 40, 2)
                           if sum(im.getpixel((x, 68))[:3]) > 300)
                far  = sum(1 for x in range(50, 90, 2)
                           if sum(im.getpixel((x, 68))[:3]) > 300)
                return near >= 4 and far < 3
            finally:
                os.unlink(tmp)

        # Math dialog (if left open from a prior session) is drawn ON TOP of
        # the Measure dialog and silently absorbs all subsequent touches.
        # Dismiss it first. Math's X close at (684,68) works (unlike Measure's
        # at (664,68) which is a no-op on this FW).
        if _math_dialog_open():
            self.touch(684, 68); time.sleep(0.5)
        # Ensure Measure dialog is open. The header X glyph is a no-op on this
        # FW so the dialog can be left open from a prior interactive session.
        if not _dialog_open():
            self.click("measure_button"); time.sleep(0.45)
        # Always tap the desired tab — the dialog remembers the previously
        # selected tab across sessions, so skipping the tap when tab=='vertical'
        # can leave us on Horizontal/Others and tap the wrong tiles. Give the
        # tab change a generous settle time; rapid follow-up taps can otherwise
        # land on the prior tab's layout.
        self.touch(*tab_xy); time.sleep(0.6)
        # Optionally clear previous measurements.
        if clear_first:
            self.touch(*MEAS_CLEAR_BUTTON); time.sleep(0.4)
        # Set Source A: open dropdown, tap channel. Dropdown render needs a
        # generous settle; 0.4s sometimes drops the entry tap (seen on CH4 in
        # Source B). Use 0.7s.
        self.touch(*MEAS_SOURCE_A_DROPDOWN); time.sleep(0.7)
        self.touch(*MEAS_SOURCE_CHANNELS[ch]); time.sleep(0.5)
        # Set Source B if applicable.
        if tab == "others":
            self.touch(*MEAS_SOURCE_B_DROPDOWN); time.sleep(0.7)
            self.touch(*MEAS_SOURCE_B_CHANNELS[ch_b]); time.sleep(0.5)
        _dump("after_sources.png")
        # Tap each measurement tile.
        for k in kinds:
            self.touch(*tiles[k]); time.sleep(0.3)
        _dump("after_kinds.png")
        # Close dialog. The header X glyph at (664, 68) does nothing on this FW —
        # tap the top-bar Measure button instead to toggle the dialog off so the
        # main view's readout strip becomes visible for OCR. Verify the dialog
        # actually closed; rapid touch sequences sometimes drop the toggle tap.
        time.sleep(0.4)
        for _ in range(3):
            if not _dialog_open():
                break
            self.click("measure_button"); time.sleep(0.7)

        # Capture and OCR.
        raw = capture(self.host)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            save_png(raw, tmp)
            if debug_dir:
                save_png(raw, os.path.join(debug_dir, "after_close.png"))
            return ocr_readouts(tmp)
        finally:
            os.unlink(tmp)


def _fmt(x: float) -> str:
    if x == 0:
        return "0"
    return f"{x:.6g}"


def _to_float(s: str) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return float("nan")


def _cmd_of(raw: str) -> str:
    try:
        return json.loads(raw).get("cmd", "")
    except (json.JSONDecodeError, TypeError):
        return ""


def _data_of(raw: str) -> str:
    try:
        return str(json.loads(raw).get("data", ""))
    except (json.JSONDecodeError, TypeError):
        return ""


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="DPO-F1204 SCPI helper")
    p.add_argument("--host", default="192.168.0.75")
    p.add_argument("--debug", action="store_true")
    p.add_argument("cmd", nargs="*", help="SCPI command (omit for *IDN?)")
    args = p.parse_args()
    with Scope(args.host, debug=args.debug) as s:
        if not args.cmd:
            print(s.idn())
        else:
            r = s.send_scpi(" ".join(args.cmd))
            print(f"ok={r.ok} code={r.code} msgId={r.msg_id} data={r.data!r}")
