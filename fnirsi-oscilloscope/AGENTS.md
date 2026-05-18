# Agent Guide — FNIRSI Oscilloscope

> Instrument-specific entry point for AI coding agents. For the full lab
> overview, see [../AGENTS.md](../AGENTS.md).

## What this instrument is

Python control library and CLI for the **FNIRSI DPOF1204-200**
oscilloscope. Talks to the scope over two WebSockets exposed by its
embedded HTTP server. The firmware has partial SCPI support, so much of
the library drives the on-screen UI by tapping mapped touchscreen
coordinates and reading results via Tesseract OCR.

Default scope IP: `192.168.0.75`. Override per-call via `--host`.

## Read this first

Documentation is **partitioned by topic** in [docs/](docs/) so you can
load only the file relevant to a task. Always start at
[docs/INDEX.md](docs/INDEX.md). Each topic file is small (typically
<200 lines).

## Conventions for agents working here

1. **Do not auto-commit.** Local edits only; the human tests and
   commits.
2. **One WebSocket client at a time.** If the browser UI is open on the
   scope, scripts will be kicked off. Close the browser before running.
3. **The firmware buffers ONE pending SCPI reply** — releases it on the
   next command. `Scope._exchange()` already handles this by sending a
   dummy `get_dev_info` after each real command. Do not call `ws.send`
   directly; always go through `Scope`.
4. **Many SCPI commands return `"deadline has elapsed"`.** See
   [docs/scpi.md](docs/scpi.md) for the full list of working vs. broken
   commands before adding a new one.
5. **No waveform binary export exists.** Verified by exhaustive SCPI
   probe + JS-bundle string extraction (only 7 `ws_control` opcodes
   total). Don't waste time looking — OCR or screen-capture the readouts.
6. **Touchscreen requires a `down`+`up` pair.** `Scope.touch(x, y)`
   already does both. A `clicked` event alone is acked but does nothing.
7. **Dialog detection** uses pixel sampling on the y=68 title strip. See
   [docs/ui-coords.md](docs/ui-coords.md#dialog-detection) for the
   universal "any-dialog-open" check and per-dialog discriminators.
8. **Image-budget rule:** when inspecting many screenshots, sample
   pixels programmatically with PIL rather than viewing each PNG — agent
   tooling typically caps image views per response.

## High-level architecture

```
                    ┌──────────────────┐
   user  ─►  scopectl.py  ──► Scope (scope.py)
                                │
        ┌───────────────────────┼──────────────────────┐
        ▼                       ▼                      ▼
  send_scpi()             touch(x,y)            screen.capture()
        │                       │                      │
        ▼                       ▼                      ▼
   ws_control              ws_control             ws_image
   (cmd=scpi)              (cmd=mouse_event)      (cmd=getImage)
        │                       │                      │
        ▼                       ▼                      ▼
                       FNIRSI DPOF1204-200
```

Dialog-driven flows (`measure`, `cursor`, `math`, `trig-ui`):

```
   open dialog (touch top-bar button)
   → sample y=68 title strip to confirm correct dialog is on top
   → tap option / dropdown coords from measure.py / trigger.py / mathui.py
   → crop readout strip → PIL → tesseract → regex parse
   → close dialog (per-dialog X coord OR re-tap top-bar toggle)
```

## Tasks you might be asked to do

| Task | Where to look |
|------|--------------|
| Add a new SCPI command | [docs/scpi.md](docs/scpi.md) (check it isn't broken first), then `Scope` method in [scope.py](scope.py), then CLI flag in [scopectl.py](scopectl.py) |
| Map a new touchscreen coord | [clickmap.py](clickmap.py) + `clickmap.json` or hard-coded in `*ui.py` |
| Parse a new on-screen readout | [measure.py](measure.py) for regex; [docs/measurements.md](docs/measurements.md) for OCR gotchas |
| Map a new dialog | [docs/ui-coords.md](docs/ui-coords.md) for dialog detector pattern |
| Add advanced trigger sub-panel | [trigger.py](trigger.py) + [docs/triggers.md](docs/triggers.md) |

## Known footguns (compressed)

- Measure dialog X at `(664,68)` is a **no-op**. Close via the top-bar
  Measure toggle. Cursor dialog X at `(665,68)` (one pixel right) **works**.
- Math dialog left open will absorb all touches silently — `measure()`
  now auto-dismisses it.
- Source A/B dropdown needs ≥0.7 s settle (0.4 s drops CH4).
- `:CURS:MODE?` always returns `"X"`. Trust the write.
- `:TRIG:EDGE:NREJ` is write-only on this firmware.
- `:TRIG:EDGE:HOLDOFF?` reads but the write times out.
- `replace_string_in_file` has, on at least one occasion, silently
  truncated `scopectl.py` to ~half. `wc -l` after large edits.

## Memory hint

If your agent supports persistent memory, mirror the contents of
[docs/known-issues.md](docs/known-issues.md) and [docs/scpi.md](docs/scpi.md)
into it — both compress poorly and are referenced constantly.
