# SCPI dialect (V1.0.1.26020603)

Hybrid Rigol / SCPI-99. **Channel argument is `C1`/`C2`/`C3`/`C4`**, NOT
`CHAN1`.

## ✅ Works reliably (read+write unless noted)

| Command | Effect |
|---------|--------|
| `*IDN?`, `*OPC?`, `SYST:VERS?`, `SYST:ERR?` | Identification + status |
| `:SYST:LANG?` | Returns `"SCHinese"` |
| `:CHAN<n>:SCAL <V/div>` | Vertical scale |
| `:CHAN<n>:OFFS <V>` | Vertical offset |
| `:CHAN<n>:PROB <ratio>` | Probe ratio |
| `:CHAN<n>:COUP DC\|AC\|GND` | Coupling |
| `:CHAN<n>:BWL?`, `:CHAN<n>:INV?`, `:CHAN<n>:UNIT?`, `:CHAN<n>:LAB?` | Query-only |
| `:TIM:SCAL <s/div>` | Timebase |
| `:TRIG:EDGE:SOUR C<n>` | Trigger source |
| `:TRIG:EDGE:LEV <V>` | Trigger level |
| `:TRIG:EDGE:SLOP RIS\|FALL\|ALT` | Edge slope |
| `:TRIG:EDGE:COUP AC\|DC` | Edge coupling (added 2026-05-14) |
| `:TRIG:EDGE:HOLDOFF?` | Holdoff read **only** (write times out — use touch dialog) |
| `:ACQ:TYPE NORM\|PEAK` | Acquisition type (other values silently ignored) |
| `:ACQ:MODE?` | Returns `"YT"` |
| `:ACQ:SRAT?` | Sample rate, e.g. `"5.00E+08"` |
| `:ACQ:MDEP?` | Memory depth, e.g. `"7M"` |
| `:RUN` / `:STOP` / `:SING` / `:AUT` | Acquisition control |
| `:TRIG:STAT?` | `RUN`/`STOP`/`AUTO`/`WAIT`/`TD` |
| `:TRIG:MODE?` | Sweep mode (`AUTO`/`NORM`), **not** trigger type |
| `:CURS:SOUR? <n>` | Cursor source channel |
| `:CURS:X1?`, `:CURS:X2?`, `:CURS:Y1?`, `:CURS:Y2?` | Cursor positions |
| `:CURS:XDEL?`, `:CURS:YDEL?` | Cursor deltas |

## ✏️ Write-only

| Command | Notes |
|---------|-------|
| `:TRIG:EDGE:NREJ ON\|OFF` | Query times out; write accepted |
| `:CURS:MODE OFF\|X\|Y\|XY` | Query always returns `"X"` |

## ❌ Broken — use UI passthrough or skip

- **Waveform readback** — `:WAV:*`, `:DATA?`, `:FETC?`, Siglent
  `C<n>:WF?`. All return empty or "deadline has elapsed". **There is no
  workaround**: confirmed by exhaustive SCPI probe + JS bundle string
  extraction. Only seven `ws_control` opcodes exist; none expose
  waveform data.
- **Measurement queries** — `:MEAS:VPP?`, `:MEAS:VRMS?`, `:MEAS:PER?`,
  etc. → `"deadline has elapsed"`. `:MEAS:FREQ?` returns garbage
  `~1e-38`. Drive Measure dialog + OCR instead
  ([measurements.md](measurements.md)).
- **Math / FFT / Cursor SCPI** — `:MATH:*`, `:FFT:*`, most `:CURS:*`
  control. Drive via touch ([math-fft.md](math-fft.md)).
- **Advanced trigger types** — `:TRIG:MODE PULS/SLOP/VID/PATT/RUNT/...`.
  Writes silently accepted, device stays in edge mode. Use
  `trigger_ui()` ([triggers.md](triggers.md)).
- **`*SAV` / `*RCL`** — silently acked, state not persisted.
- **`:CHAN<n>:DISP ON|OFF`** — silently ignored. Use
  `Scope.channel_set()` (touchscreen + verify).
- **`:CHAN<n>:DISP?`** — not implemented.
- **`:ACQ:AVER`, `:ACQ:TYPE AVER`, `:ACQ:TYPE HRES`** — silently
  ignored.
- **`:DISP:DATA?`, `:HCOP:SDUM?`, `:STOR:*`, `:MMEM:*`, `:SYST:TIME?`,
  `:SYST:DATE?`** — all broken.
- **`*ESR?`, `*STB?`, `*TST?`** — silent.
- **Siglent dialect** (`C2:PAVA?`, `TDIV?`, `TRSE?`, etc.) — all time
  out.

## Adding new SCPI commands — checklist

1. **Query first.** If `:NEW:CMD?` times out or returns junk, skip — it
   is broken on this firmware.
2. **Write then re-query.** If write is acked but query doesn't reflect
   the value, it is silently ignored — skip or use UI passthrough.
3. **Use `Scope._exchange()`** — never call `ws.send` directly.
4. **Document outcome here** under ✅/✏️/❌.

## Notes

- Use `tools/scpi_survey.py` as a starting point when probing new
  commands.
- Plain-text `"deadline has elapsed"` is the firmware's universal "I
  don't support this" reply. It is **not JSON**.
