"""Touchscreen-driven Math / FFT helper for the FNIRSI DPOF1204-200.

SCPI :MATH:* and :FFT:* are broken on this firmware (return "deadline has
elapsed"), so we drive the on-screen Math dialog instead.

Access path:
    Gear icon (753, 450)  →  Function Menu  →  Math (363, 350)
    → Math dialog opens.

Layout (Math dialog, 800x480 frame):

Page 1, all operators except FFT:
    Operation toggle  : (162, 113)
    Operator dropdown : (520, 113)
    Source A dropdown : (167, 163)
    Source B dropdown : (517, 163)
    Scale dropdown    : (200, 213)
    Position field    : (548, 213)
    Close (X)         : (665,  68)

Page 1, when Operator == FFT:
    Operation toggle  : (162, 113)
    Operator dropdown : (520, 113)
    Auto Setup button : (619, 113)
    Source A dropdown : (167, 163)
    Display Full/Excl : (145, 216) / (220, 216)
    Unit selector     : dBVrms (503, 216) / Vrms (563, 216) / dBm (617, 216)
    Window dropdown   : (200, 265)
    Scale field       : (548, 265)
    External Load     : (167, 315)
    Ref Level         : (548, 315)
    Center Freq       : (167, 365)
    Horiz Range       : (548, 365)
    Next page         : (358, 410)
    Close (X)         : (665,  68)

Page 2 (FFT only):
    Peak Search toggle: (172, 217)
    Previous page     : (358, 410)
"""
from __future__ import annotations

# Entry path.
GEAR_BUTTON = (753, 450)
FUNCTION_MENU_MATH = (363, 350)
FUNCTION_MENU_CLOSE = (685, 290)
MATH_DIALOG_CLOSE = (665, 68)

# Common (any operator).
MATH_OPERATION_TOGGLE = (162, 113)
MATH_OPERATOR_DROPDOWN = (520, 113)
MATH_SOURCE_A_DROPDOWN = (167, 163)
MATH_SOURCE_B_DROPDOWN = (517, 163)
MATH_SCALE_DROPDOWN = (200, 213)
MATH_POSITION_FIELD = (548, 213)

# FFT page 1 only.
MATH_AUTO_SETUP = (619, 113)
MATH_FFT_DISPLAY_FULL = (145, 216)
MATH_FFT_DISPLAY_EXCLUSIVE = (220, 216)
MATH_FFT_UNIT_DBVRMS = (503, 216)
MATH_FFT_UNIT_VRMS   = (563, 216)
MATH_FFT_UNIT_DBM    = (617, 216)
MATH_FFT_WINDOW_DROPDOWN = (200, 265)
MATH_FFT_SCALE_FIELD     = (548, 265)
MATH_FFT_EXTERNAL_LOAD   = (167, 315)
MATH_FFT_REF_LEVEL       = (548, 315)
MATH_FFT_CENTER_FREQ     = (167, 365)
MATH_FFT_HORIZ_RANGE     = (548, 365)
MATH_FFT_NEXT_PAGE       = (358, 410)
MATH_FFT_PREV_PAGE       = (358, 410)  # same location, label changes

# FFT page 2.
MATH_FFT_PEAK_SEARCH_TOGGLE = (172, 217)

# Operator dropdown grid (2 cols × 4 rows). Tap MATH_OPERATOR_DROPDOWN first.
MATH_OPERATORS = {
    "+":    (520, 144),
    "FFT":  (614, 144),
    "-":    (520, 177),
    "d/dt": (614, 177),
    "*":    (520, 211),
    "intdt":(614, 211),   # ∫dt
    "/":    (520, 244),
    "sqrt": (614, 244),   # √
}

# Source A/B dropdown (vertical list). Tap MATH_SOURCE_A_DROPDOWN first.
MATH_SOURCE_CHANNELS = {
    1: (167, 192),
    2: (167, 225),
    3: (167, 258),
    4: (167, 290),
}
MATH_SOURCE_B_CHANNELS = {
    1: (517, 192),
    2: (517, 225),
    3: (517, 258),
    4: (517, 290),
}
