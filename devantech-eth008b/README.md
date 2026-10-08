# Devantech ETH008-B Ethernet Relay Board

Eight-channel volt-free-contact relay board on the lab network at
`192.168.0.200`. Used to switch power and signal lines to other bench
equipment under script control.

## Quick start

```bash
cd devantech-eth008b

python relayctl.py info              # module id, versions, MAC, supply voltage
python relayctl.py status            # state of all eight relays
python relayctl.py on 3              # energise relay 3
python relayctl.py off 3             # de-energise relay 3
python relayctl.py on 3 --pulse 2.5  # energise relay 3 for 2.5 s, then release
python relayctl.py toggle 3
python relayctl.py set 1,3,4         # set all eight relays at once
python relayctl.py all-off
python relayctl.py watch             # poll and print state changes
```

`relayctl.py` uses only the Python standard library. Run
`python relayctl.py --help` for the full command reference.

## Safety

> **The relay contacts are wired to powered lab equipment.**

- **Never switch a relay faster than 3 Hz.** `relayctl.py` enforces a
  333 ms minimum between state changes. `--no-rate-limit` removes the
  guard and should not be used against this board.
- Read `status` before and after any change, and restore the mask you
  found if you were only probing.
- The board has no input channels, so it cannot tell you whether the
  equipment downstream actually responded. Confirm that separately.

## Board facts

| Property | Value |
|----------|-------|
| Model | ETH008-B (module id 19) |
| Address | `192.168.0.200`, hostname `ETH008`, DHCP enabled |
| MAC | `44:b7:d0:a5:79:e2` |
| Hardware / firmware | v2 / v28 |
| TCP command port | 17494 |
| Supply | 12 V DC, 2.1 mm jack, positive core (reads ~11.9 V) |
| Relays | 8 × SPDT volt-free, 16 A @ 250 V AC / 16 A @ 24 V DC |
| Inputs | None — this model is outputs only |

## Web interface

`http://192.168.0.200/` shows live relay state and lets you click the
bullets to toggle. HTTP authentication is currently **disabled** on this
board, as is the TCP/IP password. Settings pages:

- `config.htm` — network, passwords, latched outputs
- `mqtt.htm` — MQTT broker and per-relay topics
- `ping.htm` — switch a relay when pings to a host are lost

## Documentation

See [docs/INDEX.md](docs/INDEX.md). Vendor datasheet:
<https://www.robot-electronics.co.uk/files/eth008b.pdf>
