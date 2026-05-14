"""Probe the non-SCPI ws_control opcodes (discovered from the firmware JS bundle)."""
import json
import os
import time
import websocket

URL = os.environ.get("FNIRSI_URL", "ws://192.168.0.75/ws_control")

OPCODES = [
    ("get_dev_info",     ""),
    ("get_dev_info",     "{}"),
    ("get_dev_info",     None),       # omit data
    ("get_lan_config",   ""),
    ("get_lan_config",   None),
    ("get_wired_config", ""),
    ("get_wired_config", None),
    ("web_indicator",    ""),
    ("web_indicator",    "on"),
    ("web_indicator",    "off"),
    ("web_indicator",    "1"),
    ("web_indicator",    "0"),
    ("web_indicator",    {"state": 1}),
    ("getImage",         ""),         # already known to work on /ws_image
    ("get_screen_info",  ""),
    ("get_device_status",""),
    ("get_trigger_status",""),
    ("get_waveform",     ""),
    ("get_waveform",     "C1"),
    ("get_channel_data", ""),
    ("ping",             ""),
    ("heartbeat",        ""),
    ("keep_alive",       ""),
    ("get_version",      ""),
    ("get_capabilities", ""),
]

def probe(ws, msg_id, cmd, data):
    obj = {"cmd": cmd}
    if data is not None:
        obj["data"] = data
    obj["msgId"] = msg_id
    raw = json.dumps(obj)
    ws.send(raw)
    try:
        rsp = ws.recv()
    except websocket.WebSocketTimeoutException:
        return ("TOUT", None)
    if isinstance(rsp, bytes):
        return ("BIN", f"{len(rsp)} bytes")
    try:
        j = json.loads(rsp)
        return ("JSON", j)
    except Exception:
        return ("TEXT", rsp)

ws = None
msg_id = 1
def connect():
    return websocket.create_connection(URL, timeout=3.0)

for cmd, data in OPCODES:
    if ws is None:
        ws = connect()
    try:
        kind, val = probe(ws, msg_id, cmd, data)
    except websocket.WebSocketConnectionClosedException:
        kind, val = ("CLOSE", "server hung up")
        try: ws.close()
        except Exception: pass
        ws = None
    label = f"{cmd}({data!r})" if data is not None else f"{cmd}(<no data>)"
    print(f"  {kind:5s} {label:50s} -> {val}")
    msg_id += 1
    time.sleep(0.1)
if ws is not None:
    ws.close()
