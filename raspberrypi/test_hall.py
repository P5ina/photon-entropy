#!/usr/bin/env python3
"""Test script for Hall sensor (MAGNET module).

Usage:
    python test_hall.py           # Test Hall sensor
    python test_hall.py --mock    # Run in mock mode
    python test_hall.py --raw     # Show raw pin values continuously
"""

import argparse
import time

try:
    from gpiozero import Button
    HAS_GPIO = True
    GPIO_LIB = "gpiozero"
except ImportError:
    HAS_GPIO = False
    GPIO_LIB = None
    print("[WARN] gpiozero not found, running in mock mode")
    print("       Install with: pip install gpiozero lgpio")

from config import Config


def test_hall(config: Config, mock: bool = False, raw: bool = False):
    """Test the Hall effect sensor."""
    print("=" * 50)
    print("HALL SENSOR TEST (MAGNET MODULE)")
    print("=" * 50)

    hall_pin = config.hall_pin
    print(f"\nHall sensor pin: GPIO {hall_pin}")

    if mock or not HAS_GPIO:
        print("[MOCK MODE]")
        print("\nIn mock mode, cannot test actual Hall sensor.")
        return

    print(f"GPIO Library: {GPIO_LIB}")
    print("\nKY-003 Hall sensor: outputs LOW when magnet detected (active LOW)")
    print("Using gpiozero Button class (works reliably on Pi 5)")
    print("Bring a magnet close to the sensor. Press Ctrl+C to exit.\n")

    # Use Button class - works reliably on Pi 5 for active-low sensors
    # Hall sensor: HIGH = no magnet, LOW = magnet present
    # With pull_up=True: is_pressed=True when pin goes LOW (magnet detected)
    hall = Button(hall_pin, pull_up=True, bounce_time=0.05)
    magnet_count = 0
    last_state = None

    def on_magnet_detected():
        nonlocal magnet_count
        magnet_count += 1
        print(f"  ✓ MAGNET DETECTED! (count: {magnet_count})")

    def on_magnet_removed():
        print(f"    Magnet removed")

    hall.when_pressed = on_magnet_detected
    hall.when_released = on_magnet_removed

    print("-" * 50)

    # Show initial state
    # Note: pin.state is the actual GPIO level, is_pressed is the logical state
    initial_pressed = hall.is_pressed
    initial_pin_state = hall.pin.state
    print(f"Initial state: is_pressed={initial_pressed}, pin.state={initial_pin_state}")
    print(f"  → {'Magnet present!' if initial_pressed else 'No magnet'}")

    if raw:
        print("\nRAW MODE: Showing state changes...")
        print("-" * 50)
    else:
        print("\nWaiting for magnet...")
        print("-" * 50)

    try:
        while True:
            if raw:
                current = hall.is_pressed
                if current != last_state:
                    pin_val = hall.pin.state
                    status = "MAGNET DETECTED" if current else "No magnet"
                    print(f"  is_pressed={current}, pin.state={pin_val} → {status}")
                    last_state = current
            time.sleep(0.05)
    except KeyboardInterrupt:
        print(f"\n\nTest ended. Total magnet detections: {magnet_count}")
    finally:
        hall.close()


def main():
    parser = argparse.ArgumentParser(description="Test Hall sensor for Bomb Defusal game")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    parser.add_argument("--raw", action="store_true", help="Show raw pin values continuously")
    args = parser.parse_args()

    config = Config.from_env()
    mock = args.mock or not HAS_GPIO

    test_hall(config, mock, raw=args.raw)


if __name__ == "__main__":
    main()
