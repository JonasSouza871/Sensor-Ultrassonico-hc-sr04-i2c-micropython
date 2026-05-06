# HC-SR04 Ultrassônico I2C — MicroPython

![](https://img.shields.io/badge/MicroPython-2B2728?logo=micropython&logoColor=white)
![](https://img.shields.io/badge/RP2040-A22846?logo=raspberrypi&logoColor=white)
![](https://img.shields.io/badge/I2C-FF6F00?logo=i2c&logoColor=white)
![](https://img.shields.io/badge/HC--SR04-00A86B)
![](https://img.shields.io/badge/OLED%20SSD1306%20%7C%20SH1107-9B59B6)
![](https://img.shields.io/badge/BitDogLab%20v7-6C3483)

---

## Visão Geral

Este projeto implementa a leitura de distância do sensor ultrassônico HC‑SR04 configurado em **modo I2C**, exibindo o resultado em um display OLED (SSD1306 ou SH1107). O código foi desenvolvido em **MicroPython** para a placa **BitDogLab v7** (RP2040).

O sensor é conectado via I2C nos pinos **SDA=8 / SCL=9**, e o display em um barramento I2C separado com **SDA=2 / SCL=3**, garantindo estabilidade na comunicação e evitando contenção de barramento.

---

## Configuração do Módulo HC‑SR04 — jumper M1/M2

O HC‑SR04 possui dois jumpers de solda (M1 e M2) na parte traseira do módulo que definem o protocolo de comunicação:

| M1 | M2 | Modo |
|:--:|:--:|------|
| 0  | 0  | GPIO padrão (Trigger/Echo) |
| **1** | **0** | **I2C** |
| 1  | 1  | 1-Wire |
| 0  | 1  | UART |

> **Importante:** Para utilizar o modo I2C, o jumper **M1 deve ser soldado (1)** e o **M2 deve permanecer aberto (0)**. Sem essa solda, o sensor não responde no endereço `0x57` do barramento I2C.

<img src="Imagens/3.%20Ligação%20M1%20.jpeg" width="480" alt="Ligação M1"/>

---

## Conexão com a BitDogLab v7

Os conectores I2C dedicados da BitDogLab v7 não foram utilizados nesta montagem. Em vez disso, as conexões foram feitas diretamente nos **pinos inferiores da placa** (GPIO 8/9 para o sensor, GPIO 2/3 para o display), utilizando **jumpers convencionais**. Essa escolha foi feita pela **maior estabilidade mecânica** que os pinos inferiores proporcionam com cabos jumper.

<img src="Imagens/4.%20Circuito%20montado.jpeg" width="480" alt="Circuito montado"/>

### Pinagem

| Componente | SDA | SCL | I2C |
|------------|:---:|:---:|:---:|
| HC‑SR04    | GP8 | GP9 | I2C0 |
| OLED       | GP2 | GP3 | I2C1 |

**Observação:** Futuramente está prevista a confecção de uma **placa adaptadora** para utilizar os conectores I2C originais da BitDogLab v7, eliminando a necessidade de jumpers avulsos e tornando a conexão mais robusta.

---

## Estrutura do Repositório

```
/
├── lib/
│   ├── ssd1306.py          # Driver do display OLED SSD1306
│   └── sh1107.py           # Driver do display OLED SH1107
├── script/
│   ├── Sensor_ultrassonico_display_ssd1306.py   # Script único original (SSD1306)
│   └── Sensor_ultrassonico_Display_SH1107.py    # Script único original (SH1107)
├── Imagens/
│   ├── 1. Frente hc-sr04 I2C.jpeg
│   ├── 2. Fundo hc-sr04 I2C.jpeg
│   ├── 3. Ligação M1 .jpeg
│   └── 4. Circuito montado.jpeg
├── main_ssd1306.py         # Entry point principal — display SSD1306
├── main_sh1107.py          # Entry point principal — display SH1107
└── README.md
```

- **`lib/`** — Drivers dos displays organizados como módulos importáveis.
- **`script/`** — Scripts monolíticos originais mantidos como referência.
- **`main_*.py`** — Entry points que importam os drivers de `lib/` e executam o loop de medição e exibição.

---

## Funcionamento

1. O scan I2C verifica a presença do sensor no endereço `0x57`.
2. A cada ciclo, o comando `0x01` é enviado para iniciar a medição.
3. Após 120 ms, o registrador `0xAF` é lido — 3 bytes que codificam a distância em micrômetros.
4. O valor é convertido para centímetros e exibido no OLED com uma zona de status:
   - **PERIGO** (≤ 15 cm)
   - **ALERTA** (≤ 30 cm)
   - **LIVRE** (> 30 cm ou sem eco)

---

## Referência

Este projeto foi baseado no artigo *TTB22 — The I2C Mode of the HC-SR04 Ultrasonic Sensor* do blog **PTSolutions**:

[https://ptsolns.com/blogs/tinker-thoughts/ttb22-the-i2c-mode-of-the-hc-sr04-ultrasonic-sensor](https://ptsolns.com/blogs/tinker-thoughts/ttb22-the-i2c-mode-of-the-hc-sr04-ultrasonic-sensor)
