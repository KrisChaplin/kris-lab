# Cursors

## CLI

```bash
python scopectl.py cursor --src 3 --mode X \
    --x1 -5e-4 --x2 5e-4 --show
python scopectl.py cursor --hide
python scopectl.py cursor                          # read current state
python scopectl.py cursor --json
```

`--mode` is one of `OFF | X | Y | XY`. Time positions are seconds;
voltage positions are volts.

## What SCPI works

| Command | Status |
|---------|--------|
| `:CURS:SOUR?` / write | ✅ |
| `:CURS:X1?`, `X2?`, `Y1?`, `Y2?` (read+write) | ✅ |
| `:CURS:XDEL?`, `:CURS:YDEL?` | ✅ (read-only — computed) |
| `:CURS:MODE OFF\|X\|Y\|XY` write | ✏️ Write-only; query always returns `"X"` |
| `:CURS:STAT?` | ❌ Returns `"?"` |

Because the mode and state queries are broken, the library:
- **Trusts** the mode write (records `None` if user didn't set it).
- **Reads display state from a pixel** at `(150, 113)` — see below.

## On-screen display toggle

The SCPI `:CURS:*` calls set the mathematical positions but don't enable
the on-screen cursor markers. To toggle the markers we tap the toggle
pill inside the Cursor Measurement dialog.

| What | Where |
|------|-------|
| Toggle tap point | `(160, 113)` |
| State sample pixel | `(150, 113)` |
| ON colour | `(16, 134, 173)` blue |
| OFF colour | `(140, 142, 140)` grey |

`Scope.cursor_show(on, close_dialog=True)`:

1. Snapshot the screen.
2. Detect whether the Cursor dialog is currently foregrounded
   (`any_dialog_open` + bright pixels at x=90–130, y=68).
3. If not open, tap `cursor_button (553, 30)` to open it.
4. Sample `(150, 113)` to read current state.
5. Tap `(160, 113)` only if a state flip is needed.
6. If `close_dialog`, tap the dialog X at **`(665, 68)`** (which
   **does** work on this dialog — see [ui-coords.md](ui-coords.md)).

## Δt → frequency convenience

The CLI prints `Δt` plus `1/Δt` in Hz for the X cursors. Useful for
quick period → frequency sanity checks.

## State save/load

`Scope.cursor_state()` returns a dict suitable for inclusion in the full
`state_dump` round-trip. End-to-end save/load round-trip with cursors
is **not yet** verified — open TODO.
