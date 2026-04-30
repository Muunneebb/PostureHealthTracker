from PIL import Image, ImageDraw, ImageFont
from . import config

try:
    import board
    import busio
    import adafruit_ssd1306
    HW = True
except Exception:
    HW = False


class OLED:
    def __init__(self):
        self.available = False
        if not HW:
            return
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=config.SSD1306_I2C_ADDR)
            self.display.fill(0)
            self.display.show()
            self.font = ImageFont.load_default()
            self.available = True
        except Exception:
            self.available = False

    def show_status(self, lines):
        # lines: list of strings (max 4-6)
        if not self.available:
            print('\n'.join(lines))
            return
        image = Image.new('1', (128, 64))
        draw = ImageDraw.Draw(image)
        y = 0
        for line in lines:
            draw.text((0, y), line, font=self.font, fill=255)
            y += 10
        self.display.image(image)
        self.display.show()
