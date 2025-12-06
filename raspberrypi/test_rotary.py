#!/usr/bin/env python3
"""Test script for rotary encoder (KEYPAD module).

Usage:
    python test_rotary.py           # Test rotary encoder
    python test_rotary.py --mock    # Run in mock mode
"""

import argparse
import time

try:
    from gpiozero import RotaryEncoder, Button
    HAS_GPIO = True
    GPIO_LIB = "gpiozero"
except ImportError:
    HAS_GPIO = False
    GPIO_LIB = None
    print("[WARN] gpiozero not found, running in mock mode")
    print("       Install with: pip install gpiozero lgpio")

from config import Config


def test_rotary(config: Config, mock: bool = False):
    """Test the rotary encoder."""
    print("=" * 50)
    print("ROTARY ENCODER TEST (KEYPAD MODULE)")
    print("=" * 50)

    clk_pin = config.rotary_clk
    dt_pin = config.rotary_dt
    sw_pin = config.rotary_sw

    print(f"\nPins: CLK=GPIO {clk_pin}, DT=GPIO {dt_pin}, SW=GPIO {sw_pin}")

    if mock or not HAS_GPIO:
        print("[MOCK MODE]")
        print("\nIn mock mode, cannot test actual rotary encoder.")
        return

    print(f"GPIO Library: {GPIO_LIB}")
    print("\nRotate the encoder and press the button. Press Ctrl+C to exit.\n")

    # Create rotary encoder with polling approach (more reliable on Pi 5)
    encoder = RotaryEncoder(clk_pin, dt_pin, max_steps=0)
    button = Button(sw_pin, pull_up=True, bounce_time=0.05)

    current_value = 0
    last_steps = 0
    last_button_state = False

    print("-" * 50)
    print(f"Starting value: {current_value}")
    print("-" * 50)

    try:
        while True:
            # Poll encoder steps
            steps = encoder.steps
            if steps != last_steps:
                diff = steps - last_steps
                current_value += diff
                if diff > 0:
                    print(f"  -> Clockwise     | Steps: {steps} | Value: {current_value}")
                else:
                    print(f"  <- Counter-CW    | Steps: {steps} | Value: {current_value}")
                last_steps = steps

            # Poll button state
            button_pressed = button.is_pressed
            if button_pressed and not last_button_state:
                print(f"  * Button PRESSED | Current value: {current_value}")
            elif not button_pressed and last_button_state:
                print(f"    Button released")
            last_button_state = button_pressed

            time.sleep(0.01)  # 10ms polling interval
    except KeyboardInterrupt:
        print("\n\nTest ended.")
    finally:
        encoder.close()
        button.close()


def main():
    parser = argparse.ArgumentParser(description="Test rotary encoder for Bomb Defusal game")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    args = parser.parse_args()

    config = Config.from_env()
    mock = args.mock or not HAS_GPIO

    test_rotary(config, mock)


if __name__ == "__main__":
    main()
