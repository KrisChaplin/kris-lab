#!/usr/bin/env python3
"""CLI for controlling the DPO-F1204.

Examples:
    python3 scopectl.py state
    python3 scopectl.py ch 2 --on --scale 0.5 --offset 0 --coupling DC --probe 1
    python3 scopectl.py tb 1e-3                  # 1 ms/div
    python3 scopectl.py trig --src 2 --lev 0.5 --slope RISE
    python3 scopectl.py run | stop | single | auto
    python3 scopectl.py screenshot out.png
    python3 scopectl.py setup-square            # nice view of the test square wave on CH2
"""
import argparse
import sys
from scope import Scope


def cmd_state(s: Scope, _args):
    print(f"IDN          : {s.idn()}")
    print(f"acq type     : {s.acq_type()}")
    print(f"trig status  : {s.trig_status()}")
    print(f"trig source  : {s.trigger_source()}")
    print(f"trig level   : {s.trigger_level()} V")
    print(f"trig slope   : {s.trigger_slope()}")
    print(f"timebase     : {s.timebase()} s/div")
    print(f"sample rate  : {s.sample_rate()} Sa/s")
    print(f"mem depth    : {s.memory_depth()}")
    on = {ch: s.channel_is_on(ch) for ch in (1, 2, 3, 4)}
    for ch in (1, 2, 3, 4):
        print(f"CH{ch} display  : {'on' if on[ch] else 'off'}")
        print(f"CH{ch} scale    : {s.channel_scale(ch)} V/div")
        print(f"CH{ch} offset   : {s.channel_offset(ch)} V")
        print(f"CH{ch} coupling : {s.channel_coupling(ch)}")
        print(f"CH{ch} probe    : {s.channel_probe(ch)}x")


def cmd_ch(s: Scope, args):
    ch = args.channel
    if args.on:
        ok = s.channel_set(ch, True)
        print(f"CH{ch} on  : {ok}")
    if args.off:
        ok = s.channel_set(ch, False)
        print(f"CH{ch} off : {ok}")
    if args.scale is not None:
        print(f"CH{ch} scale -> {s.channel_scale(ch, args.scale)} V/div")
    if args.offset is not None:
        print(f"CH{ch} offset -> {s.channel_offset(ch, args.offset)} V")
    if args.coupling is not None:
        print(f"CH{ch} coupling -> {s.channel_coupling(ch, args.coupling)}")
    if args.probe is not None:
        print(f"CH{ch} probe -> {s.channel_probe(ch, args.probe)}x")


def cmd_tb(s: Scope, args):
    print(f"timebase -> {s.timebase(args.seconds_per_div)} s/div")


def cmd_trig(s: Scope, args):
    if args.src is not None:
        print(f"trig source -> {s.trigger_source(args.src)}")
    if args.lev is not None:
        print(f"trig level  -> {s.trigger_level(args.lev)} V")
    if args.slope is not None:
        print(f"trig slope  -> {s.trigger_slope(args.slope)}")
    if args.coupling is not None:
        print(f"trig coup   -> {s.trigger_coupling(args.coupling)}")
    if args.nrej is not None:
        print(f"trig nrej   -> {s.trigger_noise_reject(args.nrej == 'on')} (write-only)")
    print(f"trig status : {s.trig_status()}")
    print(f"trig coup   : {s.trigger_coupling()}")
    print(f"trig holdoff: {s.trigger_holdoff()}")


