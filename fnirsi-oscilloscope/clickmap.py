"""Tier 3.9 — Interactive click-map calibration helper.

Captures the current scope screen, displays it via PIL ``show()`` (opens
in the default image viewer), and lets you build a JSON map of labelled
(x, y) UI coordinates by typing them in.

If you have GUI matplotlib available, you can also use the second mode
(``--gui``) which lets you click directly on the displayed image.

Output: ``clickmap.json`` in the current directory, structured as::

    {
      "ch1_toggle": [760, 145],
      "ch2_toggle": [760, 220],
      "measure_button": [614, 30],
      ...
    }

The Scope class can then load these instead of hard-coded constants.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

from screen import capture, save_png


DEFAULT_LABELS = [
    "ch1_toggle", "ch2_toggle", "ch3_toggle", "ch4_toggle",
    "measure_button", "cursor_button", "runstop_button",
    "trigger_button", "autoset_button", "single_button",
    "math_button", "meas_dialog_close",
    "meas_dialog_source_a", "meas_dialog_vpp",
]


def cli_mode(host: str, out: Path, labels: list[str]):
    raw = capture(host)
    snap = out.with_suffix(".calib.png")
    save_png(raw, str(snap))
    print(f"Saved current screen to {snap}.")
    print("Open it in your image viewer and read pixel coords.")
    print("For each label, enter 'x,y' or blank to skip, or 'q' to stop.\n")

    data = {}
    if out.exists():
        try:
            data = json.loads(out.read_text())
            print(f"(Loaded {len(data)} existing entries from {out})")
        except json.JSONDecodeError:
            pass

    for label in labels:
        cur = data.get(label)
        prompt = f"  {label}"
        if cur:
            prompt += f" [{cur[0]},{cur[1]}]"
        prompt += ": "
        try:
            s = input(prompt).strip()
        except EOFError:
            break
        if s in ("q", "quit"):
            break
        if not s:
            continue
        try:
            x_s, y_s = s.split(",")
            data[label] = [int(x_s.strip()), int(y_s.strip())]
        except ValueError:
            print(f"  ignored: cannot parse {s!r}")

    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"\nWrote {len(data)} entries to {out}.")


def gui_mode(host: str, out: Path, labels: list[str]):
    try:
        import matplotlib.pyplot as plt
        from PIL import Image
    except ImportError:
        print("GUI mode needs matplotlib + Pillow. Falling back to CLI.")
        return cli_mode(host, out, labels)

    raw = capture(host)
    snap = out.with_suffix(".calib.png")
    save_png(raw, str(snap))

    data: dict = {}
    if out.exists():
        try:
            data = json.loads(out.read_text())
        except json.JSONDecodeError:
            pass

    pending = list(labels)
    fig, ax = plt.subplots()
    ax.imshow(Image.open(snap))
    ax.set_title(f"Click for: {pending[0]}  (right-click=skip)")

    def on_click(evt):
        nonlocal pending
        if evt.inaxes is not ax or not pending:
            return
        label = pending[0]
        if evt.button == 3:
            print(f"  {label}: skipped")
        else:
            x, y = int(round(evt.xdata)), int(round(evt.ydata))
            data[label] = [x, y]
            print(f"  {label}: ({x},{y})")
        pending = pending[1:]
        if pending:
            ax.set_title(f"Click for: {pending[0]}  (right-click=skip)")
            fig.canvas.draw_idle()
        else:
            plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", on_click)
    plt.show()
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"\nWrote {len(data)} entries to {out}.")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--host", default="192.168.0.75")
    p.add_argument("--out", type=Path, default=Path("clickmap.json"))
    p.add_argument("--gui", action="store_true",
                   help="Interactive matplotlib click-to-pick")
    p.add_argument("--label", action="append",
                   help="Custom label(s); may repeat. Replaces default set.")
    args = p.parse_args()
    labels = args.label or DEFAULT_LABELS
    (gui_mode if args.gui else cli_mode)(args.host, args.out, labels)


if __name__ == "__main__":
    main()
