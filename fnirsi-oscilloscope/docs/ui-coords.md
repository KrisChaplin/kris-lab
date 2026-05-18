# UI coordinates & dialog detection

Screen is 800 × 480. All coordinates are `(x, y)` in screen pixels.

## Top-bar buttons (y=30)

| Label | (x, y) | Source |
|-------|--------|--------|
| `trig_button` | (453, 30) | opens Trigger dialog |
| `cursor_button` | (553, 30) | opens Cursor Measurement dialog |
| `measure_button` | (614, 30) | opens Measure dialog (toggle) |
| `runstop_button` | (740, 30) | Run/Stop |

Open `clickmap.json` for the persisted set; run `python clickmap.py` to
add or recalibrate.

## Right-side channel toggle column (x=760)

| Channel | y |
|---------|---|
| CH1 | 145 |
| CH2 | 210 |
| CH3 | 275 |
| CH4 | 340 |

Pitch is 65 px. Earlier values (295/370) miss CH3/CH4.

## Channel badge colours (RGB, calibrated 2026-05-14)

| Channel | (R, G, B) | Notes |
|---------|-----------|-------|
| CH1 yellow | (200, 172, 17) | |
| CH2 cyan | (30, 120, 201) | |
| CH3 green | (49, 223, 90) | |
| CH4 magenta | (222, 52, 189) | |

`channel_state.BADGE_BOX` must use `x0 ≥ 715` — the orange
trigger-position arrow on the right of the waveform area leaks
saturated pixels into the CH3 row otherwise.

## Dialog detection

Any modal dialog paints the y=68 title bar a **uniform mid-grey
(66, 65, 66)**. The waveform background underneath is much darker
(~(33, 32, 33)).

```python
def any_dialog_open(im):
    r, g, b = im.getpixel((300, 68))[:3]
    return 50 < r < 90 and 50 < g < 90 and 50 < b < 90
```

Sample `x=300` because it sits clear of every dialog's title text (left)
and X-close glyph (right).

### Per-dialog discriminator (title-text bright-pixel range at y=68)

| Dialog | Bright at | Notes |
|--------|-----------|-------|
| Math | x=10–38 | Short title "Math" |
| Measure | x=40–80 | Title ends near x=80 |
| Cursor Measurement | x=90–130 | Only this dialog has bright pixels past x=100 |
| Trigger | (different layout — title at far left, less reliable) | |

Cursor-specific check:

```python
def cursor_dialog_open(im):
    if not any_dialog_open(im):
        return False
    return sum(1 for x in range(90, 130, 2)
               if sum(im.getpixel((x, 68))[:3]) > 300) >= 4
```

## Dialog close buttons

| Dialog | X coord | Status |
|--------|---------|--------|
| Trigger | (755, 68) | works |
| Math | (684, 68) | works |
| Cursor | (665, 68) | **works** |
| Measure | (664, 68) | **NO-OP** — must close via top-bar Measure toggle |

Two glyphs **one pixel apart** with opposite behaviour. Don't conflate.

## Cursor on-screen toggle (inside Cursor dialog)

Touch `(160, 113)` to toggle on/off. Read state from pixel `(150, 113)`:

| Pixel | State |
|-------|-------|
| (16, 134, 173) blue | ON |
| (140, 142, 140) grey | OFF |

## Measure dialog inner layout

- Sub-tabs at **y = 105**: Vertical / Horizontal / Others
- Bottom-bar buttons at **y = 428** are **dialog selectors** (switch
  between Measure / Math / Trigger / Cursor), NOT Measure sub-tabs.
- Source A / Source B dropdowns need **≥ 0.7 s** settle time; 0.4 s
  drops the CH4 entry.

## Trigger dialog inner layout

See [trigger.py](../trigger.py) — Type grid is 3 cols × 5 rows at
y=137,170,202,234,266 with column x=183,303,423. All 14 types
addressable; sub-panel parameter fields not yet mapped.

## Mapping new coordinates

```bash
python clickmap.py --gui     # matplotlib click-to-pick
python clickmap.py           # keyboard entry
```

For dialog-internal coords (not eligible for `click(label)`), hard-code
into the relevant `*ui.py` constants module.
