from machine import I2C, Pin
import time
import framebuf
from micropython import const

# ==========================================
# BIBLIOTECA DISPLAY GRANDE (SH1107)
# ==========================================
_LOW_COLUMN_ADDRESS = const(0x00)
_HIGH_COLUMN_ADDRESS = const(0x10)
_MEM_ADDRESSING_MODE = const(0x20)
_SET_CONTRAST = const(0x8100)
_SET_SEGMENT_REMAP = const(0xA0)
_SET_MULTIPLEX_RATIO = const(0xA800)
_SET_NORMAL_INVERSE = const(0xA6)
_SET_DISPLAY_OFFSET = const(0xD300)
_SET_DC_DC_CONVERTER_SF = const(0xAD81)
_SET_DISPLAY_OFF = const(0xAE)
_SET_DISPLAY_ON = const(0xAF)
_SET_PAGE_ADDRESS = const(0xB0)
_SET_SCAN_DIRECTION = const(0xC0)
_SET_DISP_CLK_DIV = const(0xD550)
_SET_DIS_PRECHARGE = const(0xD922)
_SET_VCOM_DSEL_LEVEL = const(0xDB35)

class SH1107(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc=False, delay_ms=50, rotate=0):
        self.width = width; self.height = height; self.external_vcc = external_vcc
        self.delay_ms = delay_ms; self.rotate = rotate; self.rotate90 = rotate == 90 or rotate == 270
        self.flip_flag = False; self.inverse = False
        if self.rotate90: self.width, self.height = self.height, self.width; _mode = framebuf.MONO_VLSB
        else: _mode = framebuf.MONO_HMSB
        self.pages = self.height // 8; self.buffer = bytearray(self.pages * self.width)
        self.buffer_mv = memoryview(self.buffer)
        super().__init__(self.buffer, self.width, self.height, _mode); self.init_display()

    def init_display(self):
        _mux = 0x7F if self.height == 128 else 0x3F; self.reset()
        self.write_command(bytes([_SET_DISPLAY_OFF])); self.fill(0)
        self.write_command((_SET_MULTIPLEX_RATIO | _mux).to_bytes(2, "big"))
        self.write_command((_MEM_ADDRESSING_MODE | (0x00 if self.rotate90 else 0x01)).to_bytes(1, "big"))
        self.write_command(bytes([_SET_PAGE_ADDRESS])); self.write_command(_SET_DC_DC_CONVERTER_SF.to_bytes(2, "big"))
        self.write_command(_SET_DISP_CLK_DIV.to_bytes(2, "big")); self.write_command(_SET_VCOM_DSEL_LEVEL.to_bytes(2, "big"))
        self.write_command(_SET_DIS_PRECHARGE.to_bytes(2, "big")); self.contrast(0x80); self.invert(0)
        self.flip(False, update=False); self.write_command(bytes([_SET_DISPLAY_ON])); time.sleep_ms(self.delay_ms)

    def contrast(self, contrast): self.write_command((_SET_CONTRAST | (contrast & 0xFF)).to_bytes(2, "big"))
    def invert(self, invert=0): self.write_command((_SET_NORMAL_INVERSE | (invert & 1)).to_bytes(1, "big")); self.inverse = bool(invert)

    def flip(self, flag=None, update=False):
        if flag is None: flag = not self.flip_flag
        if self.height == 128 and self.width == 128: _row_offset = 0x00
        elif self.rotate90: _row_offset = 0x60
        else: _row_offset = 0x20 if (self.rotate == 180) ^ flag else 0x60
        _remap = 0x00 if (self.rotate in (90, 180)) ^ flag else 0x01
        _direction = 0x08 if (self.rotate in (180, 270)) ^ flag else 0x00
        self.write_command((_SET_DISPLAY_OFFSET | _row_offset).to_bytes(2, "big"))
        self.write_command(bytes([_SET_SEGMENT_REMAP | _remap]))
        self.write_command(bytes([_SET_SCAN_DIRECTION | _direction]))
        self.flip_flag = flag
        if update: self.show()

    def show(self):
        if self.rotate90:
            _cmd = bytearray(3); _cmd[1] = _LOW_COLUMN_ADDRESS; _cmd[2] = _HIGH_COLUMN_ADDRESS
            for _page in range(self.pages):
                _cmd[0] = _SET_PAGE_ADDRESS | _page; self.write_command(_cmd)
                _start = self.width * _page; self.write_data(self.buffer_mv[_start:_start + self.width])
        else:
            _row_bytes = self.width // 8; _cmd = bytearray(2)
            for _row in range(self.height):
                _cmd[0] = _row & 0x0F; _cmd[1] = _HIGH_COLUMN_ADDRESS | (_row >> 4)
                self.write_command(_cmd); _start = _row * _row_bytes; self.write_data(self.buffer_mv[_start:_start + _row_bytes])

    def reset(self): pass