def cmd_cursor(s: Scope, args):
    import json as _json
    if args.src is not None:
        s.cursor_source(args.src)
    if args.mode is not None:
        s.cursor_mode(args.mode)
    if args.x1 is not None:
        s.cursor_x1(args.x1)
    if args.x2 is not None:
        s.cursor_x2(args.x2)
    if args.y1 is not None:
        s.cursor_y1(args.y1)
    if args.y2 is not None:
        s.cursor_y2(args.y2)
    if args.show:
        on = s.cursor_show(True)
        print(f"display: {'ON' if on else 'OFF'}")
    elif args.hide:
        on = s.cursor_show(False)
        print(f"display: {'ON' if on else 'OFF'}")
    state = s.cursor_state()
    if args.json:
        print(_json.dumps(state, indent=2))
        return
    print(f"source : CH{state['source']}")
    print(f"X1     : {state['x1']:.6g} s")
    print(f"X2     : {state['x2']:.6g} s")
    print(f"Δt     : {state['xdelta']:.6g} s"
          + (f"  (= {1.0/state['xdelta']:.6g} Hz)" if state['xdelta'] else ""))
    print(f"Y1     : {state['y1']:.6g} V")
    print(f"Y2     : {state['y2']:.6g} V")
    print(f"ΔV     : {state['ydelta']:.6g} V")


def cmd_run(s, _):     print("run ok=",    s.run())
def cmd_stop(s, _):    print("stop ok=",   s.stop())
def cmd_single(s, _):  print("single ok=", s.single())
def cmd_auto(s, _):    print("auto ok=",   s.auto())
def cmd_reset(s, _):   print("reset ok=",  s.write("*RST"))


def cmd_ping(s: Scope, _):
    """Quick connection test - verify scope is reachable."""
    import time as _t
    start = _t.time()
    idn = s.idn()
    elapsed = (_t.time() - start) * 1000
    if idn:
        print(f"ok ({elapsed:.0f}ms) - {idn}")
    else:
        print(f"FAIL - no response")


def cmd_diagnose(s: Scope, args):
    """Full init: reset → auto → state → optional screenshot.
    
    One command to go from unknown state to captured signal.
    """
    import time as _t
    from screen import capture, save_png
    
    print("=== Diagnose: reset + auto + state ===")
    
    # 1. Reset (clears dialogs, resets to defaults)
    print("1. Reset...", end=" ", flush=True)
    s.write("*RST")
    print("ok")
    _t.sleep(0.3)
    
    # 2. Enable requested channel (default: all off after reset, enable CH1)
    ch = args.channel or 1
    print(f"2. Enable CH{ch}...", end=" ", flush=True)
    s.channel_set(ch, True)
    print("ok")
    
    # 3. Auto-set (finds signal, adjusts scale/timebase/trigger)
    print("3. Auto-set...", end=" ", flush=True)
    s.auto()
    _t.sleep(1.0)  # auto needs time to analyze
    print("ok")
    
    # 4. State dump
    print("\n=== Current State ===")
    cmd_state(s, args)
    
    # 5. Screenshot if requested
    if args.screenshot:
        out = args.screenshot
        print(f"\n=== Screenshot: {out} ===")
        save_png(capture(s.host), out)
        print(f"saved {out}")


def cmd_acq(s: Scope, args):
    if args.type is not None:
        print(f"acq type -> {s.acq_type(args.type)}")
    else:
        print(f"acq type : {s.acq_type()}")
        print(f"srate    : {s.sample_rate()}")
        print(f"mdep     : {s.memory_depth()}")


def cmd_indicator(s: Scope, args):
    print(f"indicator {'on' if args.on else 'off'}: {s.indicator(args.on)}")


def cmd_dev_info(s: Scope, _):
    import json as _json
    print(_json.dumps(s.dev_info(), indent=2))


def cmd_click(s: Scope, args):
    if args.x is not None and args.y is not None:
        print(f"touch ({args.x},{args.y}): {s.touch(args.x, args.y)}")
    elif args.label:
        print(f"click {args.label!r}: {s.click(args.label)}")
    else:
        # list available labels.
        m = Scope._load_clickmap()
        if not m:
            print("clickmap.json is empty")
        else:
            for k in sorted(m):
                x, y = m[k]
                print(f"  {k:30s} -> ({x:3d}, {y:3d})")


def cmd_state_save(s: Scope, args):
    st = s.state_save(args.path)
    print(f"saved {len(st)} keys to {args.path}")


def cmd_state_load(s: Scope, args):
    n = s.state_load(args.path)
    print(f"applied {n} settings from {args.path}")


