# Agent Guide — kris-lab

> Entry point for AI coding agents (Claude Code, Cursor, Aider, Continue,
> Codex, etc.). Human entry point is [README.md](README.md).

## What this repo is

Automation libraries and AI agent instructions for multiple lab
instruments. Each instrument has its own folder with dedicated code,
CLI tools, and documentation.

## Instruments

| Folder | Instrument | Agent guide |
|--------|------------|-------------|
| [fnirsi-oscilloscope/](fnirsi-oscilloscope/) | FNIRSI DPOF1204-200 oscilloscope | [fnirsi-oscilloscope/AGENTS.md](fnirsi-oscilloscope/AGENTS.md) |
| *(coming soon)* | Logic analyzer | — |

## Global conventions for agents

1. **Do not auto-commit.** Local edits only; the human tests and commits.
2. **Each instrument folder is self-contained.** Code, docs, and tools
   for an instrument live in its folder.
3. **Instrument-specific rules live in `<folder>/AGENTS.md`.** Load that
   file when working on a specific instrument.
4. **Documentation is partitioned by topic.** Each instrument has a
   `docs/INDEX.md` that fans out to small focused files. Load only what
   you need.
5. **Python 3.10+ syntax** (`str | None`, pattern matching OK).
6. **Don't add dependencies** without updating `requirements.txt`.
7. **Image-budget rule:** when inspecting many screenshots, sample
   pixels programmatically with PIL rather than viewing each PNG.

## How to navigate

1. Identify which instrument the task concerns.
2. Load that instrument's `AGENTS.md` for specific conventions and
   gotchas.
3. Load topic files from `<instrument>/docs/` as needed.

## Adding a new instrument

1. Create a new folder: `<instrument-name>/`
2. Add `AGENTS.md` with instrument-specific conventions.
3. Add `README.md` with human-readable overview.
4. Add `docs/INDEX.md` pointing to topic files.
5. Update this file's instrument table.
6. Update `.github/copilot-instructions.md` if needed.
