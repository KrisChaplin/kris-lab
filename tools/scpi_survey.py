#!/usr/bin/env python3
"""Probe many SCPI queries against the DPOF1204 and print results.

This is a discovery script: identify which command tree the firmware
implements. The DPOF1204 manuals are scarce, so we try several common
oscilloscope SCPI dialects (Rigol DS/MSO, Keysight, SCPI-99, plus a few
Fnirsi-specific guesses based on the in-firmware JS strings).
"""
import time
from scope import Scope

QUERIES = [
    # IEEE 488.2 common
    "*IDN?", "*OPC?", "*ESR?", "*STB?", "*TST?", "*RST?",
    # SYSTem
    "SYST:VERS?", "SYST:ERR?", "SYST:DATE?", "SYST:TIME?",
    # Acquire / Run state (Rigol-like)
    ":RUN", ":STOP", ":SING",
    ":ACQ:STAT?", ":ACQ:TYPE?", ":ACQ:MODE?", ":ACQ:SRAT?",
    ":TRIG:STAT?", ":TRIG:MODE?", ":TRIG:SWE?",
    ":TRIG:EDGE:SOUR?", ":TRIG:EDGE:LEV?", ":TRIG:EDGE:SLOP?",
    # Timebase
    ":TIM:SCAL?", ":TIM:OFFS?", ":TIM:MODE?", ":TIM:MAIN:SCAL?",
    "TIMEBASE:SCALE?", "HORIZONTAL:SCALE?",
    # Channel (try both forms)
    ":CHAN1:DISP?", ":CHAN1:SCAL?", ":CHAN1:OFFS?", ":CHAN1:COUP?",
    ":CHAN1:PROB?", ":CHAN1:BWL?", ":CHAN1:INV?", ":CHAN1:UNIT?",
    ":CHAN2:DISP?", ":CHAN2:SCAL?", ":CHAN2:OFFS?", ":CHAN2:COUP?",
    ":CHAN2:PROB?", ":CHAN2:BWL?",
    "CHANNEL2:SCALE?",
    # Measurements
    ":MEAS:FREQ? CHAN2", ":MEAS:VPP? CHAN2", ":MEAS:VAMP? CHAN2",
    ":MEAS:VMAX? CHAN2", ":MEAS:VMIN? CHAN2", ":MEAS:VAVG? CHAN2",
    ":MEAS:VRMS? CHAN2", ":MEAS:PER? CHAN2", ":MEAS:DUTY? CHAN2",
    ":MEAS:RISE? CHAN2", ":MEAS:FALL? CHAN2",
    ":MEAS:ITEM? VPP,CHAN2", ":MEAS:ITEM? FREQ,CHAN2",
    "MEASURE:VPP? CHAN2", "MEASURE:FREQUENCY? CHAN2",
    # Waveform
    ":WAV:SOUR?", ":WAV:FORM?", ":WAV:MODE?", ":WAV:POIN?",
    ":WAV:XINC?", ":WAV:XOR?", ":WAV:YINC?", ":WAV:YOR?", ":WAV:YREF?",
    ":WAV:PRE?",
    # Display / acquisition memory depth
    ":ACQ:MDEP?", ":ACQ:MEMD?", ":MEM:DEPT?",
    # LXI
    "LXI:IDEN:STAT?",
]


def main():
    with Scope(timeout=2.5) as s:
        for q in QUERIES:
            try:
                r = s.scpi(q)
            except Exception as e:
                print(f"{q:30s}  EXC {e}")
                # reconnect on error
                try:
                    s.close(); s.open()
                except Exception as e2:
                    print(f"  reconnect failed: {e2}")
                    return
                continue
            if r is None:
                print(f"{q:30s}  (no-reply expected)")
            else:
                print(f"{q:30s}  code={r.code}  {r.data!r}")
            time.sleep(0.02)


if __name__ == "__main__":
    main()
