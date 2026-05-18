# Documentation Index

Topic-partitioned docs so AI agents (and humans) load only what's
relevant. Each file is small and self-contained.

| Topic | File | Load when … |
|-------|------|-------------|
| Architecture overview | [architecture.md](architecture.md) | First time orientation; understanding the layered design |
| WebSocket protocol | [protocol.md](protocol.md) | Adding a new opcode, debugging frame handling |
| SCPI dialect | [scpi.md](scpi.md) | Adding a SCPI call (check it isn't broken first) |
| UI coordinates & dialog detection | [ui-coords.md](ui-coords.md) | Mapping a new button or dialog state |
| Measurements (Measure dialog + OCR) | [measurements.md](measurements.md) | Adding a new measurement or fixing OCR |
| Cursors | [cursors.md](cursors.md) | Anything touching `:CURS:*` or cursor display |
| Triggers (edge + advanced) | [triggers.md](triggers.md) | Trigger types, holdoff, noise reject |
| Math / FFT | [math-fft.md](math-fft.md) | Math operators, FFT peak readout |
| Known issues / footguns | [known-issues.md](known-issues.md) | When something acts weirdly |

## Hardware quick facts

- **Scope**: FNIRSI DPOF1204-200, 200 MHz, 1 GS/s, 14 Mpts
- **Firmware**: V1.0.1.26020603
- **Screen**: 800 × 480, RGB565 framebuffer (768 000 B/frame)
- **Default IP**: `192.168.0.75`
- **Only TCP/80 is open.** No raw SCPI port. No telnet. No SSH.
- **Single client** — browser UI competes with scripts.

## How the library is split

```
scope.py        ← Scope class (WebSocket SCPI + touchscreen + helpers)
scopectl.py     ← argparse CLI
screen.py       ← framebuffer capture + PNG encode
measure.py      ← Measure dialog coords + OCR helpers
trigger.py      ← Trigger dialog coords (type grid, source, slope, mode, …)
mathui.py       ← Math / FFT dialog coords
channel_state.py← Read channel on/off from screenshot badges
clickmap.py     ← Interactive coord recorder
clickmap.json   ← Persisted button coordinates
```
