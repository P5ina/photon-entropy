# Hardware Components — Bomb Defusal Game

## Overview

This document lists all hardware components required to build the physical "bomb" controller for the Bomb Defusal game.

---

## Core Components

| Component | Quantity | Purpose | Notes |
|-----------|----------|---------|-------|
| Raspberry Pi 4/5 | 1 | Main controller | Any model with GPIO and I2C |
| LCD 16x2 I2C | 1 | Display timer, codes, hints | I2C address: 0x27 or 0x3F |
| ADS1115 ADC | 1 | Analog sensors (future) | I2C address: 0x48 |
| Breadboard | 1-2 | Prototyping | 830 points recommended |
| Jumper wires | ~40 | Connections | Male-to-female, male-to-male |
| Resistors 10kΩ | 4 | Pull-down for buttons | For WIRES module |

---

## Sensors & Modules (from 37 KY Sensor Kit)

### Module: WIRES (4 buttons + 4 LEDs)

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| Button 1 (Red) | - | GPIO 19 | Tactile button |
| Button 2 (Green) | - | GPIO 26 | Tactile button |
| Button 3 (Blue) | - | GPIO 21 | Tactile button |
| Button 4 (Yellow) | - | GPIO 20 | Tactile button |
| LED 1 (Red) | - | GPIO 25 | Wire color indicator |
| LED 2 (Green) | - | GPIO 8 | Wire color indicator |
| LED 3 (Blue) | - | GPIO 7 | Wire color indicator |
| LED 4 (Yellow) | - | GPIO 1 | Wire color indicator |

> These are additional components — not from the KY kit. See Shopping List below.

### Module: KEYPAD (rotary encoder)

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| Rotary Encoder | KY-040 | CLK: GPIO 5, DT: GPIO 6, SW: GPIO 13 | Enter 3-digit code |

### Module: SIMON (memory sequence)

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| RGB LED | KY-016 or KY-009 | R: GPIO 17, G: GPIO 27, B: GPIO 22 | Shows color sequence |
| Touch Sensor | KY-036 | GPIO 12 | Player input |

### Module: MAGNET (Hall sensor)

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| Hall Sensor | KY-003 or KY-024 | GPIO 16 | Detects magnet proximity |
| Magnet | - | - | Any small magnet as "key" |

### Module: STABILITY (tilt detection)

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| Tilt Sensor | KY-017 or KY-020 | GPIO 24 | Detects shaking/tilting |

### Output: Feedback

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| Buzzer (Active) | KY-012 | GPIO 18 | Tick-tock, errors, explosion |
| RGB LED (Status) | KY-016 | Shared with SIMON | Game status indicator |

---

## GPIO Pinout Summary

```
Raspberry Pi GPIO Layout
─────────────────────────────────────────────────────
                    3.3V  [1]  [2]  5V
          LCD SDA   GPIO2 [3]  [4]  5V
          LCD SCL   GPIO3 [5]  [6]  GND
                   GPIO4  [7]  [8]  GPIO8   ← LED 2 (Green)
                    GND   [9]  [10] GPIO15
         RGB Red   GPIO17 [11] [12] GPIO18  ← Buzzer (PWM)
        RGB Green  GPIO27 [13] [14] GND
         RGB Blue  GPIO22 [15] [16] GPIO23
                    3.3V  [17] [18] GPIO24  ← Tilt Sensor
                   GPIO10 [19] [20] GND
                   GPIO9  [21] [22] GPIO25  ← LED 1 (Red)
                   GPIO11 [23] [24] GPIO7   ← LED 3 (Blue)
                    GND   [25] [26] GPIO1   ← LED 4 (Yellow)
                   GPIO0  [27] [28] GPIO1
          Rotary CLK GPIO5 [29] [30] GND
          Rotary DT  GPIO6 [31] [32] GPIO12  ← Touch Sensor
        Rotary SW   GPIO13 [33] [34] GND
        Button 1   GPIO19 [35] [36] GPIO16  ← Hall Sensor
        Button 2   GPIO26 [37] [38] GPIO20  ← Button 4
                    GND   [39] [40] GPIO21  ← Button 3
─────────────────────────────────────────────────────

I2C Devices:
  - LCD 16x2:  SDA=GPIO2, SCL=GPIO3, Address=0x27/0x3F
  - ADS1115:   SDA=GPIO2, SCL=GPIO3, Address=0x48

PWM Pins (for RGB LED):
  - Red:   GPIO 17
  - Green: GPIO 27
  - Blue:  GPIO 22
```

---

## Shopping List

### Required (not in KY-037 kit)

| Item | Quantity | Approx. Price | Notes |
|------|----------|---------------|-------|
| Tactile Push Buttons 6x6mm | 4 | $1-2 | For WIRES module |
| LED 5mm (Red) | 1 | $0.50 | Wire indicator |
| LED 5mm (Green) | 1 | $0.50 | Wire indicator |
| LED 5mm (Blue) | 1 | $0.50 | Wire indicator |
| LED 5mm (Yellow) | 1 | $0.50 | Wire indicator |
| Resistors 220Ω | 4 | $0.50 | Current limiting for LEDs |
| Resistors 10kΩ | 4 | $0.50 | Pull-down for buttons |
| Small Magnet | 1 | $1 | For Hall sensor module |

