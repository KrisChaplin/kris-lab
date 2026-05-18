# Known Issues — Kingst LA2016

> **Load this when:** Something acts weird, unexpected behavior.

## Trigger Limitations

**Only ONE edge trigger allowed.**

```bash
# ✅ Works: one edge + any number of level triggers
--triggers CH0=r,CH1=1,CH2=0

# ❌ Broken: multiple edge triggers (undefined behavior)
--triggers CH0=r,CH1=f
```

The hardware only supports a single edge trigger. The software accepts
multiple but behavior is undefined.

## PulseView + VS Code Snap

Running PulseView from VS Code's integrated terminal causes crashes due
to snap environment contamination.

**Fix:** Run from regular terminal, or:
```bash
env -i HOME=$HOME DISPLAY=$DISPLAY /mnt/github-runner-mounts/tools/sigrok-local/bin/pulseview-la2016
```

## No Configuration Readback

The FPGA registers are write-only or have different read/write meanings.
Software cannot read back previously applied settings.

**Implication:** Each session starts from defaults. Don't expect settings
to persist or be queryable.

## Memory Limits

| Sample Rate | Approx Duration | Samples (uncompressed) |
|-------------|-----------------|------------------------|
| 200 MHz | ~5 seconds | ~40M |
| 100 MHz | ~10 seconds | ~80M |
| 10 MHz | ~100 seconds | ~800M |
| 1 MHz | ~1000 seconds | ~8G (with compression) |

Compression helps significantly for slow-changing signals. Fast random
data compresses poorly.

## Streaming Mode Limits

Streaming (continuous capture) is limited by USB bandwidth:
- ~300 Mbps effective
- At 200 MHz with 16 channels = 3.2 Gbps → won't work
- At 10 MHz with 4 channels = 40 Mbps → works

For most uses, normal capture mode (to memory, then download) is better.

## Channel Numbering

Channels are CH0-CH15 (not CH1-CH16). The PWM outputs are PWM1 and PWM2.

## Voltage Threshold

Default is 1.4V (suitable for 3.3V logic). For 5V logic, use 2.5V.
For 1.8V logic, use 0.9V.

```bash
--config voltage_threshold=2.5-2.5
```

Note the `X-X` format (threshold specified twice).

## Protocol Decoder Gotchas

### I2C
- Both SCL and SDA required
- Sample rate must be ≥10× clock rate

### SPI
- CS is optional but recommended for framing
- MISO is optional for write-only captures
- Mode (CPOL/CPHA) defaults may not match your device

### UART
- Only RX or TX can be decoded per decoder instance
- For bidirectional, use two decoder instances

## Firmware Already Loaded

Don't search for or try to install firmware. The wrapper script sets
`SIGROK_FIRMWARE_DIR` and firmware is pre-installed at:

```
/mnt/github-runner-mounts/tools/sigrok-firmware/
```
