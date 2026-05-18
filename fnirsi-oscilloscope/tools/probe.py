#!/usr/bin/env python3
"""Generalized SCPI/opcode probe for the DPO-F1204.

Reads commands from stdin (one per line) and reports each result classified
into:
  OK    - JSON reply with code=0 and data populated
  ACK   - JSON reply with code=0 and empty data (typical for SCPI writes)
  ERR   - JSON reply with code!=0
  TEXT  - non-JSON text reply (e.g. 'deadline has elapsed', '操作成功')
  TOUT  - timeout
  EXC   - other exception

A non-SCPI envelope can be tested by prefixing the line with '@' and a JSON
object, e.g.:
    @{"cmd":"get_dev_info","data":""}
"""
from __future__ import annotations
import json
import sys
import time
import argparse
import websocket


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="192.168.0.75")
    p.add_argument("--timeout", type=float, default=2.5)
    p.add_argument("--delay", type=float, default=0.08,
                   help="seconds between commands")
    p.add_argument("--file", help="read commands from file (default: stdin)")
    args = p.parse_args()

    src = open(args.file) if args.file else sys.stdin

    ws = websocket.WebSocket()
    ws.settimeout(args.timeout)
    ws.connect(f"ws://{args.host}/ws_control",
               origin=f"http://{args.host}")

    last_seen_msg_id = -1
    for line in src:
        cmd = line.strip()
        if not cmd or cmd.startswith("#"):
            continue
        if cmd.startswith("@"):
            try:
                envelope = json.loads(cmd[1:])
            except Exception as e:
                print(f"  BAD-JSON {cmd!r}: {e}")
                continue
            label = json.dumps(envelope)
        else:
            envelope = {"cmd": "scpi", "data": cmd}
            label = cmd

        try:
            ws.send(json.dumps(envelope))
        except Exception as e:
            print(f"{label[:60]:60s} SEND-EXC {e}")
            ws.close(); ws = websocket.WebSocket(); ws.settimeout(args.timeout)
            ws.connect(f"ws://{args.host}/ws_control",
                       origin=f"http://{args.host}")
            continue
        try:
            raw = ws.recv()
        except websocket.WebSocketTimeoutException:
            print(f"{label[:60]:60s} TOUT")
            continue
        except Exception as e:
            print(f"{label[:60]:60s} RECV-EXC {e}")
            continue
        if isinstance(raw, (bytes, bytearray)):
            kind = "BIN"
            data = f"<{len(raw)} bytes>"
            print(f"{label[:60]:60s} {kind}   {data}")
        else:
            stripped = raw.strip()
            try:
                j = json.loads(stripped) if stripped else None
            except json.JSONDecodeError:
                j = None
            if j is None:
                print(f"{label[:60]:60s} TEXT  {stripped!r}")
            else:
                code = j.get("code", -1)
                data = j.get("data", "")
                mid = j.get("msgId")
                if mid is not None and isinstance(mid, int):
                    if last_seen_msg_id != -1 and mid != last_seen_msg_id + 1:
                        skew = f" [SKEW: expected {last_seen_msg_id+1}, got {mid}]"
                    else:
                        skew = ""
                    last_seen_msg_id = mid
                else:
                    skew = ""
                if code == 0 and (data == "" or data is None):
                    print(f"{label[:60]:60s} ACK   msgId={mid}{skew}")
                elif code == 0:
                    short = data if len(str(data)) < 200 else str(data)[:200] + "..."
                    print(f"{label[:60]:60s} OK    msgId={mid}{skew} {short!r}")
                else:
                    print(f"{label[:60]:60s} ERR   msgId={mid}{skew} code={code} {data!r}")
        time.sleep(args.delay)

    ws.close()


if __name__ == "__main__":
    main()
