# GitHub Copilot instructions

This repository contains automation libraries and AI agent instructions
for multiple lab instruments. Read [AGENTS.md](../AGENTS.md) for the
full agent guide; this file captures Copilot-specific conventions.

## Repository structure

Each instrument lives in its own folder with dedicated code and docs:

| Folder | Instrument | Agent guide |
|--------|------------|-------------|
| [fnirsi-oscilloscope/](../fnirsi-oscilloscope/) | FNIRSI DPOF1204-200 | [AGENTS.md](../fnirsi-oscilloscope/AGENTS.md) |

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
