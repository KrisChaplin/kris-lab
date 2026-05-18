# WebSocket protocol

## Endpoints

| URL | Purpose |
|-----|---------|
| `ws://<ip>/ws_control` | JSON-framed control channel |
| `ws://<ip>/ws_image` | Binary RGB565 framebuffer |

Only **one client at a time**. If the browser UI is open, scripts get
kicked off.

## Request envelopes (`ws_control`)

All requests are JSON text frames:

```json
{"cmd": "scpi",          "data": "*IDN?"}
{"cmd": "mouse_event",   "data": "{\"event\":\"down\",\"x\":760,\"y\":220}"}
{"cmd": "mouse_event",   "data": "{\"event\":\"up\",\"x\":760,\"y\":220}"}
{"cmd": "get_dev_info",  "data": ""}
{"cmd": "web_indicator", "data": "on"}
```

The `data` field must always be present (even empty). Omitting it
crashes the server-side WebSocket.

## Reply envelope

```json
{
  "cmd": "scpi_control",
  "code": 0,
  "data": "FNIRSI,DPOF1204-200,…",
  "msgId": 42,
  "ts": 1747234567000,
  "type": "response",
  "version": 1
}
```

The reply `cmd` field identifies the opcode that generated it.

## Critical rules

1. **One pending reply at a time.** The firmware emits the *previous*
   command's reply only when the *next* command arrives. `_exchange()`
   pairs every real command with a dummy `get_dev_info` and matches
   replies by `cmd`.
2. **Cross-session leakage.** A fresh connection may still receive
   frames from the last client's queue. `Scope.open()` drains them.
3. **`msgId` is firmware-wide monotonic**, not per session.
4. **Write acks are empty frames.** Zero-length text frame =
   `Reply(ok=True, data="", code=0)`.
5. **Plain-text error**: `"deadline has elapsed"` means
   unsupported / dropped / timed out. Not JSON.
6. **Chinese error**: `"不支持的命令: <name>"` = "unsupported command".
7. **Chinese ack**: `"操作成功"` = "operation succeeded". Returned by
   `mouse_event` and `web_indicator`.
8. **Mouse events**: `clicked` alone is inert. Always send `down` then
   `up` with the same `(x,y)`.
9. **Empty/`"1"` acks don't prove anything happened.** Always
   round-trip a setter with its query.

## `/ws_image`

```python
ws.send(json.dumps({"cmd": "getImage", "data": ""}))
frame = ws.recv()                # bytes, len == 800*480*2 == 768000
```

- Row-major, little-endian RGB565, top-left origin.
- The browser polls every ~70 ms. `screen.capture(host)` grabs one.

## Non-SCPI opcode summary

| Opcode | Data | Reply |
|--------|------|-------|
| `get_dev_info` | `""` | JSON dict (model, sn, mac, lang, visa_tcp, visa_usb, …) |
| `get_lan_config` | `""` | JSON LAN config |
| `get_wired_config` | `""` | JSON wired config |
| `set_lan_config` | JSON config | ack |
| `web_indicator` | `"on"`/`"off"`/`"1"`/`"0"` | `"操作成功"` |
| `mouse_event` | `'{"event":"down\|up","x":X,"y":Y}'` | `"操作成功"` |
| `device_ota` | binary | (untested) |
| `getImage` *(on `/ws_image` only)* | `""` | 768 000 byte RGB565 frame |

`get_dev_info` exposes `visa_tcp` and `visa_usb` fields but the port
number itself is masked (`"***"`) and firewalled. The library cannot
reach raw VISA.
