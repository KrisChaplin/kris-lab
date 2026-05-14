#!/usr/bin/env python3
"""Quick probe of FNIRSI DPO-F1204 /ws_control SCPI WebSocket.

Sends a list of likely SCPI queries and prints responses.
Override scope URL with the FNIRSI_URL environment variable.
"""
import os
import sys
import json
import time
import websocket

URL = os.environ.get("FNIRSI_URL", "ws://192.168.0.75/ws_control")

QUERIES = [
    "*IDN?",
    "*OPC?",
    "SYST:VERS?",
    "SYST:ERR?",
    ":CHAN2:DISP?",
    ":CHAN2:SCAL?",
    ":CHAN2:OFFS?",
    ":CHAN2:COUP?",
    ":TIM:SCAL?",
    ":TIM:OFFS?",
    ":TRIG:STAT?",
    ":TRIG:EDGE:SOUR?",
    ":TRIG:EDGE:LEV?",
    ":ACQ:STAT?",
    ":MEAS:FREQ? CHAN2",
    ":MEAS:VPP? CHAN2",
    ":MEAS:VAMP? CHAN2",
    ":MEAS:VMAX? CHAN2",
    ":MEAS:VMIN? CHAN2",
    ":MEAS:PER? CHAN2",
    ":WAV:SOUR?",
    ":WAV:FORM?",
    ":WAV:POIN?",
    ":WAV:PRE?",
]

def main():
    ws = websocket.WebSocket()
    ws.settimeout(2.0)
    ws.connect(URL)
    print(f"connected to {URL}", file=sys.stderr)
    # First, fetch device info via dedicated command
    try:
        ws.send(json.dumps({"cmd": "get_dev_info"}))
        print("dev_info ->", ws.recv())
    except Exception as e:
        print(f"dev_info err: {e}")

    for q in QUERIES:
        msg = json.dumps({"cmd": "scpi", "data": q})
        try:
            ws.send(msg)
        except Exception as e:
            print(f"SEND-ERR {q!r}: {e}")
            continue
        time.sleep(0.05)
        try:
            resp = ws.recv()
        except websocket.WebSocketTimeoutException:
            resp = "<timeout>"
        except Exception as e:
            resp = f"<err:{e}>"
        print(f"{q:30s} -> {resp!r}")
    ws.close()

if __name__ == "__main__":
    main()
