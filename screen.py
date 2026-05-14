#!/usr/bin/env python3
"""Capture the DPOF1204 screen as a PNG.

The scope serves an 800x480 RGB565 framebuffer on the ws://<ip>/ws_image
WebSocket. The client polls by sending {"cmd":"getImage","data":""} and the
server responds with a single 800*480*2 = 768000-byte binary frame.

Usage: python3 screen.py [out.png]
Requires Pillow (`pip install pillow`).
"""
import json
import struct
import sys
import time
import websocket

WIDTH, HEIGHT = 800, 480
EXPECTED_BYTES = WIDTH * HEIGHT * 2


def capture(host: str = "192.168.0.75", timeout: float = 5.0) -> bytes:
    ws = websocket.WebSocket()
    ws.settimeout(timeout)
    ws.connect(f"ws://{host}/ws_image", origin=f"http://{host}")
    try:
        ws.send(json.dumps({"cmd": "getImage", "data": ""}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            frame = ws.recv()
            if isinstance(frame, (bytes, bytearray)) and len(frame) == EXPECTED_BYTES:
                return bytes(frame)
            # ignore stray text or short frames
        raise RuntimeError("no full frame received within timeout")
    finally:
        ws.close()


def rgb565_to_rgb888(raw: bytes) -> bytes:
    """Convert little-endian RGB565 buffer to packed RGB888."""
    out = bytearray(len(raw) // 2 * 3)
    # Vectorise with struct + bit math; fast enough for 768 kB.
    pixels = struct.unpack(f"<{len(raw)//2}H", raw)
    j = 0
    for px in pixels:
        r = (px >> 11) & 0x1F
        g = (px >> 5) & 0x3F
        b = px & 0x1F
        out[j] = (r << 3) | (r >> 2)
        out[j + 1] = (g << 2) | (g >> 4)
        out[j + 2] = (b << 3) | (b >> 2)
        j += 3
    return bytes(out)


def save_png(raw: bytes, path: str) -> None:
    from PIL import Image
    rgb = rgb565_to_rgb888(raw)
    img = Image.frombytes("RGB", (WIDTH, HEIGHT), rgb)
    img.save(path)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "screen.png"
    raw = capture()
    save_png(raw, out)
    print(f"saved {out} ({WIDTH}x{HEIGHT}, {len(raw)} bytes RGB565)")


if __name__ == "__main__":
    main()
