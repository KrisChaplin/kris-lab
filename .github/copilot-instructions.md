# GitHub Copilot instructions

This repository contains automation libraries and AI agent instructions
for multiple lab instruments. Read [AGENTS.md](../AGENTS.md) for the
full agent guide; this file captures Copilot-specific conventions.

## Repository structure

Each instrument lives in its own folder with dedicated code and docs:

| Folder | Instrument | Agent guide |
|--------|------------|-------------|
| [fnirsi-oscilloscope/](../fnirsi-oscilloscope/) | FNIRSI DPOF1204-200 | [AGENTS.md](../fnirsi-oscilloscope/AGENTS.md) |
| [kingst-la2016/](../kingst-la2016/) | Kingst LA2016 | [AGENTS.md](../kingst-la2016/AGENTS.md) |

## Global conventions

- **Do not auto-commit.** The human runs `git add`/`commit` after testing.
- **Python 3.10+ syntax** (`str | None`, structural pattern matching OK).
- Type hints on public methods.
- Don't add new dependencies without updating `requirements.txt`.
- Don't refactor unrelated code while fixing a bug.

## Instrument-specific work

When working on a specific instrument:
1. Load that instrument's `AGENTS.md` for conventions and gotchas.
2. Load topic files from `<instrument>/docs/` as needed.
3. Run CLI tools from within the instrument folder.

## FNIRSI Oscilloscope quick reference

Location: [fnirsi-oscilloscope/](../fnirsi-oscilloscope/)

**Working directory:** `cd /home/krisc/work/kris_lab/kris-lab/fnirsi-oscilloscope`

**One-shot signal find (recommended start):**
```bash
python scopectl.py diagnose -c <CH> -s /tmp/scope.png
```

**Or clear dialogs first (choose one):**
```bash
python scopectl.py reset                           # Closes dialogs + resets settings
python scopectl.py click measure_button && sleep 0.3 && python scopectl.py click measure_button  # Closes dialogs only
```

**Key commands:**
```bash
python scopectl.py state                          # Current settings
python scopectl.py auto                           # Auto-set (finds signal)
python scopectl.py screenshot /tmp/scope.png     # Visual check
python scopectl.py ch <N> --on --scale <V/div>   # Channel + voltage scale
python scopectl.py tb <s/div>                    # Timebase (e.g., 500e-6)
python scopectl.py trig --src <N> --lev <V> --slope RISE
python scopectl.py measure <ch> Vpp Freq         # OCR measurements
```

**Key facts:**
- If commands silently fail, a dialog may be blocking — run safe init
- Adjust scale until signal fills 3-5 vertical divisions
- Adjust timebase to show 2-4 complete cycles
- One WebSocket client only — close browser UI before scripts
- See [fnirsi-oscilloscope/AGENTS.md](../fnirsi-oscilloscope/AGENTS.md) for full reference

## Kingst LA2016 quick reference

Location: [kingst-la2016/](../kingst-la2016/)

**CLI wrapper (use this exact path):**
```
/mnt/github-runner-mounts/tools/sigrok-local/bin/sigrok-cli-la2016
```

**Command template:**
```bash
sigrok-cli-la2016 -d kingst-la2016 --config samplerate=<RATE> --samples <N> [--triggers CH0=r] [-P i2c:scl=CH0:sda=CH1] -o out.sr
```

**Key facts:**
- 16 channels (CH0-CH15), 200 MHz max, 128 MiB memory
- Rates: 1M (I2C/UART), 10M (slow SPI), 100M (fast SPI)
- Triggers: `CH0=r` (rise), `=f` (fall), `=1` (high), `=0` (low)
- Only ONE edge trigger allowed (level triggers can combine)
- GUI: `pulseview-la2016` (run from regular terminal, not VS Code)
- See [kingst-la2016/AGENTS.md](../kingst-la2016/AGENTS.md) for full command reference.
