#!/usr/bin/env python3
"""Detect channel display state from a scope screenshot.

The right-side channel badges on the DPO-F1204 show each channel's signature
colour when the channel is active, and a desaturated grey when it is not.
We detect by sampling pixels inside each badge and looking for the channel's
hue with high saturation.

Channel signature colours (R, G, B) calibrated 2026-05-14:
    CH1 yellow   (200, 172,  17)
    CH2 cyan     ( 30, 120, 201)
    CH3 green    ( 49, 223,  90)
    CH4 magenta  (222,  52, 189)

Usage:
    python3 channel_state.py screen.png
"""
from __future__ import annotations
import sys
from PIL import Image

# Bounding boxes (x0,y0,x1,y1) for each channel badge in 800x480 frame.
# x0 must be >=715 to avoid the trigger position arrow at the right edge
# of the waveform area (it leaks orange pixels into the CH3 row).
BADGE_BOX = {
    1: (715, 120, 795, 175),
    2: (715, 185, 795, 235),
    3: (715, 250, 795, 300),
    4: (715, 315, 795, 365),
}

# Hue signatures (R, G, B). Calibrated from `badges_ch34_on.png` and `pre.png`.
SIGNATURE = {
    1: (200, 172,  17),  # yellow
    2: ( 30, 120, 201),  # cyan
    3: ( 49, 223,  90),  # green
    4: (222,  52, 189),  # magenta
}


def _saturation(rgb):
    r, g, b = rgb[:3]
    return max(r, g, b) - min(r, g, b)


def _close(a, b, tol=70):
    return all(abs(int(x) - int(y)) <= tol for x, y in zip(a, b))


def detect(image_path: str) -> dict[int, bool]:
    im = Image.open(image_path).convert("RGB")
    out = {}
    for ch, box in BADGE_BOX.items():
        sig = SIGNATURE[ch]
        x0, y0, x1, y1 = box
        active = False
        for y in range(y0, y1, 3):
            for x in range(x0, x1, 3):
                px = im.getpixel((x, y))
                if _saturation(px) > 60 and _close(px, sig):
                    active = True
                    break
            if active:
                break
        out[ch] = active
    return out


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "screen.png"
    state = detect(path)
    for ch in sorted(state):
        print(f"CH{ch}: {'ON ' if state[ch] else 'off'}")
