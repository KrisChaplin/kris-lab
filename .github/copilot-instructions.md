# GitHub Copilot instructions

This repository is a Python control library and CLI for the FNIRSI
DPOF1204-200 oscilloscope. Read [AGENTS.md](../AGENTS.md) for the full
agent guide; this file captures Copilot-specific conventions.

## Project shape

- Top-level flat layout — modules import each other as bare names
  (`from screen import capture`, `from trigger import TRIG_TYPES`, etc.).
  Do not move files into a package directory without updating every
  import.
- CLI entry: [scopectl.py](../scopectl.py) — argparse subcommands.
- Library entry: `Scope` class in [scope.py](../scope.py).
- Documentation: [docs/INDEX.md](../docs/INDEX.md) is the table of
  contents. Each topic is its own small file — load only what you need.

## Code style

- Python 3.10+ syntax (`str | None`, structural pattern matching OK).
- Type hints on public methods; no `from __future__ import annotations`
  in new files unless the file already had it.
- Touchscreen coordinates are kept as module-level `UPPER_SNAKE`
  constants in `trigger.py` / `measure.py` / `mathui.py`.
- Pixel-sampling helpers belong in `scope.py` as nested functions of the
  method that owns them — they tend to be one-shot and aren't worth
  exposing.
- No docstring-adding passes on code you didn't otherwise change.

## Critical runtime gotchas

1. The scope firmware buffers exactly one pending SCPI reply, released
   on the next command. `Scope._exchange()` already pairs every real
   command with a dummy `get_dev_info` to flush. Never call `ws.send`
   directly.
2. Many SCPI commands return `"deadline has elapsed"` — see
   [docs/scpi.md](../docs/scpi.md) before adding new ones.
3. No waveform binary export exists on this firmware.
4. Touchscreen needs a `down`+`up` pair (use `Scope.touch()`).
5. Image-budget caps — sample pixels with PIL rather than viewing every
   PNG.

## Test signal assumed by examples

CH3 + CH4 square wave, both on 100 mV/div, trigger CH3 rising at 0.15 V,
timebase 500 µs/div → 1 kHz, Vpp 312 mV.

## Don't

- Don't auto-commit. The human runs `git add`/`commit` after testing.
- Don't refactor unrelated code while fixing a bug.
- Don't add new top-level dependencies without updating
  [requirements.txt](../requirements.txt).
