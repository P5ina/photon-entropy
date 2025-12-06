#!/usr/bin/env python3
"""Test script for touch sensor (SIMON module).

Usage:
    python test_touch.py           # Test touch sensor
    python test_touch.py --mock    # Run in mock mode
"""

import argparse
import time

try:
    from gpiozero import Button, TonalBuzzer
    HAS_GPIO = True
    GPIO_LIB = "gpiozero"
except ImportError:
    HAS_GPIO = False
    GPIO_LIB = None
    print("[WARN] gpiozero not found, running in mock mode")
    print("       Install with: pip install gpiozero lgpio")

from config import Config


def test_touch(config: Config, mock: bool = False):
    """Test the touch sensor."""
    print("=" * 50)
    print("TOUCH SENSOR TEST (SIMON MODULE)")
    print("=" * 50)

    touch_pin = config.touch_pin
    buzzer_pin = config.buzzer_pin
    print(f"\nTouch sensor pin: GPIO {touch_pin}")
    print(f"Buzzer pin: GPIO {buzzer_pin}")

    if mock or not HAS_GPIO:
        print("[MOCK MODE]")
        print("\nIn mock mode, cannot test actual touch sensor.")
        return

    print(f"GPIO Library: {GPIO_LIB}")
    print("\nTouch the sensor. Press Ctrl+C to exit.\n")

    touch = Button(touch_pin, pull_up=False)
    buzzer = TonalBuzzer(buzzer_pin)
    touch_count = 0

    def beep():
        """Short beep on touch."""
        buzzer.play(880)  # A5 note
        time.sleep(0.05)
        buzzer.stop()

    def on_touch():
        nonlocal touch_count
        touch_count += 1
        beep()
        print(f"  ✓ TOUCH detected! (count: {touch_count})")

    def on_release():
        print(f"    Released")

    touch.when_pressed = on_touch
    touch.when_released = on_release

    print("-" * 50)
    print("Waiting for touches...")
    print("-" * 50)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\n\nTest ended. Total touches: {touch_count}")
    finally:
        touch.close()
        buzzer.close()


def main():
    parser = argparse.ArgumentParser(description="Test touch sensor for Bomb Defusal game")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    args = parser.parse_args()

    config = Config.from_env()
    mock = args.mock or not HAS_GPIO

    test_touch(config, mock)


if __name__ == "__main__":
    main()
