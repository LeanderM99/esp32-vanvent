"""Log one UART line through a USB-UART adapter: timestamped hex + ASCII per burst.

    python sniff.py COM5 9600
    python sniff.py COM5 115200 --gap 0.02

Adapter RX -> J2 UTX, adapter GND -> J2 GND, adapter set to 3.3 V. Nothing else.
A new line starts after `gap` seconds of silence. Ctrl+C to stop.
"""
import argparse
import time

import serial


def fmt(burst: bytes) -> str:
    ascii_ = "".join(chr(b) if 32 <= b < 127 else "." for b in burst)
    return f"{burst.hex(' ')}  |{ascii_}|"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("baud", type=int, nargs="?", default=9600)
    ap.add_argument("--gap", type=float, default=0.02)
    a = ap.parse_args()
    t0 = time.monotonic()
    buf, start = bytearray(), 0.0
    with serial.Serial(a.port, a.baud, timeout=a.gap) as s:
        print(f"listening on {a.port} @ {a.baud}")
        while True:
            chunk = s.read(s.in_waiting or 1)  # empty after `gap` of silence
            if chunk:
                if not buf:
                    start = time.monotonic() - t0
                buf += chunk
            if buf and (not chunk or len(buf) >= 256):
                print(f"{start:9.3f}  {fmt(bytes(buf))}", flush=True)
                buf.clear()


if __name__ == "__main__":
    assert fmt(b"\x55\xaaHi\n") == "55 aa 48 69 0a  |U.Hi.|"
    try:
        main()
    except KeyboardInterrupt:
        pass
