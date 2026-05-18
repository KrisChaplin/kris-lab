# Kingst LA2016 Logic Analyzer

16-channel USB logic analyzer with 200 MHz max sample rate, controlled via
[sigrok](https://sigrok.org/) open-source software.

## Hardware

- **Model**: Kingst LA2016
- **Channels**: 16 logic + 2 PWM outputs
- **Max sample rate**: 200 MHz
- **Memory**: 128 MiB DDR2 SDRAM
- **Input voltage**: -50V to +50V tolerant
- **Threshold**: Configurable 0.4V to 4.0V

## Software Setup

This device uses sigrok-cli and PulseView with the `kingst-la2016` driver.
The Ubuntu 22.04 package is too old, so a custom build is installed at:

```
/mnt/github-runner-mounts/tools/sigrok-local/
```

Wrapper scripts handle the library paths:

```bash
# CLI (for automation)
/mnt/github-runner-mounts/tools/sigrok-local/bin/sigrok-cli-la2016

# GUI (for humans)
/mnt/github-runner-mounts/tools/sigrok-local/bin/pulseview-la2016
```

### Firmware

FPGA firmware was extracted from KingstVIS and installed to:
```
/mnt/github-runner-mounts/tools/sigrok-firmware/
```

## Quick Start

```bash
# Scan for device
sigrok-cli-la2016 --scan

# Show device capabilities
sigrok-cli-la2016 -d kingst-la2016 --show

# Capture 10000 samples at 10 MHz
sigrok-cli-la2016 -d kingst-la2016 --config samplerate=10M --samples 10000 -o capture.sr

# Capture with trigger on CH0 rising edge
sigrok-cli-la2016 -d kingst-la2016 --config samplerate=10M --samples 10000 \
    --triggers CH0=r -o capture.sr

# Decode I2C protocol (requires libsigrokdecode)
sigrok-cli-la2016 -d kingst-la2016 --config samplerate=1M --samples 100000 \
    -P i2c:scl=CH0:sda=CH1
```

## Sample Rates

| Rate | Use case |
|------|----------|
| 200 MHz | High-speed digital, SPI at 50+ MHz |
| 100 MHz | Fast SPI, JTAG |
| 10 MHz | I2C, UART, moderate SPI |
| 1 MHz | Slow protocols, long captures |

## Voltage Thresholds

| Threshold | Logic family |
|-----------|--------------|
| 0.9V | LVCMOS 1.8V |
| 1.4V | LVCMOS 3.3V (default) |
| 2.5V | CMOS 5V |
| 4.0V | High-voltage logic |

## For AI Agents

See [AGENTS.md](AGENTS.md) for automation instructions and
[docs/INDEX.md](docs/INDEX.md) for detailed topic documentation.

## See Also

- [sigrok wiki: Kingst LA2016](https://sigrok.org/wiki/Kingst_LA2016)
- [sigrok wiki: Kingst LA Series](https://sigrok.org/wiki/Kingst_LA_Series)
