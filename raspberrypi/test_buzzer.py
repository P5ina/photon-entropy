#!/usr/bin/env python3
"""Test script for buzzer.

Usage:
    python test_buzzer.py           # Test buzzer
    python test_buzzer.py --mock    # Run in mock mode
"""

import argparse
import time

try:
    from gpiozero import TonalBuzzer, Buzzer
    HAS_GPIO = True
    GPIO_LIB = "gpiozero"
except ImportError:
    HAS_GPIO = False
    GPIO_LIB = None
    print("[WARN] gpiozero not found, running in mock mode")
    print("       Install with: pip install gpiozero lgpio")

from config import Config


def test_buzzer(config: Config, mock: bool = False):
    """Test the buzzer."""
    print("=" * 50)
    print("BUZZER TEST")
    print("=" * 50)

    buzzer_pin = config.buzzer_pin
    print(f"\nBuzzer pin: GPIO {buzzer_pin}")

    if mock or not HAS_GPIO:
        print("[MOCK MODE]")
        print("\nSimulating buzzer sounds...")
        print("  [BEEP] Short beep")
        time.sleep(0.5)
        print("  [BEEP BEEP BEEP] Triple beep")
        time.sleep(0.5)
        print("  [BEEEEP] Long beep")
        time.sleep(0.5)
        print("  [tick-tock] Timer pattern")
        return

    print(f"GPIO Library: {GPIO_LIB}")
    print("\nTesting buzzer patterns...\n")

    # Try TonalBuzzer first (for passive buzzers), fall back to simple Buzzer
    try:
        buzzer = TonalBuzzer(buzzer_pin)
        is_tonal = True
        print("Using TonalBuzzer (passive buzzer)")
    except Exception:
        buzzer = Buzzer(buzzer_pin)
        is_tonal = False
        print("Using simple Buzzer (active buzzer)")

    print("-" * 50)

    # Test 1: Short beep
    print("  1. Short beep...", end=" ", flush=True)
    if is_tonal:
        buzzer.play(440)  # A4 note
        time.sleep(0.1)
        buzzer.stop()
    else:
        buzzer.on()
        time.sleep(0.1)
        buzzer.off()
    print("OK")
    time.sleep(0.3)

    # Test 2: Triple beep
    print("  2. Triple beep...", end=" ", flush=True)
    for _ in range(3):
        if is_tonal:
            buzzer.play(880)  # A5 note
            time.sleep(0.1)
            buzzer.stop()
        else:
            buzzer.on()
            time.sleep(0.1)
            buzzer.off()
        time.sleep(0.1)
    print("OK")
    time.sleep(0.3)

    # Test 3: Long beep
    print("  3. Long beep...", end=" ", flush=True)
    if is_tonal:
        buzzer.play(330)  # E4 note
        time.sleep(0.5)
        buzzer.stop()
    else:
        buzzer.on()
        time.sleep(0.5)
        buzzer.off()
    print("OK")
    time.sleep(0.3)

    # Test 4: Timer tick pattern
    print("  4. Timer tick pattern (5 ticks)...", end=" ", flush=True)
    for i in range(5):
        if is_tonal:
            buzzer.play(1000)
            time.sleep(0.05)
            buzzer.stop()
        else:
            buzzer.on()
            time.sleep(0.05)
            buzzer.off()
        time.sleep(0.95)
    print("OK")

    # Test 5: Alarm pattern (if tonal)
    if is_tonal:
        print("  5. Alarm pattern...", end=" ", flush=True)
        for _ in range(3):
            buzzer.play(880)
            time.sleep(0.15)
            buzzer.play(440)
            time.sleep(0.15)
        buzzer.stop()
        print("OK")
        time.sleep(0.3)

    # Test 6: Success sound
    print("  6. Success sound...", end=" ", flush=True)
    if is_tonal:
        for freq in [523, 659, 784, 1047]:  # C5, E5, G5, C6
            buzzer.play(freq)
            time.sleep(0.1)
        buzzer.stop()
    else:
        for _ in range(2):
            buzzer.on()
            time.sleep(0.1)
            buzzer.off()
            time.sleep(0.05)
    print("OK")

    buzzer.close()
    print("\n" + "-" * 50)
    print("Buzzer test complete!")


def main():
    parser = argparse.ArgumentParser(description="Test buzzer for Bomb Defusal game")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    args = parser.parse_args()

    config = Config.from_env()
    mock = args.mock or not HAS_GPIO

    test_buzzer(config, mock)


if __name__ == "__main__":
    main()
