# Hardware Components — Bomb Defusal Game

## Overview

This document lists all hardware components required to build the physical "bomb" controller for the Bomb Defusal game.

---

## Core Components

| Component | Quantity | Purpose | Notes |
|-----------|----------|---------|-------|
| Raspberry Pi 4/5 | 1 | Main controller | Any model with GPIO and I2C |
| LCD 16x2 I2C | 1 | Display timer, codes, hints | I2C address: 0x27 or 0x3F |
| Breadboard | 1-2 | Prototyping | 830 points recommended |
| Jumper wires | ~40 | Connections | Male-to-female, male-to-male |

---

## Sensors & Modules (from 37 KY Sensor Kit)

### Module: WIRES (4 buttons + 4 LEDs)

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| Button 1 (Red) | - | GPIO 19 | Tactile button |
| Button 2 (Blue) | - | GPIO 26 | Tactile button |
| Button 3 (Green) | - | GPIO 21 | Tactile button |
| Button 4 (Yellow) | - | GPIO 15 | Tactile button |
| LED 1 (Red) | - | GPIO 25 | Wire color indicator |
| LED 2 (Blue) | - | GPIO 8 | Wire color indicator |
| LED 3 (Green) | - | GPIO 7 | Wire color indicator |
| LED 4 (Yellow) | - | GPIO 1 | Wire color indicator |

> These are additional components — not from the KY kit. See Shopping List below.

### Module: SIMON (memory sequence)

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| RGB LED | KY-016 or KY-009 | R: GPIO 17, G: GPIO 27, B: GPIO 22 | Shows color sequence |

### Module: MAGNET (Hall sensor)

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| Hall Sensor | KY-003 or KY-024 | GPIO 16 | Detects magnet proximity |
| Magnet | - | - | Any small magnet as "key" |

### Output: Feedback

| Component | KY Module | GPIO | Description |
|-----------|-----------|------|-------------|
| Buzzer (Active) | KY-012 | GPIO 18 | Tick-tock, errors, explosion |
| RGB LED (Status) | KY-016 | Shared with SIMON | Game status indicator |

---

## GPIO Pinout Summary

```
Raspberry Pi GPIO Layout (Active pins marked with ←)
─────────────────────────────────────────────────────
                   3.3V  [1]  [2]  5V
   LCD SDA (I2C)   GPIO2 [3]  [4]  5V
   LCD SCL (I2C)   GPIO3 [5]  [6]  GND
                   GPIO4 [7]  [8]  GPIO14
   Button 4         GND  [9]  [10] GPIO15  ← Button 4 (Yellow)
   RGB LED Red    GPIO17 [11] [12] GPIO18  ← Buzzer (PWM)
   RGB LED Green  GPIO27 [13] [14] GND
   RGB LED Blue   GPIO22 [15] [16] GPIO23
                   3.3V  [17] [18] GPIO24
                  GPIO10 [19] [20] GND
                   GPIO9 [21] [22] GPIO25  ← LED 1 (Red)
                  GPIO11 [23] [24] GPIO8   ← LED 2 (Blue)
                    GND  [25] [26] GPIO7   ← LED 3 (Green)
                   GPIO0 [27] [28] GPIO1   ← LED 4 (Yellow)
                   GPIO5 [29] [30] GND
                   GPIO6 [31] [32] GPIO12
                  GPIO13 [33] [34] GND
   Button 1       GPIO19 [35] [36] GPIO16  ← Hall Sensor
   Button 2       GPIO26 [37] [38] GPIO20
   Button 3         GND  [39] [40] GPIO21  ← Button 3 (Green)
─────────────────────────────────────────────────────

Used GPIO Pins:
  WIRES module:
    - Buttons: GPIO 19, 26, 21, 15
    - LEDs:    GPIO 25, 8, 7, 1

  SIMON module:
    - RGB LED: GPIO 17 (R), 27 (G), 22 (B)

  MAGNET module:
    - Hall Sensor: GPIO 16

  Output:
    - Buzzer: GPIO 18 (PWM)

  I2C (LCD):
    - SDA: GPIO 2
    - SCL: GPIO 3
    - Address: 0x27 or 0x3F
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
| Small Magnet | 1 | $1 | For Hall sensor module |

**Total additional cost:** ~$5-8

### Optional (already have from KY kit)

| Item | From KY Kit |
|------|-------------|
| KY-016 RGB LED | ✓ |
| KY-003 Hall Sensor | ✓ |
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
Each button with internal pull-up (no external resistor needed):

GPIO Pin ──────── Button ──────── GND

Button pressed  = LOW (GND)
Button released = HIGH (internal pull-up)
```

### LEDs (WIRES module indicators)

```
Each LED with current limiting resistor:

GPIO Pin ────[220Ω]──── LED (+) ──── LED (-) ──── GND

GPIO HIGH = LED ON
GPIO LOW  = LED OFF
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

### Hall Sensor (KY-003)

```
KY-003          Raspberry Pi
─────────────────────────────────
GND  ─────────────► GND
VCC  ─────────────► 3.3V
SIG  ─────────────► GPIO 16
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

## Optional Enhancements

| Component | Purpose | Notes |
|-----------|---------|-------|
| 7-Segment Display | Show countdown timer | More dramatic than LCD |
| WS2812B LED Strip | Multiple indicators | Addressable RGB |
| Vibration Motor | Haptic feedback | On strikes/explosion |
| Speaker | Sound effects | Better audio than buzzer |
| Enclosure/Box | Physical bomb prop | 3D printed or cardboard |