def cmd_screenshot(s: Scope, args):
    # Reuse screen.py logic to avoid duplication.
    from screen import capture, save_png
    raw = capture(s.host)
    save_png(raw, args.out)
    print(f"saved {args.out}")


def cmd_measure(s: Scope, args):
    import json as _json
    kinds = tuple(args.kinds) if args.kinds else ("Vpp",)
    r = s.measure(args.ch, kinds=kinds, tab=args.tab,
                  ch_b=args.ch_b,
                  clear_first=not args.no_clear,
                  debug_dir=args.debug_dir)
    if args.json:
        print(_json.dumps({k: v["value"] for k, v in r.items()}, indent=2))
        return
    if not r:
        print("(no readouts detected)")
        return
    for k, v in r.items():
        if v["value"] is None:
            print(f"  {k:<12} = ***            (raw={v['raw']})")
        else:
            print(f"  {k:<12} = {v['value']:<14g} {v['unit']}  (raw={v['raw']})")


def cmd_trig_ui(s: Scope, args):
    s.trigger_ui(ttype=args.type, source=args.src,
                 slope=args.slope, mode=args.mode)
    print("trig-ui applied")


def cmd_math(s: Scope, args):
    s.math_ui(operator=args.operator,
              source=args.src,
              source_b=args.src_b,
              on=(True if args.on else False if args.off else None),
              fft_unit=args.fft_unit,
              fft_display=args.fft_display,
              auto_setup=args.auto_setup)
    print("math applied")


def cmd_fft_peak(s: Scope, args):
    peak = s.fft_peak(debug_dir=args.debug_dir)
    if peak is None:
        print("(no FFT peak detected)")
        return
    if peak >= 1e9:
        print(f"FFT peak: {peak / 1e9:.6g} GHz ({peak:.0f} Hz)")
    elif peak >= 1e6:
        print(f"FFT peak: {peak / 1e6:.6g} MHz ({peak:.0f} Hz)")
    elif peak >= 1e3:
        print(f"FFT peak: {peak / 1e3:.6g} kHz ({peak:.3f} Hz)")
    else:
        print(f"FFT peak: {peak:.3f} Hz")


def cmd_setup_square(s: Scope, args):
    """Configure the scope to nicely display the front-panel cal square
    wave on CH2 (1 kHz ish). Ensures CH2 is on (idempotent), configures
    timebase/trigger, runs, and saves a screenshot."""
    from screen import capture, save_png
    import time as _t
    print("Ensuring CH2 is on...")
    s.channel_set(2, True)
    print("Configuring CH2 for square wave display...")
    s.channel_coupling(2, "DC")
    s.channel_probe(2, 1)
    s.channel_scale(2, 1.0)
    s.channel_offset(2, 0)
    s.timebase(5e-4)
    s.trigger_source(2)
    s.trigger_slope("RISE")
    s.trigger_level(0.5)
    s.run()
    _t.sleep(0.6)
    out = args.out or "square.png"
    save_png(capture(s.host), out)
    print(f"saved {out}")
    cmd_state(s, args)


# ============= Protocol Presets =============

def _preset_apply(s: Scope, name: str, channels: list, timebase: float,
                  trig_ch: int, trig_level: float, scale: float,
                  screenshot: str | None):
    """Common logic for protocol presets."""
    from screen import capture, save_png
    import time as _t
    
    print(f"=== Preset: {name} ===")
    
    # Reset first to clear dialogs
    print("1. Reset...", end=" ", flush=True)
    s.write("*RST")
    _t.sleep(0.3)
    print("ok")
    
    # Enable channels
    print(f"2. Enable CH{channels}...", end=" ", flush=True)
    for ch in channels:
        s.channel_set(ch, True)
        s.channel_coupling(ch, "DC")
        s.channel_probe(ch, 1)
        s.channel_scale(ch, scale)
        s.channel_offset(ch, 0)
    print("ok")
    
    # Timebase
    print(f"3. Timebase {timebase*1e6:.1f}µs/div...", end=" ", flush=True)
    s.timebase(timebase)
    print("ok")
    
    # Trigger
    print(f"4. Trigger CH{trig_ch} @ {trig_level}V falling...", end=" ", flush=True)
    s.trigger_source(trig_ch)
    s.trigger_slope("FALL")  # Start conditions are falling edge
    s.trigger_level(trig_level)
    print("ok")
    
    s.run()
    _t.sleep(0.5)
    
    if screenshot:
        print(f"5. Screenshot {screenshot}...", end=" ", flush=True)
        save_png(capture(s.host), screenshot)
        print("ok")
    
    print(f"\nPreset '{name}' applied. Adjust scale/timebase as needed.")


