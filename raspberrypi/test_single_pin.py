#!/usr/bin/env python3
"""Test a single GPIO pin as button input.

Usage:
    python test_single_pin.py 19      # Test GPIO 19
    python test_single_pin.py 24      # Test GPIO 24
    python test_single_pin.py 4       # Test GPIO 4
"""

import sys
import time

try:
    from gpiozero import Button
    HAS_GPIO = True
except ImportError:
    print("gpiozero not found. Install with: pip install gpiozero lgpio")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: python test_single_pin.py <GPIO_NUMBER>")
    print("Example: python test_single_pin.py 19")
    sys.exit(1)

pin = int(sys.argv[1])

print(f"Testing GPIO {pin}")
print("Press Ctrl+C to exit\n")

# Try with pull_up=False (external pull-down resistor)
print(f"Mode: pull_up=False (expects external pull-down resistor)")
print("-" * 40)

try:
    btn = Button(pin, pull_up=False, bounce_time=0.05)

    def on_press():
        print(f"  PRESSED (GPIO {pin})")

    def on_release():
        print(f"  released (GPIO {pin})")

    btn.when_pressed = on_press
    btn.when_released = on_release

    print(f"Listening on GPIO {pin}...")
    print(f"Current state: {'PRESSED' if btn.is_pressed else 'not pressed'}")
    print()

    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nDone.")
    btn.close()
except Exception as e:
    print(f"Error: {e}")
