# ETH008-B Hardware

## Power

- 12 V DC via a 2.1 mm barrel jack, **positive core**.
- Regulated or unregulated supply is acceptable.
- The relay coils are driven from this same 12 V rail, so the supply must
  cope with all eight coils energised at once.
- Measured on the lab board: 11.9 V (`0x78` returns `119`).

## Relays

Eight SPDT volt-free contacts. Each channel brings out:

| Terminal | Meaning |
|----------|---------|
| `NC` | Normally connected — closed to `C` when the relay is **de-energised** |
| `C` | Common |
| `NO` | Normally open — closed to `C` when the relay is **energised** |

"Active" in the command set means the coil is energised, i.e. `C`–`NO`
closed and `C`–`NC` open.

The contacts are volt-free: the board does not source any voltage onto
them. Whatever you switch must be powered externally.

### Contact ratings

| Load type | Typical application | Rating |
|-----------|--------------------|--------|
| AC1 | Non-inductive or slightly inductive | 16 A @ 250 V AC |
| AC15 | Electromagnetic load (>72 VA) | 3 A @ 120 V AC, 1.5 A @ 240 V AC |
| AC3 | Motor control | 750 W |
| DC1 | Non-inductive or slightly inductive | 16 A @ 24 V DC |
| DC13 | Electromagnetic load | 0.22 A @ 120 V DC, 0.1 A @ 250 V DC |

Relay part is a Hongfa HF115FD. Exceeding these regions shortens contact
life significantly.

### Switching rate

Mechanical contacts have a finite life, and the loads on this bench board
are live equipment. **Do not switch faster than 3 Hz.** `relayctl.py`
enforces a 333 ms minimum between state changes.

## Inputs

The ETH008-B has **no digital or analogue inputs**. Commands `0x25` (get
inputs) and `0x30` (analogue) return no data. Any code that reads inputs
from this board is wrong — it will simply time out.

## Connectors and controls

- RJ45 Ethernet, 10/100.
- 2.1 mm DC jack.
- A two-position jumper block read at power-up:
  - **left pair** — normal run
  - **right pair** — factory reset

Factory reset clears the network and authentication settings, so the board
reverts to DHCP with a 192.168.0.200 fallback. Do not do this without
asking — the board's address is referenced by other lab tooling.

## Addressing

With a DHCP server the board takes a leased address. Without one it falls
back to a fixed `192.168.0.200` / `255.255.255.0`. The lab board is on
DHCP and currently holds `192.168.0.200`, hostname `ETH008`, MAC
`44:b7:d0:a5:79:e2`.

Devantech supply a "Module Finder" application that scans the local
network for their modules if the address is ever lost.
