#!/usr/bin/env python3
"""Test all GPIO pins to find available ones.

Usage:
    python test_pins.py
"""

import time

try:
    from gpiozero import DigitalInputDevice
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    print("gpiozero not found. Install with: pip install gpiozero lgpio")
    exit(1)

# All usable GPIO pins on Raspberry Pi (BCM numbering)
# Excluding: 0, 1 (I2C EEPROM), 2, 3 (I2C), 14, 15 (UART)
ALL_GPIO_PINS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

# Pins currently used by the project
USED_PINS = {
    19: "Wire Button 1",
    26: "Wire Button 2",
    21: "Wire Button 3",
    15: "Wire Button 4",
    25: "Wire LED 1",
    8: "Wire LED 2",
    7: "Wire LED 3",
    1: "Wire LED 4",
    17: "RGB Red",
    27: "RGB Green",
    22: "RGB Blue",
    12: "Touch Sensor",
    16: "Hall Sensor (current)",
    18: "Buzzer",
}

def test_pin(pin: int) -> tuple[int, int, str]:
    """Test a single pin with pull-up and pull-down.

    Returns: (value_with_pullup, value_with_pulldown, status)
    """
    try:
        # Test with pull-up
        dev_up = DigitalInputDevice(pin, pull_up=True)
        val_up = dev_up.value
        dev_up.close()
        time.sleep(0.05)

        # Test with pull-down
        dev_down = DigitalInputDevice(pin, pull_up=False)
        val_down = dev_down.value
        dev_down.close()
        time.sleep(0.05)

        # Determine status
        if val_up == 1 and val_down == 0:
            status = "OK (floating)"
        elif val_up == 0 and val_down == 0:
            status = "STUCK LOW (shorted to GND?)"
        elif val_up == 1 and val_down == 1:
            status = "STUCK HIGH (shorted to VCC?)"
        else:
            status = "OK (responds to pull)"

        return val_up, val_down, status
    except Exception as e:
        return -1, -1, f"ERROR: {e}"


def main():
    print("=" * 60)
    print("GPIO PIN AVAILABILITY TEST")
    print("=" * 60)
    print("\nTesting all GPIO pins with pull-up and pull-down resistors.")
    print("A 'floating' pin responds correctly to internal pull resistors.")
    print()

    print("-" * 60)
    print(f"{'GPIO':<6} {'Pull-Up':<8} {'Pull-Down':<10} {'Status':<20} {'Usage'}")
    print("-" * 60)

    available = []
    problematic = []

    for pin in ALL_GPIO_PINS:
        usage = USED_PINS.get(pin, "")
        val_up, val_down, status = test_pin(pin)

        if val_up == -1:
            print(f"{pin:<6} {'ERR':<8} {'ERR':<10} {status:<20} {usage}")
            problematic.append(pin)
        else:
            print(f"{pin:<6} {val_up:<8} {val_down:<10} {status:<20} {usage}")

            if "OK" in status and pin not in USED_PINS:
                available.append(pin)
            elif "STUCK" in status:
                problematic.append(pin)

    print("-" * 60)

    print(f"\nAVAILABLE PINS (not used, responding correctly):")
    if available:
        print(f"  GPIO: {', '.join(map(str, available))}")
        print(f"\n  Recommended for Hall sensor: GPIO {available[0]}")
    else:
        print("  None found!")

    if problematic:
        print(f"\nPROBLEMATIC PINS (stuck or error):")
        print(f"  GPIO: {', '.join(map(str, problematic))}")

    print()


if __name__ == "__main__":
    main()