def cmd_preset_i2c(s: Scope, args):
    """I2C preset: 2 channels (SDA, SCL), trigger on SDA falling (start)."""
    # I2C speeds: 100kHz standard, 400kHz fast, 1MHz fast-mode+
    # Default to 400kHz settings
    speed = args.speed or "400k"
    tb_map = {"100k": 20e-6, "400k": 5e-6, "1m": 2e-6}
    timebase = tb_map.get(speed, 5e-6)
    
    ch_sda = args.sda or 1
    ch_scl = args.scl or 2
    voltage = args.voltage or 3.3
    
    print(f"I2C preset: SDA=CH{ch_sda}, SCL=CH{ch_scl}, speed={speed}, {voltage}V logic")
    _preset_apply(s, f"I2C-{speed}", [ch_sda, ch_scl], timebase,
                  trig_ch=ch_sda, trig_level=voltage * 0.5,
                  scale=voltage / 3, screenshot=args.screenshot)


def cmd_preset_spi(s: Scope, args):
    """SPI preset: 4 channels (SCK, MOSI, MISO, CS), trigger on CS falling."""
    # SPI speeds vary widely: 1MHz to 50MHz+
    speed = args.speed or "1m"
    tb_map = {"1m": 2e-6, "10m": 200e-9, "25m": 100e-9}
    timebase = tb_map.get(speed, 2e-6)
    
    ch_sck = args.sck or 1
    ch_mosi = args.mosi or 2
    ch_miso = args.miso or 3
    ch_cs = args.cs or 4
    voltage = args.voltage or 3.3
    channels = [ch_sck, ch_mosi, ch_miso, ch_cs]
    
    print(f"SPI preset: SCK=CH{ch_sck}, MOSI=CH{ch_mosi}, MISO=CH{ch_miso}, CS=CH{ch_cs}")
    print(f"  speed={speed}, {voltage}V logic")
    _preset_apply(s, f"SPI-{speed}", channels, timebase,
                  trig_ch=ch_cs, trig_level=voltage * 0.5,
                  scale=voltage / 3, screenshot=args.screenshot)


def cmd_preset_uart(s: Scope, args):
    """UART preset: 1 channel, trigger on falling edge (start bit)."""
    # UART baud rates: 9600, 115200, 921600
    baud = args.baud or "115200"
    # Timebase to show ~10 bits
    baud_int = int(baud.replace("k", "000"))
    bit_time = 1.0 / baud_int
    timebase = bit_time * 2  # Show ~2 bits per division (20 bits total)
    
    ch = args.channel or 1
    voltage = args.voltage or 3.3
    
    print(f"UART preset: CH{ch}, baud={baud}, {voltage}V logic")
    print(f"  bit time={bit_time*1e6:.2f}µs, timebase={timebase*1e6:.1f}µs/div")
    _preset_apply(s, f"UART-{baud}", [ch], timebase,
                  trig_ch=ch, trig_level=voltage * 0.5,
                  scale=voltage / 3, screenshot=args.screenshot)


