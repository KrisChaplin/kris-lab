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
| [glkvm-comet/](../glkvm-comet/) | GL.iNet GL-RM1PE Comet PoE KVM | [AGENTS.md](../glkvm-comet/AGENTS.md) |
| [devantech-eth008b/](../devantech-eth008b/) | Devantech ETH008-B relay board | [AGENTS.md](../devantech-eth008b/AGENTS.md) |

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

## Devantech ETH008-B quick reference

Location: [devantech-eth008b/](../devantech-eth008b/)

**Address:** `192.168.0.200`, TCP command port 17494. Standard library only.

```bash
cd devantech-eth008b
python relayctl.py info                 # module id, versions, MAC, supply volts
python relayctl.py status               # 0x0d  00001101  1:ON 2:off ...
python relayctl.py on 3                 # energise relay 3
python relayctl.py off 3
python relayctl.py on 3 --pulse 2.5     # auto-release after 2.5 s
python relayctl.py set 1,3,4            # whole mask in one command
python relayctl.py all-off
```

**Key facts:**
- ⚠️ Contacts drive powered equipment — **never switch faster than 3 Hz**.
  `relayctl.py` enforces this; do not pass `--no-rate-limit`.
- Read `status` first and restore the mask you found when probing.
- Relays are 1-8; the `0x24` bitmask uses bit 0 for relay 1.
- Pulsed `off` means "off for N seconds then back **on**", not a delayed off.
- No inputs on this model; input commands just time out.
- Only 5 concurrent TCP connections, and a command is dropped if the socket
  closes before its acknowledgement is read.
- See [devantech-eth008b/AGENTS.md](../devantech-eth008b/AGENTS.md) for the full
  command sets.
