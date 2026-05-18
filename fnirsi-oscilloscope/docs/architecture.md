# Architecture

## Three transport layers, one device

All scope interaction goes through one of three logical channels, each
multiplexed onto the embedded HTTP server on TCP/80:

| Channel | URL | Direction | Payload |
|---------|-----|-----------|---------|
| HTTP UI | `http://<ip>/` | bidir | SPA static assets (Vue + lib chunks) |
| Control | `ws://<ip>/ws_control` | request/response | JSON-framed opcodes |
| Image | `ws://<ip>/ws_image` | request/binary | One RGB565 framebuffer per request |

## `ws_control` opcodes (complete list)

Discovered by string-extracting the JS bundle. There is **nothing else**:

| Opcode | Data | Purpose |
|--------|------|---------|
| `scpi` | SCPI string | Forward to the SCPI engine |
| `mouse_event` | `'{"event":"down\|up\|clicked","x":X,"y":Y}'` | Touchscreen passthrough |
| `get_dev_info` | `""` | Model / SN / MAC / VISA addresses |
| `get_lan_config` | `""` | LAN/IP config |
| `get_wired_config` | `""` | Wired ethernet config |
| `set_lan_config` | JSON | Persist LAN config |
| `device_ota` | bytes | OTA firmware update |
| `web_indicator` | `"on"` / `"off"` | Toggle the "remote" indicator on the scope's screen |

No waveform, no measurement, no math, no cursor opcodes. Those rely
purely on the on-screen UI driven via `mouse_event` + screenshot OCR.

## Layered Python design

```
   ┌─────────────────────────────────────┐
   │ scopectl.py    (argparse CLI)       │
   ├─────────────────────────────────────┤
   │ Scope          (scope.py)           │
   │   send_scpi    – paired exchange    │
   │   touch / click                     │
   │   channel_set, trigger_*, measure,  │
   │   cursor_*, math_ui, fft_peak       │
   ├─────────────────────────────────────┤
   │ screen.py            measure.py     │
   │ (RGB565 → PNG)       (coords + OCR) │
   │ trigger.py           mathui.py      │
   │ channel_state.py     clickmap.json  │
   └─────────────────────────────────────┘
```

`Scope` owns the WebSocket lifecycle and the protocol-level workarounds
(pending-reply pairing, stale-frame draining). Higher-level workflows
build on it but never own a socket.

## Key invariants

1. **Exactly one pending SCPI reply** lives in the firmware. The next
   command flushes it. `Scope._exchange()` exploits this by sending a
   real cmd + a `get_dev_info` dummy and matching the reply `cmd` field.
2. **Touchscreen events must be `down`+`up`.** A `clicked` event alone
   is acked but inert.
3. **Dialogs are modal.** Only one dialog is ever foreground. The y=68
   title strip is the universal "is a dialog open" probe — see
   [ui-coords.md](ui-coords.md#dialog-detection).
4. **Many SCPI writes silently succeed but do nothing.** Always
   round-trip a setter with its query when adding a new command. If the
   query is also broken, drive via touchscreen.

## CLI subcommand → method map

| Subcommand | Method |
|------------|--------|
| `state` / `save` / `load` | `state_dump` / `state_save` / `state_load` |
| `ch` | `channel_*` setters + `channel_set` |
| `tb` | `timebase` |
| `trig` | `trigger_*` (source/level/slope/coupling/nrej/holdoff) |
| `run` / `stop` / `single` / `auto` | `:RUN` / `:STOP` / `:SING` / `:AUT` |
| `acq` | `acq_type` |
| `screenshot` | `screen.capture` |
| `measure` | `Scope.measure(ch, kinds, tab=...)` |
| `cursor` | `cursor_*` setters + `cursor_show` |
| `math` | `math_ui` |
| `fft-peak` | `fft_peak` |
| `trig-ui` | `trigger_ui` |
| `click` | `click(label)` |
| `dev-info` / `indicator` | `dev_info` / `indicator` |
