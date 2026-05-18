# Known issues & footguns

Compressed catalogue of "things that bit us". Skim before debugging
anything weird.

## Protocol / WebSocket

- **One pending reply at a time.** The firmware only releases the last
  reply when the *next* command arrives. Always use `Scope._exchange()`.
- **Cross-session reply leakage.** Frames from the previous client
  survive in the queue across reconnects. `Scope.open()` drains.
- **Empty / `"1"` ack does NOT prove a command ran.** The `*OPC?` dummy
  bleeds through. Always re-query.
- **Plain-text `"deadline has elapsed"`** = unsupported / dropped /
  timed out. Not JSON. Catch as a string.
- **Chinese strings**: `"操作成功"` = success ack from `mouse_event` /
  `web_indicator`. `"不支持的命令: <name>"` = unsupported.
- **`get_dev_info` with omitted `data`** crashes the server-side
  WebSocket. Always include `data` (empty string is fine).
- **One client at a time.** Browser UI competes — close it.

## SCPI

- **Channel arg is `C<n>`**, not `CHAN<n>` / `:CHANNEL<n>`.
- **`:CHAN<n>:DISP`** silently ignored. Use `channel_set()`
  (touchscreen + verify via badge colour).
- **`:ACQ:TYPE AVER`/`HRES`** silently ignored.
- **`*SAV` / `*RCL`** silently acked, state not persisted.
- **Waveform export does not exist.** Verified by exhaustive SCPI
  probe + JS-bundle string extraction.
- **Many query forms return `~1e-38` garbage** instead of error. e.g.
  `:MEAS:FREQ?` with no signal. Filter aggressively.
- **`:CURS:MODE?` always returns `"X"`** regardless of actual mode.
- **`:TRIG:EDGE:HOLDOFF`** write times out; the query works.
- **`:TRIG:EDGE:NREJ`** write works; the query times out.

## UI / dialogs

- **Measure dialog X at `(664, 68)` is a NO-OP.** Cursor dialog X at
  `(665, 68)` (one pixel right) works. Trigger X at `(755, 68)` works.
  Math X at `(684, 68)` works. Don't confuse Measure for the others.
- **Dialog REMEMBERS its last tab** across opens. Always tap the
  desired sub-tab.
- **Math dialog left open absorbs all touches silently.** `measure()`
  auto-dismisses; other paths may need to do the same.
- **Source A/B dropdown settle ≥ 0.7 s.** 0.4 s drops the CH4 entry.
- **Bottom-bar Trigger button is a DIALOG SELECTOR**, not a Measure
  sub-tab. There is no "trigger" Measure sub-tab.

## Pixel sampling

- **`BADGE_BOX` x0 must be ≥ 715.** The orange trigger-position arrow
  leaks saturated pixels into the CH3 row otherwise.
- **Use `(300, 68)` for any-dialog-open check.** Title text and X-close
  glyphs avoided.

## OCR

- `Vpp:***` (literal asterisks) means scope couldn't compute — parse as
  `value=None`. Usually a trigger problem.
- Channel-coloured text on dark BG: collapse `max(R,G,B)` then
  threshold + invert before Tesseract.
- `VALUE_RE` / `NOVAL_RE` need to accept `Name(3-4):` form for
  two-source measurements.

## Tooling

- **`replace_string_in_file` once silently truncated `scopectl.py`**
  from ~260 lines to 121. Run `wc -l` after large edits as a sanity
  check.
- **Image-budget caps** — view at most a couple of PNGs per response;
  sample pixels with PIL for batch checks.
