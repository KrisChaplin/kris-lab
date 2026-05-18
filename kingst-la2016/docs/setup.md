# Setup & Installation — Kingst LA2016

> **Load this only for:** First-time setup, rebuilding, troubleshooting.
> For normal operation, AGENTS.md has everything needed.

## Why Custom Build?

Ubuntu 22.04's sigrok package (libsigrok 0.5.2) is too old — the
`kingst-la2016` driver was added later. A custom build from git master
is installed to `/mnt/github-runner-mounts/tools/sigrok-local/`.

## Installed Components

| Component | Version | Location |
|-----------|---------|----------|
| libsigrok | 0.6.0-git | sigrok-local/lib/ |
| libsigrokcxx | 0.6.0-git | sigrok-local/lib/ (C++ bindings) |
| libsigrokdecode | 0.6.0-git | sigrok-local/lib/ (protocol decoders) |
| sigrok-cli | 0.8.0-git | sigrok-local/bin/ |
| PulseView | 0.5.0-git | sigrok-local/bin/ |

## Source Locations (for rebuilding)

```
/mnt/github-runner-mounts/tools/libsigrok/
/mnt/github-runner-mounts/tools/libsigrokdecode/
/mnt/github-runner-mounts/tools/sigrok-cli-src/
/mnt/github-runner-mounts/tools/pulseview-src/
/mnt/github-runner-mounts/tools/sigrok-util/        # firmware extraction tools
```

## Firmware Extraction

Firmware was extracted from KingstVIS using:

```bash
cd /mnt/github-runner-mounts/tools/sigrok-util/firmware/kingst-la
./sigrok-fwextract-kingst-la2016 /mnt/github-runner-mounts/tools/KingstVIS/KingstVIS
```

Extracted files copied to: `/mnt/github-runner-mounts/tools/sigrok-firmware/`

## USB Permissions

udev rule at `/etc/udev/rules.d/60-kingst.rules`:

```
ACTION!="add|change", GOTO="kingst_rules_end"
SUBSYSTEM!="usb", GOTO="kingst_rules_end"
ATTR{idVendor}=="77a1", ATTR{idProduct}=="01a2", MODE="0664", GROUP="plugdev", TAG+="uaccess"
LABEL="kingst_rules_end"
```

Reload with: `sudo udevadm control --reload-rules && sudo udevadm trigger`

## Rebuild Commands

```bash
# Set PKG_CONFIG_PATH for all builds
export PKG_CONFIG_PATH=/mnt/github-runner-mounts/tools/sigrok-local/lib/pkgconfig

# libsigrok
cd /mnt/github-runner-mounts/tools/libsigrok
make clean && ./configure --prefix=/mnt/github-runner-mounts/tools/sigrok-local
make -j$(nproc) && make install

# libsigrokdecode
cd /mnt/github-runner-mounts/tools/libsigrokdecode
make clean && ./configure --prefix=/mnt/github-runner-mounts/tools/sigrok-local
make -j$(nproc) && make install

# sigrok-cli
cd /mnt/github-runner-mounts/tools/sigrok-cli-src
make clean && PKG_CONFIG_PATH=... ./configure --prefix=...
make -j$(nproc) && make install

# PulseView
cd /mnt/github-runner-mounts/tools/pulseview-src/build
rm -rf * && PKG_CONFIG_PATH=... cmake -DCMAKE_INSTALL_PREFIX=... ..
make -j$(nproc) && make install
```

## Build Dependencies (Ubuntu 22.04)

```bash
sudo apt install -y git gcc g++ make autoconf automake libtool pkg-config \
  libglib2.0-dev libzip-dev libusb-1.0-0-dev libftdi1-dev libhidapi-dev \
  libserialport-dev sdcc check doxygen python3-dev libglibmm-2.4-dev \
  libboost-all-dev qtbase5-dev libqt5svg5-dev qttools5-dev cmake swig \
  python3-setuptools python3-numpy
```

## Troubleshooting

### Device not detected
1. Check USB: `lsusb | grep 77a1`
2. Check permissions: `ls -la /dev/bus/usb/$(lsusb | grep 77a1 | awk '{print $2"/"$4}' | tr -d ':')`
3. Reload udev rules and re-plug device

### Library errors
- Ensure wrapper scripts are used (they set LD_LIBRARY_PATH)
- Check `ldd /mnt/github-runner-mounts/tools/sigrok-local/bin/sigrok-cli`

### PulseView crashes in VS Code terminal
- Run from regular terminal (snap environment conflict)
- Or use: `env -i HOME=$HOME DISPLAY=$DISPLAY /path/to/pulseview-la2016`
