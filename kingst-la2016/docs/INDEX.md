# Documentation Index — Kingst LA2016

**For most tasks, AGENTS.md has everything you need.** Only load these
files when troubleshooting or doing advanced work.

| Topic | File | Load when … |
|-------|------|-------------|
| Setup & installation | [setup.md](setup.md) | First-time setup, rebuilding, troubleshooting connection |
| Advanced decoders | [decoders.md](decoders.md) | Stacking decoders, uncommon protocols |
| Known issues | [known-issues.md](known-issues.md) | Something acts weird |

## Quick Facts (Don't Re-Discover These)

```
WRAPPER:    /mnt/github-runner-mounts/tools/sigrok-local/bin/sigrok-cli-la2016
GUI:        /mnt/github-runner-mounts/tools/sigrok-local/bin/pulseview-la2016
FIRMWARE:   /mnt/github-runner-mounts/tools/sigrok-firmware/
DEVICE:     kingst-la2016
CHANNELS:   CH0-CH15 (logic), PWM1-PWM2 (output)
MAX RATE:   200 MHz
MEMORY:     128 MiB (~40M+ samples with compression)
THRESHOLD:  1.4V default (3.3V logic)
```

## Command Templates

```bash
# Set this once per session
LACLI="/mnt/github-runner-mounts/tools/sigrok-local/bin/sigrok-cli-la2016"

# Capture pattern
$LACLI -d kingst-la2016 --config samplerate=<RATE> --samples <N> [--triggers <T>] [-P <decoder>] [-o <file>]

# Common rates: 1M (I2C/UART), 10M (slow SPI), 100M (fast SPI), 200M (max)
# Trigger: CH0=r (rise), CH0=f (fall), CH0=1 (high), CH0=0 (low)
```

## Protocol Quick Reference

| Protocol | Rate | Decoder |
|----------|------|---------|
| I2C | 1M-4M | `-P i2c:scl=CH0:sda=CH1` |
| SPI | 10M-100M | `-P spi:clk=CH0:mosi=CH1:miso=CH2:cs=CH3` |
| UART | 1M | `-P uart:rx=CH0:baudrate=115200` |

## Output Quick Reference

| Format | Flag | Use |
|--------|------|-----|
| Native | `-o file.sr` | Re-analysis in PulseView |
| CSV | `-O csv -o file.csv` | Pandas/spreadsheet |
| VCD | `-O vcd -o file.vcd` | GTKWave |
