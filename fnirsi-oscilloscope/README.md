# FNIRSI DPOF1204-200 Oscilloscope

Python control library and CLI for the **FNIRSI DPOF1204-200** oscilloscope
(200 MHz, 1 GS/s, 14 Mpts, firmware V1.0.1.26020603).

Drives the scope over its embedded WebSockets:
- `ws://<ip>/ws_control` — JSON-framed SCPI + touchscreen passthrough
- `ws://<ip>/ws_image` — 800×480 RGB565 framebuffer (one shot per `getImage`)

The firmware's SCPI is partial. Measurements, math/FFT, cursors and
advanced triggers have **no working SCPI** — this library drives the
on-screen UI by tapping mapped coordinates and reads results via OCR.

## Quick start

```bash
# From repo root
pip install -r requirements.txt          # also needs system `tesseract`

# Run from this folder
cd fnirsi-oscilloscope
python scopectl.py state                  # dump everything
python scopectl.py ch 2 --on --scale 1.0  # configure CH2
python scopectl.py tb 500e-6              # 500 µs/div
python scopectl.py trig --src 2 --lev 0.5 --slope RISE
python scopectl.py screenshot out.png
python scopectl.py measure 3 Vpp Freq     # OCR-driven
python scopectl.py cursor --src 3 --mode X --x1 -5e-4 --x2 5e-4 --show
```

Default host is `192.168.0.75`; override with `--host` on every subcommand.

## File map

| File | Role |
|------|------|
| [scope.py](scope.py) | `Scope` class — WebSocket SCPI + touchscreen + helpers |
| [scopectl.py](scopectl.py) | CLI front-end (state / ch / tb / trig / measure / cursor / math / fft-peak / save / load / screenshot / ...) |
| [screen.py](screen.py) | `capture()` / `save_png()` — RGB565 → PNG |
| [measure.py](measure.py) | Measure dialog tile coords + `ocr_readouts()` |
| [trigger.py](trigger.py) | Trigger dialog tile coords |
| [mathui.py](mathui.py) | Math / FFT dialog tile coords |
| [channel_state.py](channel_state.py) | Detect channel on/off by badge colour |
| [clickmap.py](clickmap.py) | Interactive coord-recorder for the touchscreen |
| [clickmap.json](clickmap.json) | Persisted button coordinates |
| [tools/](tools/) | One-off probes (SCPI survey, opcode discovery, sav/rcl) |
| [docs/INDEX.md](docs/INDEX.md) | **Start here — topic-partitioned documentation index** |

## For AI agents

See [AGENTS.md](AGENTS.md) in this folder for FNIRSI-specific agent
instructions. The top-level [../AGENTS.md](../AGENTS.md) provides the
overview for all instruments in the lab.

## Status

Working: channel config, edge trigger basics, timebase, run/stop, ACQ
NORM/PEAK, screenshot capture, OCR measurements (all 4 channels, three
Measure tabs), Math/FFT dialog control, FFT peak OCR, cursor positions
and on-screen display toggle, trigger edge coupling / noise-reject /
holdoff query.

Not working (firmware): waveform binary export (verified absent — see
[docs/scpi.md](docs/scpi.md)), `*SAV`/`*RCL`, advanced trigger SCPI,
`:MEAS:*?`, `:MATH:*`, `:CURS:*` queries (most), `:ACQ:TYPE AVER/HRES`.

## License

See [../LICENSE](../LICENSE) in repo root.
