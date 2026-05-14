"""Verify *SAV / *RCL actually persist state, and which acquisition modes take."""
from scope import Scope
import time

with Scope() as s:
    # === SAV/RCL test ===
    # Capture initial scale, change it, save, change again, recall.
    s.write(":CHAN2:SCAL 0.5")
    time.sleep(0.2)
    a = s.send_scpi(":CHAN2:SCAL?").data
    print(f"set 0.5V/div, read: {a!r}")
    s.write("*SAV 1")
    time.sleep(0.5)
    s.write(":CHAN2:SCAL 2.0")
    time.sleep(0.2)
    b = s.send_scpi(":CHAN2:SCAL?").data
    print(f"set 2.0V/div, read: {b!r}")
    s.write("*RCL 1")
    time.sleep(1.0)
    c = s.send_scpi(":CHAN2:SCAL?").data
    print(f"after RCL 1, read: {c!r}  (should be 0.5)")

    # === Acquisition modes: do HRES/AVER actually take? ===
    print()
    for m in ("NORM", "PEAK", "HRES", "AVER", "NORM"):
        s.write(f":ACQ:TYPE {m}")
        time.sleep(0.2)
        got = s.send_scpi(":ACQ:TYPE?").data
        print(f"set ACQ:TYPE {m:5s} -> read {got!r}")

    # === :ACQ:AVER N (averaging count) ===
    print()
    for n in (4, 16, 64, 256):
        s.write(":ACQ:TYPE AVER")
        s.write(f":ACQ:AVER {n}")
        time.sleep(0.2)
        got = s.send_scpi(":ACQ:AVER?").data
        print(f"set ACQ:AVER {n:4d} -> read {got!r}")
    s.write(":ACQ:TYPE NORM")
