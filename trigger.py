"""Touchscreen-driven control of the FNIRSI DPOF1204-200 Trigger dialog.

SCPI advanced-trigger commands are broken on this firmware, so we drive the
on-screen Trigger dialog instead. Basic Edge trigger (source / level / slope)
*does* have working SCPI in :TRIG:EDGE:* — prefer those when possible.
Use this module for trigger Type changes (Pulse, Slope, Video, Window, etc.)
and other UI-only fields like Holdoff / Noise Reject / Coupling.

Layout (768x480 screen, all coords are x,y in pixels):

    Type dropdown:    (183, 108)   → opens 3-col grid of types.
    Source dropdown:  (183, 154)   → opens CH1..CH4 list.
    Slope buttons:    Rising (151,205) / Falling (213,205) / Either (276,205)
    Mode buttons:     Auto (481,110) / Normal (543,110) / Single (605,110)
    Coupling drop:    (514, 154)
    Level field:      (514, 205)
    Holdoff toggle:   (160, 358)
    Noise Reject:     (502, 358)
    Tab bar:          Vertical/Horizontal/Trigger/Measure (y=428)
    Close (X):        (755, 68)

Type dropdown grid (3 cols × 5 rows, starts y≈137 with 32px row pitch,
columns at x≈183, 303, 423):
"""
from __future__ import annotations

# Top-bar T-icon (opens Trigger dialog directly).
TRIG_OPEN_BUTTON = (453, 30)
TRIG_DIALOG_CLOSE = (755, 68)

# Dropdown closed states.
TRIG_TYPE_DROPDOWN = (183, 108)
TRIG_SOURCE_DROPDOWN = (183, 154)
TRIG_COUPLING_DROPDOWN = (514, 154)
TRIG_LEVEL_FIELD = (514, 205)

# Slope (Edge trigger only)
TRIG_SLOPE = {
    "rising":  (151, 205),
    "falling": (213, 205),
    "either":  (276, 205),
}

# Trigger mode pills along the top right.
TRIG_MODE = {
    "auto":   (481, 110),
    "normal": (543, 110),
    "single": (605, 110),
}

# Toggle switches.
TRIG_HOLDOFF_TOGGLE = (160, 358)
TRIG_NOISE_TOGGLE = (502, 358)

# Source dropdown expansion (CH1..4).
TRIG_SOURCE_CHANNELS = {
    1: (183, 184),
    2: (183, 215),
    3: (183, 247),
    4: (183, 278),
}

# Trigger Type dropdown — 3-col grid. Captures the available types on
# this firmware as of the last screenshot.
TRIG_TYPES = {
    "edge":     (183, 137),
    "slope":    (303, 137),
    "pulse":    (423, 137),
    "video":    (183, 170),
    "window":   (303, 170),
    "interval": (423, 170),
    "runt":     (183, 202),
    "dropout":  (303, 202),
    "pattern":  (423, 202),
    "i2c":      (183, 234),
    "spi":      (303, 234),
    "uart":     (423, 234),
    "can":      (183, 266),
    "lin":      (303, 266),
}

# Tabs at the bottom of any dialog with this footer (shared with Measure).
TRIG_TABS = {
    "vertical":   (372, 428),
    "horizontal": (455, 428),
    "trigger":    (538, 428),
    "measure":    (619, 428),
}