class SH1107_I2C(SH1107):
    def __init__(self, width, height, i2c, res=None, address=0x3C, rotate=0, external_vcc=False, delay_ms=50):
        self.i2c = i2c; self.address = address; self.res = res
        if res is not None: res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc, delay_ms, rotate)

    def write_command(self, command_list): self.i2c.writeto(self.address, b"\x00" + command_list)
    def write_data(self, buf): self.i2c.writevto(self.address, (b"\x40", buf))

    def reset(self):
        if self.res is not None:
            self.res(1); time.sleep_ms(1); self.res(0); time.sleep_ms(20); self.res(1); time.sleep_ms(20)

# ==========================================
# CONFIGURAÇÃO E SENSOR
# ==========================================
i2c_sensor = I2C(0, sda=Pin(8), scl=Pin(9), freq=100000)
i2c_display = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)

oled = SH1107_I2C(128, 64, i2c_display)

I2C_ADDR = 0x57
CMD_START = 0x01
REG_READ  = 0xAF
DIST_PERIGO = 15.0
DIST_ALERTA = 30.0
TIMEOUT_MS  = 600

def ler_sensor():
    try: i2c_sensor.writeto(I2C_ADDR, bytes([CMD_START]))
    except: pass
    time.sleep_ms(120)
    try:
        i2c_sensor.writeto(I2C_ADDR, bytes([REG_READ]))
        dados = i2c_sensor.readfrom(I2C_ADDR, 3)
        if dados[0] == 0xFF and dados[1] == 0xFF: return None
        micrometros = (dados[0] << 16) | (dados[1] << 8) | dados[2]
        cm = micrometros / 10000.0
        if 2.0 <= cm <= 450.0: return cm
    except: pass
    return None

# ==========================================
# LOOP PRINCIPAL
# ==========================================
if 0x57 not in i2c_sensor.scan():
    oled.fill(0); oled.text("Sensor OFF", 20, 28); oled.show()
    while True: pass

ultimo_cm = None
ultimo_tempo = 0

while True:
    agora = time.ticks_ms()
    cm = ler_sensor()

    if cm is not None: ultimo_cm = cm; ultimo_tempo = agora
    else:
        if time.ticks_diff(agora, ultimo_tempo) > TIMEOUT_MS: ultimo_cm = None

    if ultimo_cm is None: status = "LIVRE"
    elif ultimo_cm <= DIST_PERIGO: status = "PERIGO"
    elif ultimo_cm <= DIST_ALERTA: status = "ALERTA"
    else: status = "LIVRE"

    oled.fill(0)
    oled.text("Sensor Ultrassonico", 0, 0)
    oled.rect(0, 12, 128, 1, 1)
    
    if ultimo_cm is not None:
        texto_dist = f"{ultimo_cm:.1f} cm"
        x = int(64 - (len(texto_dist) * 4))
        oled.text(texto_dist, x, 25)
    else:
        oled.text("LIVRE (sem eco)", 10, 25)

    if status == "PERIGO":
        oled.fill_rect(0, 50, 128, 14, 1)
        oled.text("PERIGO!", 32, 52, 0)
    elif status == "ALERTA":
        oled.fill_rect(0, 50, 64, 14, 1)
        oled.text("ALERTA", 12, 52, 0)
    else:
        oled.rect(0, 50, 128, 14, 1)
        oled.text("LIVRE", 44, 52)
        
    oled.show()
    time.sleep_ms(80)
