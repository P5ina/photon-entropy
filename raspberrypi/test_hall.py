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
    from gpiozero import DigitalInputDevice
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
    print("Bring a magnet close to the sensor. Press Ctrl+C to exit.\n")

    # Test with different pull configurations
    print("-" * 50)
    print("Testing pin with different configurations...")
    print("-" * 50)

    # Test 1: With pull-up
    hall_pullup = DigitalInputDevice(hall_pin, pull_up=True)
    val_pullup = hall_pullup.value
    hall_pullup.close()
    print(f"  With pull_up=True:  {val_pullup} ({'HIGH' if val_pullup else 'LOW'})")

    # Test 2: With pull-down
    hall_pulldown = DigitalInputDevice(hall_pin, pull_up=False)
    val_pulldown = hall_pulldown.value
    hall_pulldown.close()
    print(f"  With pull_up=False: {val_pulldown} ({'HIGH' if val_pulldown else 'LOW'})")

    # Diagnosis
    if val_pullup == 0 and val_pulldown == 0:
        print("\n  ⚠ Pin reads LOW with both pull-up and pull-down!")
        print("    → Signal wire is likely shorted to GND or sensor output is stuck LOW")
        print("    → Check wiring: disconnect signal wire and test again")
    elif val_pullup == 1 and val_pulldown == 1:
        print("\n  ⚠ Pin reads HIGH with both pull-up and pull-down!")
        print("    → Signal wire might be shorted to VCC")
    elif val_pullup == 1 and val_pulldown == 0:
        print("\n  ✓ Pin responds to pull resistors correctly (floating)")
        print("    → Sensor may not be connected or powered")

    print("-" * 50)

    # Use DigitalInputDevice for clearer control
    # pull_up=True provides internal pull-up resistor
    # The sensor pulls LOW when magnet is detected
    hall = DigitalInputDevice(hall_pin, pull_up=True, bounce_time=0.05)
    magnet_count = 0
    last_value = None

    def on_activated():
        # DigitalInputDevice fires when_activated when value goes HIGH
        print(f"    Magnet removed (pin went HIGH)")

    def on_deactivated():
        # Fires when value goes LOW - magnet detected!
        nonlocal magnet_count
        magnet_count += 1
        print(f"  ✓ MAGNET DETECTED! (pin went LOW, count: {magnet_count})")

    hall.when_activated = on_activated
    hall.when_deactivated = on_deactivated

    # Show initial state
    initial_value = hall.value
    print(f"Continuing with pull_up=True. Current value: {initial_value}")

    if raw:
        print("\nRAW MODE: Showing continuous pin values...")
        print("-" * 50)
    else:
        print("Waiting for magnet...")
        print("-" * 50)

    try:
        while True:
            if raw:
                current = hall.value
                if current != last_value:
                    status = "HIGH (no magnet)" if current else "LOW (MAGNET!)"
                    print(f"  Pin value: {current} - {status}")
                    last_value = current
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