**Total additional cost:** ~$5-8

### Optional (already have from KY kit)

| Item | From KY Kit |
|------|-------------|
| KY-040 Rotary Encoder | ✓ |
| KY-016 RGB LED | ✓ |
| KY-036 Touch Sensor | ✓ |
| KY-003 Hall Sensor | ✓ |
| KY-017 Tilt Sensor | ✓ |
| KY-012 Buzzer | ✓ |

---

## Wiring Diagrams

### LCD 16x2 (I2C)

```
LCD I2C Backpack    Raspberry Pi
─────────────────────────────────
VCC  ─────────────► 5V (Pin 2)
GND  ─────────────► GND (Pin 6)
SDA  ─────────────► GPIO 2 (Pin 3)
SCL  ─────────────► GPIO 3 (Pin 5)
```

### Buttons (WIRES module)

```
Each button with pull-down resistor:

3.3V ────┬──────── Button ──────── GPIO Pin
         │
        [10kΩ]
         │
        GND

Button pressed  = HIGH (3.3V)
Button released = LOW (GND via resistor)
```

### LEDs (WIRES module indicators)

```
Each LED with current limiting resistor:

GPIO Pin ────[220Ω]──── LED (+) ──── LED (-) ──── GND

GPIO HIGH = LED ON
GPIO LOW  = LED OFF
```

### Rotary Encoder (KY-040)

```
KY-040          Raspberry Pi
─────────────────────────────────
GND  ─────────────► GND
+    ─────────────► 3.3V
SW   ─────────────► GPIO 13
DT   ─────────────► GPIO 6
CLK  ─────────────► GPIO 5
```

### RGB LED (KY-016)

```
KY-016          Raspberry Pi
─────────────────────────────────
GND  ─────────────► GND
R    ─────────────► GPIO 17
G    ─────────────► GPIO 27
B    ─────────────► GPIO 22
```

### Buzzer (KY-012)

```
KY-012          Raspberry Pi
─────────────────────────────────
GND  ─────────────► GND
S    ─────────────► GPIO 18 (PWM)
```

### Touch Sensor (KY-036)

```
KY-036          Raspberry Pi
─────────────────────────────────
GND  ─────────────► GND
VCC  ─────────────► 3.3V
SIG  ─────────────► GPIO 12
```

### Hall Sensor (KY-003)

```
KY-003          Raspberry Pi
─────────────────────────────────
GND  ─────────────► GND
VCC  ─────────────► 3.3V
SIG  ─────────────► GPIO 16
```

### Tilt Sensor (KY-017)

```
KY-017          Raspberry Pi
─────────────────────────────────
GND  ─────────────► GND
VCC  ─────────────► 3.3V
SIG  ─────────────► GPIO 24
```

---

## Power Requirements

| Component | Current (mA) |
|-----------|--------------|
| Raspberry Pi 4 | 600-1200 |
| LCD 16x2 I2C | 20-40 |
| RGB LED | 20-60 |
| 4× Wire LEDs | 40-80 |
| Buzzer | 25-30 |
| Sensors (total) | 10-20 |
| **Total** | **~750-1450 mA** |

**Recommended:** 5V 3A power supply for Raspberry Pi

---

## Testing Checklist

Before assembling the full setup, test each component individually:

- [ ] LCD displays text via I2C (`i2cdetect -y 1` shows address)
- [ ] Each button registers press/release on correct GPIO
- [ ] Each wire LED lights up on correct GPIO
- [ ] Rotary encoder counts up/down correctly
- [ ] RGB LED shows all colors (R, G, B, mixed)
- [ ] Buzzer produces sound on GPIO 18
- [ ] Touch sensor detects finger
- [ ] Hall sensor detects magnet
- [ ] Tilt sensor changes state when tilted

### Test Commands

```bash
# Check I2C devices
i2cdetect -y 1

# Read GPIO state
gpio readall          # WiringPi
pinout                # RPi.GPIO

# Test button (Python)
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
print('Button 1 state:', GPIO.input(19))
"

# Test LED (Python)
python3 -c "
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.OUT)
GPIO.output(25, GPIO.HIGH)
time.sleep(1)
GPIO.output(25, GPIO.LOW)
GPIO.cleanup()
print('LED 1 blinked')
"
```

---

## Optional Enhancements

| Component | Purpose | Notes |
|-----------|---------|-------|
| 7-Segment Display | Show countdown timer | More dramatic than LCD |
| WS2812B LED Strip | Multiple indicators | Addressable RGB |
| Vibration Motor | Haptic feedback | On strikes/explosion |
| Speaker | Sound effects | Better audio than buzzer |
| Enclosure/Box | Physical bomb prop | 3D printed or cardboard |
