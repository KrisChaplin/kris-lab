"""Verification probe using Scope.query() which drains acks reliably."""
from scope import Scope
import time

GROUPS = {
    "acq.type": (
        (":ACQ:TYPE?", None),
        (":ACQ:TYPE NORM", None), (":ACQ:TYPE?", None),
        (":ACQ:TYPE PEAK", None), (":ACQ:TYPE?", None),
        (":ACQ:TYPE HRES", None), (":ACQ:TYPE?", None),
        (":ACQ:TYPE AVER", None), (":ACQ:TYPE?", None),
        (":ACQ:TYPE NORM", None), (":ACQ:TYPE?", None),
    ),
    "acq.aver": (
        (":ACQ:AVER?", None),
        (":ACQ:AVER 16", None), (":ACQ:AVER?", None),
        (":ACQ:AVER 64", None), (":ACQ:AVER?", None),
    ),
    "acq.mdep_srat": (
        (":ACQ:MDEP?", None), (":ACQ:SRAT?", None), (":ACQ:MODE?", None),
    ),
    "trig.mode": (
        (":TRIG:MODE?", None),
        (":TRIG:MODE PULS", None), (":TRIG:MODE?", None),
        (":TRIG:MODE EDGE", None), (":TRIG:MODE?", None),
    ),
    "trig.puls": (
        (":TRIG:MODE PULS", None),
        (":TRIG:PULS:SOUR?", None), (":TRIG:PULS:SOUR C2", None), (":TRIG:PULS:SOUR?", None),
        (":TRIG:PULS:WHEN?", None), (":TRIG:PULS:WHEN PGR", None), (":TRIG:PULS:WHEN?", None),
        (":TRIG:PULS:WIDT?", None), (":TRIG:PULS:WIDT 1e-6", None), (":TRIG:PULS:WIDT?", None),
        (":TRIG:PULS:LEV?", None), (":TRIG:PULS:LEV 0.5", None), (":TRIG:PULS:LEV?", None),
        (":TRIG:MODE EDGE", None),
    ),
    "saverestore": (
        ("*SAV 1", None), ("*RCL 1", None),
    ),
    "misc": (
        (":SYST:LANG?", None), (":SYST:TIME?", None), (":SYST:DATE?", None),
        (":CHAN1:LAB?", None), (":DISP:DATA?", None),
    ),
}

with Scope() as s:
    for name, cmds in GROUPS.items():
        print(f"--- {name} ---")
        for cmd, _ in cmds:
            r = s.send_scpi(cmd)
            tag = "OK " if r.ok else "ERR"
            print(f"  {tag} {cmd:40s} -> {r.data!r}")
            time.sleep(0.05)
        print()
