# kris-lab

Automation libraries and AI agent instructions for lab instruments.

Each instrument lives in its own folder with dedicated code, CLI tools,
and agent-readable documentation.

## Instruments

| Folder | Instrument | Status |
|--------|------------|--------|
| [fnirsi-oscilloscope/](fnirsi-oscilloscope/) | FNIRSI DPOF1204-200 (200 MHz, 1 GS/s) | ✅ Working |
| *(coming soon)* | Logic analyzer | 🚧 Planned |

## Quick start

```bash
pip install -r requirements.txt          # common deps (also needs system `tesseract`)

# FNIRSI oscilloscope
cd fnirsi-oscilloscope
python scopectl.py state                  # dump scope state
python scopectl.py screenshot out.png     # capture screen
```

## For AI agents

This repo has agent-discovery hooks at the top level:
- [AGENTS.md](AGENTS.md) — universal entry point (Claude Code, Cursor, Aider, etc.)
- [.github/copilot-instructions.md](.github/copilot-instructions.md) — GitHub Copilot

Each instrument folder has its own `AGENTS.md` with instrument-specific
conventions and a `docs/` subfolder with detailed topic files.

## Repository structure

```
kris-lab/
├── AGENTS.md                  ← Top-level agent guide
├── README.md                  ← You are here
├── requirements.txt           ← Common Python dependencies
├── LICENSE
├── .github/
│   └── copilot-instructions.md
└── fnirsi-oscilloscope/       ← FNIRSI DPOF1204-200 oscilloscope
    ├── AGENTS.md              ← Oscilloscope-specific agent guide
    ├── README.md
    ├── scopectl.py            ← CLI
    ├── scope.py               ← Library
    ├── docs/                  ← Topic-partitioned documentation
    └── tools/                 ← Diagnostic/probe scripts
```

## License

[MIT](LICENSE) © 2026 Kris Chaplin. Credit appreciated when
redistributing — see the attribution clause in the license file.

