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

- Flat layout — modules import each other as bare names within the folder.
- CLI entry: `scopectl.py` — argparse subcommands.
- Library entry: `Scope` class in `scope.py`.
- Documentation: `docs/INDEX.md` is the table of contents.
- Touchscreen coordinates are module-level `UPPER_SNAKE` constants.
- See [fnirsi-oscilloscope/AGENTS.md](../fnirsi-oscilloscope/AGENTS.md)
  for critical runtime gotchas (SCPI buffering, dialog detection, etc.).

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
