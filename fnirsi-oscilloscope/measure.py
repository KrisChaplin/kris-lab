"""OCR-based measurement readback for the FNIRSI DPOF1204-200.

SCPI :MEAS:* commands are broken on this firmware (return 'deadline has elapsed'),
so we drive the touchscreen Measure dialog and OCR the on-screen readout strip.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from PIL import Image
import pytesseract

# Pixel coords (x, y) for each measurement button inside the Measure dialog.
# Tab: Vertical / Horizontal / Others. The Vertical tab is selected by default.
MEAS_TAB_VERTICAL = (85, 105)
MEAS_TAB_HORIZONTAL = (195, 105)
MEAS_TAB_OTHERS = (305, 105)

# Source A dropdown (closed) and its entries.
MEAS_SOURCE_A_DROPDOWN = (170, 195)
MEAS_SOURCE_B_DROPDOWN = (445, 195)  # Only present on the Others tab.
MEAS_SOURCE_CHANNELS = {
    1: (170, 224),
    2: (170, 257),
    3: (170, 290),
    4: (170, 322),
}
MEAS_SOURCE_B_CHANNELS = {
    1: (445, 224),
    2: (445, 257),
    3: (445, 290),
    4: (445, 322),
}
MEAS_SOURCE_MATH = (255, 224)

# Vertical-tab tiles (x positions roughly: 124, 216, 308, 399, 491, 583;
# y rows: 240, 298, 355).
MEAS_VERTICAL_TILES = {
    "Vpp":         (124, 240),
    "Max":         (216, 240),
    "Min":         (308, 240),
    "Amplitude":   (399, 240),
    "VTop":        (491, 240),
    "VBase":       (583, 240),
    "Avg":         (124, 298),
    "CycleAvg":    (216, 298),
    "Stdev":       (308, 298),
    "CycleStdev":  (399, 298),
    "RMS":         (491, 298),
    "CycleRMS":    (583, 298),
    "FOV":         (124, 355),
    "FPRE":        (216, 355),
    "ROV":         (308, 355),
    "RPRE":        (399, 355),
    "Level@X":     (491, 355),
}

# Horizontal-tab tiles (single-source timing measurements).
MEAS_HORIZONTAL_TILES = {
    "Cycle":       (124, 240),
    "Freq":        (216, 240),
    "+Pulse":      (308, 240),
    "-Pulse":      (399, 240),
    "+Time":       (491, 240),
    "-Time":       (583, 240),
    "PulseWidth":  (124, 298),
    "+Duty":       (216, 298),
    "-Duty":       (308, 298),
    "Delay":       (399, 298),
    "Time@Level":  (491, 298),
}

# Others-tab tiles (two-source measurements; Source B selectable).
MEAS_OTHERS_TILES = {
    "Phase":       (124, 240),
    "FRFR":        (216, 240),
    "FRFF":        (308, 240),
    "FFFR":        (399, 240),
    "FFFF":        (491, 240),
    "FRLF":        (583, 240),
    "FFLF":        (124, 298),
    "SKEW":        (216, 298),
    "FRLR":        (308, 298),
    "FFLR":        (399, 298),
}

MEAS_DIALOG_CLOSE = (664, 68)   # X glyph centered at (664, 68); was 655 (miss)
MEAS_CLEAR_BUTTON = (615, 107)

# OCR target: bottom-left of the screen where readouts stack vertically.
# Each readout occupies roughly a 200x18 strip starting near y=415.
READOUT_REGION = (0, 410, 650, 480)


# Suffix → multiplier (for value conversion).
SI_SUFFIXES = {
    "p": 1e-12, "n": 1e-9, "u": 1e-6, "μ": 1e-6, "m": 1e-3,
    "":  1.0,
    "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9,
}

# Units we recognise; matched after the SI prefix.
UNIT_RE = r"(?:V|A|s|Hz|%|dB|S|VA|W|°|deg)"

# Matches "Name:Value Unit" or "Name = Value Unit". Allows ":" or " " separator.
# Names may include parenthesised source-pair suffixes such as "(3-4)" used by
# Others-tab measurements like ``Phase(3-4):-0.03°``.
# Examples: "Vpp:440.00mV", "Freq:1.000kHz", "SKEW(3-4):-72.00ns"
VALUE_RE = re.compile(
    rf"""
    (?P<name>[+\-]?[A-Za-z][A-Za-z0-9@_\-+]*?(?:\([^)]+\))?)\s*[:=]\s*
    (?P<sign>[-+]?)
    (?P<num>\d+(?:\.\d+)?)\s*
    (?P<prefix>[pnuμmkKMG]?)
    (?P<unit>{UNIT_RE})?
    """,
    re.VERBOSE,
)

# "Name:***" — scope couldn't compute a value (typically no stable trigger).
NOVAL_RE = re.compile(r"(?P<name>[+\-]?[A-Za-z][A-Za-z0-9@_\-+ ]*?(?:\([^)]+\))?)\s*[:=]\s*\*+")


def _to_float(sign: str, num: str, prefix: str) -> float:
    val = float(num) * SI_SUFFIXES.get(prefix, 1.0)
    return -val if sign == "-" else val


def parse_readouts(text: str) -> dict[str, dict]:
    """Parse OCR output into {name: {'value': float, 'unit': str, 'raw': str}}.

    Multiple measurements can share a line (the scope displays them side-by-side),
    so we scan with finditer rather than search. Readings whose value the scope
    can't compute show as ``Name:***`` and are returned with ``value=None``.
    """
    out: dict[str, dict] = {}
    for m in VALUE_RE.finditer(text):
        name = m.group("name")
        unit = m.group("unit") or ""
        val = _to_float(m.group("sign"), m.group("num"), m.group("prefix"))
        out[name] = {"value": val, "unit": unit, "raw": m.group(0).strip()}
    # Capture "Name:***" no-value entries too.
    for m in NOVAL_RE.finditer(text):
        name = m.group("name")
        if name not in out:
            out[name] = {"value": None, "unit": "", "raw": m.group(0).strip()}
    return out


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """Turn the dark-themed readout strip into clean black-on-white text.

    Readouts use the channel colour (yellow for CH1, cyan for CH2, magenta CH3,
    blue CH4) on a near-black background. We collapse to ``max(R,G,B)`` so all
    colours map to a similar bright value, scale up, then threshold + invert.
    """
    img = img.convert("RGB")
    px = img.load()
    w, h = img.size
    out = Image.new("L", (w, h))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > g:
                op[x, y] = r if r > b else b
            else:
                op[x, y] = g if g > b else b
    out = out.resize((w * 4, h * 4), Image.LANCZOS)
    return out.point(lambda v: 0 if v > 80 else 255, "L")


def ocr_readouts(png_path: str | Path,
                 region: tuple[int, int, int, int] = READOUT_REGION) -> dict[str, dict]:
    img = Image.open(png_path).crop(region)
    prepped = _preprocess_for_ocr(img)
    text = pytesseract.image_to_string(prepped, config="--psm 6")
    return parse_readouts(text)
