from machine import I2C, Pin
import sh1107
import time

# ===============================
# I2C — sensor e display
# ===============================
i2c_sensor = I2C(0, sda=Pin(8), scl=Pin(9), freq=100000)
i2c_display = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)

oled = sh1107.SH1107_I2C(128, 64, i2c_display)

# ===============================
# Constantes do sensor
# ===============================
I2C_ADDR = 0x57
CMD_START = 0x01
REG_READ = 0xAF
DIST_PERIGO = 15.0
DIST_ALERTA = 30.0
TIMEOUT_MS = 600


def ler_sensor():
    try:
        i2c_sensor.writeto(I2C_ADDR, bytes([CMD_START]))
    except:
        pass
    time.sleep_ms(120)
    try:
        i2c_sensor.writeto(I2C_ADDR, bytes([REG_READ]))
        dados = i2c_sensor.readfrom(I2C_ADDR, 3)
        if dados[0] == 0xFF and dados[1] == 0xFF:
            return None
        micrometros = (dados[0] << 16) | (dados[1] << 8) | dados[2]
        cm = micrometros / 10000.0
        if 2.0 <= cm <= 450.0:
            return cm
    except:
        pass
    return None


# ===============================
# LOOP PRINCIPAL
# ===============================
if I2C_ADDR not in i2c_sensor.scan():
    oled.fill(0)
    oled.text("Sensor OFF", 20, 28)
    oled.show()
    while True:
        pass

ultimo_cm = None
ultimo_tempo = 0

while True:
    agora = time.ticks_ms()
    cm = ler_sensor()

    if cm is not None:
        ultimo_cm = cm
        ultimo_tempo = agora
    else:
        if time.ticks_diff(agora, ultimo_tempo) > TIMEOUT_MS:
            ultimo_cm = None

    # Determina status
    if ultimo_cm is None:
        status = "LIVRE"
    elif ultimo_cm <= DIST_PERIGO:
        status = "PERIGO"
    elif ultimo_cm <= DIST_ALERTA:
        status = "ALERTA"
    else:
        status = "LIVRE"

    # Atualiza display
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
