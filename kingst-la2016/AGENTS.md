# Agent Guide — Kingst LA2016 Logic Analyzer

> Instrument-specific entry point for AI coding agents. For the full lab
> overview, see [../AGENTS.md](../AGENTS.md).

## TL;DR — Copy These

```bash
# The one command prefix you need (always use this):
LACLI="/mnt/github-runner-mounts/tools/sigrok-local/bin/sigrok-cli-la2016"

# Scan
$LACLI --scan

# Basic capture (TEMPLATE - fill in values)
$LACLI -d kingst-la2016 --config samplerate=<RATE> --samples <COUNT> -o <FILE>.sr

# Triggered capture
$LACLI -d kingst-la2016 --config samplerate=<RATE> --samples <COUNT> --triggers <CH>=<EDGE> -o <FILE>.sr

# Protocol decode (outputs to stdout)
$LACLI -d kingst-la2016 --config samplerate=<RATE> --samples <COUNT> -P <DECODER>
```

## Protocol Cookbook — Use Exactly These

| Protocol | Sample Rate | Decoder String | Typical Samples |
|----------|-------------|----------------|-----------------|
| I2C 100kHz | 1M | `-P i2c:scl=CH0:sda=CH1` | 100000 |
| I2C 400kHz | 4M | `-P i2c:scl=CH0:sda=CH1` | 100000 |
| SPI 1MHz | 10M | `-P spi:clk=CH0:mosi=CH1:miso=CH2:cs=CH3` | 50000 |
| SPI 10MHz | 100M | `-P spi:clk=CH0:mosi=CH1:miso=CH2:cs=CH3` | 50000 |
| UART 115200 | 1M | `-P uart:rx=CH0:baudrate=115200` | 100000 |
| UART 9600 | 500k | `-P uart:rx=CH0:baudrate=9600` | 50000 |
| 1-Wire | 1M | `-P onewire_link:owr=CH0` | 100000 |

**Rule of thumb:** Sample rate = 10× the bit rate minimum, 20× preferred.

## Trigger Syntax — All Options

```
--triggers CH0=r      # Rising edge (most common)
--triggers CH0=f      # Falling edge
--triggers CH0=1      # High level
--triggers CH0=0      # Low level
--triggers CH0=r,CH1=1  # Rising on CH0 AND CH1 high (combined)
```

**⚠️ Only ONE edge trigger allowed.** Multiple edge triggers = undefined behavior.
Level triggers can be combined freely.

## Output Formats

```bash
-o capture.sr           # Native (default, best for re-analysis)
-O csv -o capture.csv   # Spreadsheet/pandas
-O vcd -o capture.vcd   # GTKWave/waveform viewers  
-O ascii                # Stdout ASCII art (no -o)
```

## Sample Rate Decision Table

| Use Case | Rate | Why |
|----------|------|-----|
| I2C standard (100kHz) | 1M | 10× oversampling |
| I2C fast (400kHz) | 4M | 10× oversampling |
| SPI ≤1MHz | 10M | 10× oversampling |
| SPI ≤10MHz | 100M | 10× oversampling |
| SPI >10MHz | 200M | Maximum rate |
| UART any baud | 1M | Plenty for serial |
| Unknown/debug | 10M | Good default |
| Long capture (>10s) | 1M or less | Memory limit |

## Anti-Patterns — Don't Do These

1. **Don't use multiple edge triggers** — Hardware only supports one
2. **Don't search for sigrok-cli in PATH** — Use the wrapper path directly
3. **Don't look for firmware** — It's already installed, just use the wrapper
4. **Don't try `--continuous` without reason** — Memory mode is better
5. **Don't decode AND save to file** — Do one or the other, or pipe
6. **Don't use 200MHz for slow protocols** — Wastes memory, limits capture time

## Device Facts (Memorize These)

- **Channels:** CH0-CH15 (16 logic) + PWM1, PWM2 (outputs)
- **Max rate:** 200 MHz
- **Memory:** 128 MiB → ~40M samples guaranteed, more with compression
- **Threshold:** Default 1.4V (3.3V logic), configurable 0.4-4.0V
- **USB:** VID:PID 77a1:01a2
- **Connection:** Always `kingst-la2016:conn=1.10` (or similar bus.device)

## GUI (For Humans)

```bash
/mnt/github-runner-mounts/tools/sigrok-local/bin/pulseview-la2016
```

Run from regular terminal, not VS Code integrated terminal (snap conflicts).

## File Paths — Reference

| What | Path |
|------|------|
| CLI wrapper | `/mnt/github-runner-mounts/tools/sigrok-local/bin/sigrok-cli-la2016` |
| GUI wrapper | `/mnt/github-runner-mounts/tools/sigrok-local/bin/pulseview-la2016` |
| Firmware dir | `/mnt/github-runner-mounts/tools/sigrok-firmware/` |
| Install prefix | `/mnt/github-runner-mounts/tools/sigrok-local/` |
