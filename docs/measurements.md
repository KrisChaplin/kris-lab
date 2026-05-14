# Measurements (Measure dialog + OCR)

All measurements rely on the Measure dialog because `:MEAS:*?` SCPI is
broken on this firmware (see [scpi.md](scpi.md)).

## CLI

```bash
python scopectl.py measure 3 Vpp Max Min                 # vertical (default tab)
python scopectl.py measure 3 Freq Cycle --tab horizontal
python scopectl.py measure 3 Phase SKEW --tab others --ch-b 4
```

Output rows are `{name, value, unit, raw}` dicts. `value=None` means the
scope is showing `***` (typically unstable trigger).

## Workflow

1. `Scope.measure(ch, kinds, tab=...)`:
   - Detects any open dialog by sampling `(300, 68)`.
   - If Math is on top — taps Math X at `(684, 68)` to dismiss.
   - If Measure is **not** on top — taps top-bar Measure button.
   - Taps the desired sub-tab (always — sticky-tab gotcha).
   - For each `kind`, taps the corresponding tile coord from
     [measure.py](../measure.py).
   - Screenshots the readout strip, crops, runs Tesseract.
   - Parses with `VALUE_RE` / `NOVAL_RE` regexes.
   - Closes Measure by re-tapping the top-bar Measure toggle (up to 3
     retries verified by pixel probe).
2. Closes any dropdown / dialog state.

## Gotchas

- **Dialog REMEMBERS its last tab.** Always tap the desired sub-tab,
  every time.
- **Header X at (664, 68) is a no-op.** Use the top-bar toggle.
- **Math dialog absorbs touches** if left foregrounded — auto-dismissed.
- **Source A/B dropdown settle** must be ≥ 0.7 s.
- **No "trigger" sub-tab in Measure.** The bottom-bar Trigger button is
  a dialog selector — it opens the full Trigger settings dialog.

## OCR parsing

Regexes live in [measure.py](../measure.py):

| Regex | Matches |
|-------|---------|
| `VALUE_RE` | `Vpp:440.00mV`, `Phase(3-4):12.3°` — name group accepts paren suffix |
| `NOVAL_RE` | `Vpp:***`, `Phase(3-4):***` — same name shape |
| `UNIT_RE` | SI prefixes + `s`, `V`, `Hz`, `%`, `°`, `deg` |

Colour-on-dark text is collapsed to greyscale via `max(R, G, B)`,
threshold + invert before passing to Tesseract.

## FFT peak shortcut

`Scope.fft_peak()` skips the Measure dialog entirely:

```bash
python scopectl.py fft-peak
# → FFT peak: 999.991 Hz
```

It crops the top-right area `(700, 68, 800, 125)` and OCRs the cursor
frequency. The regex tolerates OCR newline / punctuation noise between
the number and the `Hz` unit via a `[^A-Za-z0-9]*` gap allowance.

## Validated coverage

- CH1 / CH2 / CH3 / CH4 — vertical (Vpp, Max, Min, Mean, etc.)
- CH1–CH4 — horizontal (Freq, Cycle, Period, Duty, etc.)
- `others` tab (two-source) — `Phase(3-4)`, `SKEW(3-4)` with `--ch-b 4`
