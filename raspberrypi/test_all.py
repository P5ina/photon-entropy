#!/usr/bin/env python3
"""Run all hardware tests sequentially.

Usage:
    python test_all.py              # Run all tests
    python test_all.py --mock       # Run in mock mode
    python test_all.py --skip-lcd   # Skip LCD test
"""

import argparse
import subprocess
import sys


def run_test(script: str, mock: bool = False):
    """Run a test script."""
    cmd = [sys.executable, script]
    if mock:
        cmd.append("--mock")

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run all hardware tests")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    parser.add_argument("--skip-lcd", action="store_true", help="Skip LCD test")
    args = parser.parse_args()

    tests = [
        ("test_leds.py", "LEDs (Wire + RGB)"),
        ("test_buttons.py", "Buttons"),
        ("test_touch.py", "Touch Sensor"),
        ("test_hall.py", "Hall Sensor"),
        ("test_buzzer.py", "Buzzer"),
    ]

    if not args.skip_lcd:
        tests.append(("test_lcd.py", "LCD Display"))

    print("=" * 60)
    print("BOMB DEFUSAL - HARDWARE TEST SUITE")
    print("=" * 60)
    print(f"\nMode: {'MOCK' if args.mock else 'HARDWARE'}")
    print(f"Tests to run: {len(tests)}")
    print()

    for i, (script, name) in enumerate(tests, 1):
        print(f"\n{'=' * 60}")
        print(f"[{i}/{len(tests)}] {name}")
        print("=" * 60)

        input(f"\nPress Enter to run {name} test (or Ctrl+C to skip)...")

        try:
            run_test(script, args.mock)
        except KeyboardInterrupt:
            print("\nTest skipped.")
            continue

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted.")
