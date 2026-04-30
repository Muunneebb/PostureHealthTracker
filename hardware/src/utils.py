import time
import math
import csv
from collections import deque

def rmssd(rr_intervals_ms):
    if not rr_intervals_ms:
        return None
    diffs = [(rr_intervals_ms[i] - rr_intervals_ms[i-1]) for i in range(1, len(rr_intervals_ms))]
    sq = [d*d for d in diffs]
    return math.sqrt(sum(sq)/len(sq)) if sq else None

class RollingAverage:
    def __init__(self, size=5):
        self.buf = deque(maxlen=size)

    def update(self, value):
        self.buf.append(value)
        return sum(self.buf)/len(self.buf)

def log_row(path, row, header=None):
    write_header = False
    try:
        with open(path, 'r'):
            pass
    except FileNotFoundError:
        write_header = True

    with open(path, 'a', newline='') as f:
        w = csv.writer(f)
        if write_header and header:
            w.writerow(header)
        w.writerow(row)

def clamp(x, a, b):
    return max(a, min(b, x))

def accel_to_pitch_roll(ax, ay, az):
    # simple conversions in degrees
    # pitch: rotation around X axis; roll: rotation around Y axis
    pitch = math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))
    roll = math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))
    return pitch, roll
