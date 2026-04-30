import time
import math
from . import config
from .utils import accel_to_pitch_roll

try:
    import board
    import busio
    import adafruit_mpu6050
    from adafruit_ads1x15.ads1115 import ADS1115
    from adafruit_ads1x15.analog_in import AnalogIn
    HW_AVAILABLE = True
except Exception:
    HW_AVAILABLE = False


class IMU:
    def __init__(self, i2c=None):
        self.available = False
        if not HW_AVAILABLE:
            return
        try:
            if i2c is None:
                i2c = busio.I2C(board.SCL, board.SDA)
            self.mpu = adafruit_mpu6050.MPU6050(i2c)
            self.available = True
        except Exception:
            self.available = False

    def read_tilt(self):
        if not self.available:
            return {'pitch':0,'roll':0,'acc':(0,0,1)}
        ax, ay, az = self.mpu.acceleration
        pitch, roll = accel_to_pitch_roll(ax, ay, az)
        return {'pitch':pitch, 'roll':roll, 'acc':(ax, ay, az)}


class ADSInputs:
    def __init__(self, i2c=None):
        self.available = False
        if not HW_AVAILABLE:
            return
        try:
            if i2c is None:
                i2c = busio.I2C(board.SCL, board.SDA)
            self.ads = ADS1115(i2c, address=config.ADS1115_ADDR)
            self.chan0 = AnalogIn(self.ads, 0)
            self.chan1 = AnalogIn(self.ads, 1)
            self.chan2 = AnalogIn(self.ads, 2)
            self.chan3 = AnalogIn(self.ads, 3)
            self.available = True
        except Exception:
            self.available = False

    def read_fsr_left(self):
        if not self.available:
            return 0
        return self.chan0.value

    def read_fsr_right(self):
        if not self.available:
            return 0
        return self.chan1.value

    def read_fsr_center(self):
        if not self.available:
            return 0
        return self.chan2.value

    def read_gsr(self):
        if not self.available:
            return 0
        return self.chan3.value


class MAX30102Sensor:
    def __init__(self):
        # Try import; reading implementation depends on library
        try:
            from max30102 import MAX30102
            self.dev = MAX30102()
            self.available = True
        except Exception:
            self.dev = None
            self.available = False

    def read(self, samples=100):
        # returns (heart_rate_bpm, rr_intervals_ms_list)
        if not self.available:
            return None, []
        # The real implementation requires signal processing to detect beats.
        # For demo code we return None. Integrate with appropriate library example.
        return None, []

