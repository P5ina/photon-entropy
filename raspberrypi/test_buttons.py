#!/usr/bin/env python3
"""Test script for buttons (WIRES module).

Buttons use internal pull-up resistor:
  GPIO -> Button -> GND (no external resistor needed)

Usage:
    python test_buttons.py           # Test all 4 buttons
    python test_buttons.py --mock    # Run in mock mode
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


def test_buttons(config: Config, mock: bool = False):
    """Test the 4 wire buttons."""
    print("=" * 50)
    print("BUTTONS TEST (WIRES MODULE)")
    print("=" * 50)

    button_pins = config.wire_buttons
    colors = ["Red", "Blue", "Green", "Yellow"]

    print("\nWiring: GPIO -> Button -> GND (internal pull-up)")
    print("        No external resistor needed\n")

    if mock or not HAS_GPIO:
        print("[MOCK MODE]")
        print("\nButton pins configuration:")
        for i, (pin, color) in enumerate(zip(button_pins, colors)):
            print(f"  Button {i+1} ({color}): GPIO {pin}")
        print("\nIn mock mode, cannot test actual button presses.")
        return

    print(f"GPIO Library: {GPIO_LIB}")
    print("\nPress each button to test. Press Ctrl+C to exit.\n")

    buttons = []
    for i, (pin, color) in enumerate(zip(button_pins, colors)):
        # pull_up=True: button connects GPIO to GND when pressed
        btn = Button(pin, pull_up=True, bounce_time=0.05)
        btn.when_pressed = lambda c=color, p=pin: print(f"  ✓ Button {c} (GPIO {p}) PRESSED")
        btn.when_released = lambda c=color, p=pin: print(f"    Button {c} (GPIO {p}) released")
        buttons.append(btn)
        print(f"  Listening on GPIO {pin} ({color})...")

    print("\n" + "-" * 50)
    print("Waiting for button presses...")
    print("-" * 50)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nTest ended.")
    finally:
        for btn in buttons:
            btn.close()


def main():
    parser = argparse.ArgumentParser(description="Test buttons for Bomb Defusal game")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    args = parser.parse_args()

    config = Config.from_env()
    mock = args.mock or not HAS_GPIO

    test_buttons(config, mock)


if __name__ == "__main__":
    main()
