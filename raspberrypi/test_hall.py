#!/usr/bin/env python3
"""Test script for Hall sensor (MAGNET module).

Usage:
    python test_hall.py           # Test Hall sensor
    python test_hall.py --mock    # Run in mock mode
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


def test_hall(config: Config, mock: bool = False):
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
    print("\nBring a magnet close to the sensor. Press Ctrl+C to exit.\n")

    # Hall sensor is active LOW (outputs LOW when magnet detected)
    hall = Button(hall_pin, pull_up=True)
    magnet_count = 0

    def on_magnet_detected():
        nonlocal magnet_count
        magnet_count += 1
        print(f"  ✓ MAGNET DETECTED! (count: {magnet_count})")

    def on_magnet_removed():
        print(f"    Magnet removed")

    hall.when_pressed = on_magnet_detected
    hall.when_released = on_magnet_removed

    print("-" * 50)
    print("Waiting for magnet...")
    print("-" * 50)

    # Show initial state
    if hall.is_pressed:
        print("  [!] Magnet already present at start")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\n\nTest ended. Total magnet detections: {magnet_count}")
    finally:
        hall.close()


def main():
    parser = argparse.ArgumentParser(description="Test Hall sensor for Bomb Defusal game")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    args = parser.parse_args()

    config = Config.from_env()
    mock = args.mock or not HAS_GPIO

    test_hall(config, mock)


if __name__ == "__main__":
    main()
