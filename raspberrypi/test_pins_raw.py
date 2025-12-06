#!/usr/bin/env python3
"""Raw GPIO pin test using lgpio directly.

Usage:
    python test_pins_raw.py
    python test_pins_raw.py 16    # Test specific pin
"""

import sys
import time

try:
    import lgpio
    HAS_LGPIO = True
except ImportError:
    HAS_LGPIO = False
    print("lgpio not found. Install with: pip install lgpio")
    exit(1)

# All usable GPIO pins on Raspberry Pi (BCM numbering)
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
    16: "Hall Sensor",
    18: "Buzzer",
}

# lgpio flags
INPUT = 0
PULL_UP = 1 << 16      # lgpio.SET_PULL_UP
PULL_DOWN = 1 << 17    # lgpio.SET_PULL_DOWN
PULL_NONE = 1 << 18    # lgpio.SET_PULL_NONE


def test_pin_lgpio(h, pin: int) -> tuple[int, int, int, str]:
    """Test a single pin using lgpio directly.

    Returns: (val_pullup, val_pulldown, val_none, status)
    """
    try:
        # Test with pull-up
        lgpio.gpio_claim_input(h, pin, PULL_UP)
        time.sleep(0.01)
        val_up = lgpio.gpio_read(h, pin)
        lgpio.gpio_free(h, pin)

        # Test with pull-down
        lgpio.gpio_claim_input(h, pin, PULL_DOWN)
        time.sleep(0.01)
        val_down = lgpio.gpio_read(h, pin)
        lgpio.gpio_free(h, pin)

        # Test with no pull (floating)
        lgpio.gpio_claim_input(h, pin, PULL_NONE)
        time.sleep(0.01)
        val_none = lgpio.gpio_read(h, pin)
        lgpio.gpio_free(h, pin)

        # Determine status
        if val_up == 1 and val_down == 0:
            status = "OK (responds to pull)"
        elif val_up == 0 and val_down == 0 and val_none == 0:
            status = "STUCK LOW"
        elif val_up == 1 and val_down == 1 and val_none == 1:
            status = "STUCK HIGH"
        elif val_up == val_down == val_none:
            status = f"STUCK at {val_up}"
        else:
            status = "OK (partial response)"

        return val_up, val_down, val_none, status
    except Exception as e:
        return -1, -1, -1, f"ERROR: {e}"


def test_single_pin_interactive(pin: int):
    """Interactive test for a single pin."""
    print(f"Interactive test for GPIO {pin}")
    print("=" * 50)

    h = lgpio.gpiochip_open(0)

    # Claim as input with pull-up
    lgpio.gpio_claim_input(h, pin, PULL_UP)

    print(f"Pin {pin} configured as INPUT with PULL_UP")
    print("Current readings (Ctrl+C to exit):")
    print("-" * 50)

    last_val = None
    try:
        while True:
            val = lgpio.gpio_read(h, pin)
            if val != last_val:
                print(f"  GPIO {pin} = {val} ({'HIGH' if val else 'LOW'})")
                last_val = val
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nDone.")
    finally:
        lgpio.gpio_free(h, pin)
        lgpio.gpiochip_close(h)


def main():
    # Check for specific pin argument
    if len(sys.argv) > 1:
        pin = int(sys.argv[1])
        test_single_pin_interactive(pin)
        return

    print("=" * 70)
    print("GPIO PIN TEST (using lgpio directly)")
    print("=" * 70)

    h = lgpio.gpiochip_open(0)
    print(f"Opened GPIO chip 0")
    print()

    print("-" * 70)
    print(f"{'GPIO':<6} {'PullUp':<7} {'PullDn':<7} {'Float':<7} {'Status':<22} {'Usage'}")
    print("-" * 70)

    available = []
    problematic = []

    for pin in ALL_GPIO_PINS:
        usage = USED_PINS.get(pin, "")
        val_up, val_down, val_none, status = test_pin_lgpio(h, pin)

        if val_up == -1:
            print(f"{pin:<6} {'ERR':<7} {'ERR':<7} {'ERR':<7} {status:<22} {usage}")
            problematic.append(pin)
        else:
            print(f"{pin:<6} {val_up:<7} {val_down:<7} {val_none:<7} {status:<22} {usage}")

            if "OK" in status and pin not in USED_PINS:
                available.append(pin)
            elif "STUCK" in status or "ERROR" in status:
                problematic.append(pin)

    lgpio.gpiochip_close(h)

    print("-" * 70)

    print(f"\nAVAILABLE PINS (not used, responding correctly):")
    if available:
        print(f"  GPIO: {', '.join(map(str, available))}")
        print(f"\n  Recommended for Hall sensor: GPIO {available[0]}")
    else:
        print("  None found!")

    if problematic:
        print(f"\nPROBLEMATIC PINS:")
        print(f"  GPIO: {', '.join(map(str, problematic))}")

    print()


if __name__ == "__main__":
    main()
