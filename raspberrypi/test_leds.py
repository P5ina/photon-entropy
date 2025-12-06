#!/usr/bin/env python3
"""Test script for all LEDs (Wire LEDs + RGB LED).

Usage:
    python test_leds.py              # Test all LEDs
    python test_leds.py --wire       # Test wire LEDs only
    python test_leds.py --rgb        # Test RGB LED only
    python test_leds.py --mock       # Run in mock mode (no real hardware)
"""

import argparse
import time
import sys

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("[WARN] RPi.GPIO not found, running in mock mode")

from config import Config


def setup_gpio():
    """Setup GPIO mode."""
    if HAS_GPIO:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)


def cleanup_gpio():
    """Cleanup GPIO."""
    if HAS_GPIO:
        GPIO.cleanup()


def test_wire_leds(config: Config, mock: bool = False):
    """Test the 4 wire indicator LEDs."""
    print("\n" + "=" * 50)
    print("WIRE LEDs TEST")
    print("=" * 50)

    led_pins = config.wire_leds
    colors = ["Red", "Blue", "Green", "Yellow"]

    if mock or not HAS_GPIO:
        print("[MOCK MODE]")
        for i, (pin, color) in enumerate(zip(led_pins, colors)):
            print(f"  LED {i+1} ({color}) - GPIO {pin}: ON")
            time.sleep(0.5)
            print(f"  LED {i+1} ({color}) - GPIO {pin}: OFF")
        print("\n[MOCK] All wire LEDs blink simultaneously")
        return

    # Setup pins
    for pin in led_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    print("\nTesting each LED individually...")
    for i, (pin, color) in enumerate(zip(led_pins, colors)):
        print(f"  LED {i+1} ({color}) - GPIO {pin}...", end=" ", flush=True)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(pin, GPIO.LOW)
        print("OK")
        time.sleep(0.3)

    print("\nBlinking all LEDs together (3 times)...")
    for _ in range(3):
        for pin in led_pins:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.3)
        for pin in led_pins:
            GPIO.output(pin, GPIO.LOW)
        time.sleep(0.3)

    print("\nWave pattern...")
    for _ in range(2):
        for pin in led_pins:
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.15)
            GPIO.output(pin, GPIO.LOW)
        for pin in reversed(led_pins):
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.15)
            GPIO.output(pin, GPIO.LOW)

    print("\nWire LEDs test complete!")


def test_rgb_led(config: Config, mock: bool = False):
    """Test the RGB LED."""
    print("\n" + "=" * 50)
    print("RGB LED TEST")
    print("=" * 50)

    r_pin = config.rgb_red
    g_pin = config.rgb_green
    b_pin = config.rgb_blue

    colors = [
        ("Red", (255, 0, 0)),
        ("Green", (0, 255, 0)),
        ("Blue", (0, 0, 255)),
        ("Yellow", (255, 255, 0)),
        ("Cyan", (0, 255, 255)),
        ("Magenta", (255, 0, 255)),
        ("White", (255, 255, 255)),
        ("Orange", (255, 128, 0)),
    ]

    if mock or not HAS_GPIO:
        print("[MOCK MODE]")
        print(f"  RGB pins - R: GPIO {r_pin}, G: GPIO {g_pin}, B: GPIO {b_pin}")
        for name, (r, g, b) in colors:
            print(f"  {name}: RGB({r}, {g}, {b})")
            time.sleep(0.5)
        print("\n[MOCK] Rainbow cycle complete")
        return

    # Setup pins with PWM
    GPIO.setup(r_pin, GPIO.OUT)
    GPIO.setup(g_pin, GPIO.OUT)
    GPIO.setup(b_pin, GPIO.OUT)

    pwm_r = GPIO.PWM(r_pin, 1000)
    pwm_g = GPIO.PWM(g_pin, 1000)
    pwm_b = GPIO.PWM(b_pin, 1000)

    pwm_r.start(0)
    pwm_g.start(0)
    pwm_b.start(0)

    def set_color(r, g, b):
        pwm_r.ChangeDutyCycle(r * 100 / 255)
        pwm_g.ChangeDutyCycle(g * 100 / 255)
        pwm_b.ChangeDutyCycle(b * 100 / 255)

    print(f"\nRGB pins - R: GPIO {r_pin}, G: GPIO {g_pin}, B: GPIO {b_pin}")
    print("\nTesting colors...")

    for name, (r, g, b) in colors:
        print(f"  {name}...", end=" ", flush=True)
        set_color(r, g, b)
        time.sleep(1)
        print("OK")

    print("\nFading through colors...")
    # Fade red to green
    for i in range(100):
        set_color(255 - int(i * 2.55), int(i * 2.55), 0)
        time.sleep(0.02)

    # Fade green to blue
    for i in range(100):
        set_color(0, 255 - int(i * 2.55), int(i * 2.55))
        time.sleep(0.02)

    # Fade blue to red
    for i in range(100):
        set_color(int(i * 2.55), 0, 255 - int(i * 2.55))
        time.sleep(0.02)

    # Turn off
    set_color(0, 0, 0)

    # Cleanup PWM
    pwm_r.stop()
    pwm_g.stop()
    pwm_b.stop()

    print("\nRGB LED test complete!")


def main():
    parser = argparse.ArgumentParser(description="Test LEDs for Bomb Defusal game")
    parser.add_argument("--wire", action="store_true", help="Test wire LEDs only")
    parser.add_argument("--rgb", action="store_true", help="Test RGB LED only")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    args = parser.parse_args()

    config = Config.from_env()
    mock = args.mock or not HAS_GPIO

    print("=" * 50)
    print("LED TEST SCRIPT")
    print("=" * 50)
    print(f"Mode: {'MOCK' if mock else 'HARDWARE'}")

    if not mock:
        setup_gpio()

    try:
        # Determine which tests to run
        test_all = not args.wire and not args.rgb

        if test_all or args.wire:
            test_wire_leds(config, mock)

        if test_all or args.rgb:
            test_rgb_led(config, mock)

        print("\n" + "=" * 50)
        print("ALL TESTS COMPLETE!")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        if not mock:
            cleanup_gpio()


if __name__ == "__main__":
    main()