def cmd_preset_i2s(s: Scope, args):
    """I2S preset: 3 channels (BCLK, WS, DATA), trigger on WS edge."""
    # I2S bit clock: typically 1.4MHz (44.1kHz * 32bit) to 12MHz+
    # Default to 3MHz settings
    speed = args.speed or "3m"
    tb_map = {"1m": 2e-6, "3m": 500e-9, "12m": 200e-9}
    timebase = tb_map.get(speed, 500e-9)
    
    ch_bclk = args.bclk or 1
    ch_ws = args.ws or 2
    ch_data = args.data or 3
    voltage = args.voltage or 3.3
    
    print(f"I2S preset: BCLK=CH{ch_bclk}, WS=CH{ch_ws}, DATA=CH{ch_data}")
    print(f"  speed={speed}, {voltage}V logic")
    _preset_apply(s, f"I2S-{speed}", [ch_bclk, ch_ws, ch_data], timebase,
                  trig_ch=ch_ws, trig_level=voltage * 0.5,
                  scale=voltage / 3, screenshot=args.screenshot)


def main():
    p = argparse.ArgumentParser(prog="scopectl")
    p.add_argument("--host", default="192.168.0.75")
    p.add_argument("--debug", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("state", help="dump current scope state").set_defaults(fn=cmd_state)

    p_ch = sub.add_parser("ch", help="channel settings")
    p_ch.add_argument("channel", type=int, choices=(1, 2, 3, 4))
    p_ch.add_argument("--on", action="store_true")
    p_ch.add_argument("--off", action="store_true")
    p_ch.add_argument("--scale", type=float, help="V/div")
    p_ch.add_argument("--offset", type=float, help="V")
    p_ch.add_argument("--coupling", choices=("DC", "AC", "GND"))
    p_ch.add_argument("--probe", type=float, help="probe ratio (1, 10, ...)")
    p_ch.set_defaults(fn=cmd_ch)

    p_tb = sub.add_parser("tb", help="timebase (s/div)")
    p_tb.add_argument("seconds_per_div", type=float)
    p_tb.set_defaults(fn=cmd_tb)

    p_tr = sub.add_parser("trig", help="trigger settings")
    p_tr.add_argument("--src", type=int, choices=(1, 2, 3, 4))
    p_tr.add_argument("--lev", type=float, help="trigger level (V)")
    p_tr.add_argument("--slope", choices=("RISE", "FALL"))
    p_tr.add_argument("--coupling", choices=("AC", "DC"),
                      help="edge-trigger input coupling")
    p_tr.add_argument("--nrej", choices=("on", "off"),
                      help="edge-trigger noise reject (write-only)")
    p_tr.set_defaults(fn=cmd_trig)

    p_cu = sub.add_parser("cursor",
                          help="on-screen cursor positions and deltas")
    p_cu.add_argument("--mode", choices=("OFF", "X", "Y", "XY"))
    p_cu.add_argument("--src", type=int, choices=(1, 2, 3, 4))
    p_cu.add_argument("--x1", type=float, help="X1 position (s)")
    p_cu.add_argument("--x2", type=float, help="X2 position (s)")
    p_cu.add_argument("--y1", type=float, help="Y1 position (V)")
    p_cu.add_argument("--y2", type=float, help="Y2 position (V)")
    p_cu.add_argument("--show", action="store_true",
                      help="enable cursor display (touch toggle)")
    p_cu.add_argument("--hide", action="store_true",
                      help="disable cursor display (touch toggle)")
    p_cu.add_argument("--json", action="store_true")
    p_cu.set_defaults(fn=cmd_cursor)

    sub.add_parser("run").set_defaults(fn=cmd_run)
    sub.add_parser("stop").set_defaults(fn=cmd_stop)
    sub.add_parser("single").set_defaults(fn=cmd_single)
    sub.add_parser("auto").set_defaults(fn=cmd_auto)
    sub.add_parser("reset", help="*RST - close dialogs, reset to defaults").set_defaults(fn=cmd_reset)
    sub.add_parser("ping", help="quick connection test").set_defaults(fn=cmd_ping)

    p_diag = sub.add_parser("diagnose", help="reset + auto + state (one-shot signal find)")
    p_diag.add_argument("-c", "--channel", type=int, choices=(1, 2, 3, 4),
                        help="channel to enable (default: 1)")
    p_diag.add_argument("-s", "--screenshot", metavar="FILE",
                        help="save screenshot to FILE")
    p_diag.set_defaults(fn=cmd_diagnose)

    p_acq = sub.add_parser("acq", help="acquisition mode / status")
    p_acq.add_argument("--type", choices=["NORM", "PEAK"],
                       help="set acquisition type (other modes ignored)")
    p_acq.set_defaults(fn=cmd_acq)

    p_ind = sub.add_parser("indicator", help="toggle web indicator LED")
    p_ind.add_argument("on", type=lambda x: x.lower() in ("on", "1", "true"))
    p_ind.set_defaults(fn=cmd_indicator)

    sub.add_parser("dev-info", help="dump device info JSON"
                   ).set_defaults(fn=cmd_dev_info)

    p_cl = sub.add_parser("click", help="tap a UI button (label or x,y)")
    p_cl.add_argument("label", nargs="?", help="clickmap.json label")
    p_cl.add_argument("--x", type=int, help="raw x coord")
    p_cl.add_argument("--y", type=int, help="raw y coord")
    p_cl.set_defaults(fn=cmd_click)

    p_sv = sub.add_parser("save", help="save scope state to JSON file")
    p_sv.add_argument("path")
    p_sv.set_defaults(fn=cmd_state_save)

    p_ld = sub.add_parser("load", help="restore scope state from JSON file")
    p_ld.add_argument("path")
    p_ld.set_defaults(fn=cmd_state_load)

    p_ss = sub.add_parser("screenshot", help="save PNG of scope screen")
    p_ss.add_argument("out", nargs="?", default="screen.png")
    p_ss.set_defaults(fn=cmd_screenshot)

    p_ms = sub.add_parser("measure", help="enable & OCR on-screen measurements")
    p_ms.add_argument("ch", type=int, choices=(1, 2, 3, 4),
                      help="source channel")
    p_ms.add_argument("kinds", nargs="*",
                      help="measurement names (Vpp Max Min Avg RMS ...)")
    p_ms.add_argument("--tab", default="vertical",
                      choices=("vertical", "horizontal", "others"))
    p_ms.add_argument("--ch-b", type=int, choices=(1, 2, 3, 4),
                      help="source B (required for --tab others)")
    p_ms.add_argument("--no-clear", action="store_true",
                      help="don't clear existing measurements first")
    p_ms.add_argument("--json", action="store_true",
                      help="emit {name: value} JSON only")
    p_ms.add_argument("--debug-dir", help="dump intermediate screenshots here")
    p_ms.set_defaults(fn=cmd_measure)

    p_tu = sub.add_parser("trig-ui",
                          help="drive Trigger dialog via touchscreen "
                               "(for trigger types lacking SCPI)")
    p_tu.add_argument("--type",
                      help="edge|slope|pulse|video|window|interval|runt|"
                           "dropout|pattern|i2c|spi|uart|can|lin")
    p_tu.add_argument("--src", type=int, choices=(1, 2, 3, 4))
    p_tu.add_argument("--slope", choices=("rising", "falling", "either"))
    p_tu.add_argument("--mode", choices=("auto", "normal", "single"))
    p_tu.set_defaults(fn=cmd_trig_ui)

    p_m = sub.add_parser("math",
                         help="drive Math/FFT dialog via touchscreen")
    p_m.add_argument("--operator",
                     choices=("+", "-", "*", "/", "FFT",
                              "d/dt", "intdt", "sqrt"))
    p_m.add_argument("--src", type=int, choices=(1, 2, 3, 4),
                     help="Source A channel")
    p_m.add_argument("--src-b", type=int, choices=(1, 2, 3, 4),
                     help="Source B channel (ignored for FFT/d-dt/intdt/sqrt)")
    p_m.add_argument("--on", action="store_true", help="toggle Operation on")
    p_m.add_argument("--off", action="store_true", help="toggle Operation off")
    p_m.add_argument("--fft-unit", choices=("dBVrms", "Vrms", "dBm"))
    p_m.add_argument("--fft-display", choices=("full", "exclusive"))
    p_m.add_argument("--auto-setup", action="store_true",
                     help="tap FFT Auto Setup")
    p_m.set_defaults(fn=cmd_math)

    p_fp = sub.add_parser("fft-peak",
                          help="OCR top-right FFT peak frequency readout")
    p_fp.add_argument("--debug-dir", help="dump crop+OCR images here")
    p_fp.set_defaults(fn=cmd_fft_peak)

    sq = sub.add_parser("setup-square", help="preset for the test square wave on CH2")
    sq.add_argument("--no-toggle", action="store_true",
                    help="(deprecated, ignored — channel_set is now idempotent)")
    sq.add_argument("--out", help="screenshot path (default: square.png)")
    sq.set_defaults(fn=cmd_setup_square)

    # Protocol presets
    p_i2c = sub.add_parser("preset-i2c", help="I2C preset (SDA+SCL)")
    p_i2c.add_argument("--sda", type=int, choices=(1, 2, 3, 4), help="SDA channel (default: 1)")
    p_i2c.add_argument("--scl", type=int, choices=(1, 2, 3, 4), help="SCL channel (default: 2)")
    p_i2c.add_argument("--speed", choices=("100k", "400k", "1m"), help="I2C speed (default: 400k)")
    p_i2c.add_argument("--voltage", type=float, help="logic voltage (default: 3.3)")
    p_i2c.add_argument("-s", "--screenshot", metavar="FILE", help="save screenshot")
    p_i2c.set_defaults(fn=cmd_preset_i2c)

    p_spi = sub.add_parser("preset-spi", help="SPI preset (SCK+MOSI+MISO+CS)")
    p_spi.add_argument("--sck", type=int, choices=(1, 2, 3, 4), help="SCK channel (default: 1)")
    p_spi.add_argument("--mosi", type=int, choices=(1, 2, 3, 4), help="MOSI channel (default: 2)")
    p_spi.add_argument("--miso", type=int, choices=(1, 2, 3, 4), help="MISO channel (default: 3)")
    p_spi.add_argument("--cs", type=int, choices=(1, 2, 3, 4), help="CS channel (default: 4)")
    p_spi.add_argument("--speed", choices=("1m", "10m", "25m"), help="SPI speed (default: 1m)")
    p_spi.add_argument("--voltage", type=float, help="logic voltage (default: 3.3)")
    p_spi.add_argument("-s", "--screenshot", metavar="FILE", help="save screenshot")
    p_spi.set_defaults(fn=cmd_preset_spi)

    p_uart = sub.add_parser("preset-uart", help="UART preset (single channel)")
    p_uart.add_argument("-c", "--channel", type=int, choices=(1, 2, 3, 4), help="channel (default: 1)")
    p_uart.add_argument("--baud", choices=("9600", "115200", "921600"), help="baud rate (default: 115200)")
    p_uart.add_argument("--voltage", type=float, help="logic voltage (default: 3.3)")
    p_uart.add_argument("-s", "--screenshot", metavar="FILE", help="save screenshot")
    p_uart.set_defaults(fn=cmd_preset_uart)

    p_i2s = sub.add_parser("preset-i2s", help="I2S preset (BCLK+WS+DATA)")
    p_i2s.add_argument("--bclk", type=int, choices=(1, 2, 3, 4), help="BCLK channel (default: 1)")
    p_i2s.add_argument("--ws", type=int, choices=(1, 2, 3, 4), help="WS/LRCLK channel (default: 2)")
    p_i2s.add_argument("--data", type=int, choices=(1, 2, 3, 4), help="DATA channel (default: 3)")
    p_i2s.add_argument("--speed", choices=("1m", "3m", "12m"), help="bit clock (default: 3m)")
    p_i2s.add_argument("--voltage", type=float, help="logic voltage (default: 3.3)")
    p_i2s.add_argument("-s", "--screenshot", metavar="FILE", help="save screenshot")
    p_i2s.set_defaults(fn=cmd_preset_i2s)

    args = p.parse_args()
    with Scope(args.host, debug=args.debug) as s:
        args.fn(s, args)


if __name__ == "__main__":
    main()
