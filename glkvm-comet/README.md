# GL.iNet Comet PoE KVM

Automation for the GL.iNet GL-RM1PE Comet PoE Remote KVM Controller connected
to the lab board.

## Quick Start

```bash
cd glkvm-comet
python kvmctl.py screenshot /tmp/glkvm.png
python kvmctl.py click 640 360 --image /tmp/glkvm.png
python kvmctl.py type 'hello from the KVM'
python kvmctl.py key Enter
```

The default endpoint is `192.168.0.77` and the default username is `admin`.
The tool securely prompts for the password, or reads `GLKVM_PASSWORD` from the
process environment. It does not persist passwords or session tokens.

Run `python kvmctl.py --help` for all commands. See `docs/INDEX.md` for the
automation workflow and protocol notes.