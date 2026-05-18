# Math / FFT

All Math features are UI-driven — `:MATH:*` and `:FFT:*` SCPI return
"deadline has elapsed".

## CLI

```bash
python scopectl.py math --operator FFT --source 3 --on
python scopectl.py math --operator '+' --source 1 --source-b 2 --on
python scopectl.py math --off
python scopectl.py fft-peak                  # OCR top-right peak readout
```

`Scope.math_ui()` opens the Math dialog (top-bar `M`), selects the
operator, sets sources A (and optionally B), toggles display on/off, and
closes. Coordinates live in [mathui.py](../mathui.py).

## Operators

```
+   -   *   /
FFT   d/dt   intdt   sqrt
```

## FFT specifics

- `fft_unit` — `dBVrms` / `dBV` / `Vrms` (touch dropdown).
- `fft_display` — `Split` / `Full`.
- `auto_setup` — taps the dialog's Auto button.

## Reading the FFT peak (OCR)

`Scope.fft_peak()` crops `(700, 68, 800, 125)` from a screenshot —
that's where the firmware draws the peak-cursor frequency readout in
FFT mode — and runs Tesseract.

The regex tolerates OCR noise between digits and the `Hz` unit
(newline / punctuation gap allowance) because Tesseract often splits
the readout across two lines.

## Gotchas

- **Math dialog left open will absorb all subsequent touches**, silently
  acked. Always close it after use. `Scope.measure()` defends by
  detecting Math-on-top and dismissing via its X at `(684, 68)` — which
  works (unlike Measure's at `(664, 68)`).
- **Source A/B dropdown settle**: ≥ 0.7 s. Same gotcha as Measure.
