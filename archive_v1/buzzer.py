import time
from . import config
try:
    import RPi.GPIO as GPIO
    HW = True
except Exception:
    HW = False


class Buzzer:
    def __init__(self, pin=config.BUZZER_GPIO):
        self.available = False
        if not HW:
            return
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.available = True

    def beep(self, duration=0.2, times=1, interval=0.1):
        if not self.available:
            print(f"Buzzer beep x{times}")
            return
        for _ in range(times):
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(interval)

    def cleanup(self):
        if self.available:
            GPIO.cleanup(self.pin)
