#!/usr/bin/env python3
"""Test script for LCD 16x2 I2C display.

Usage:
    python test_lcd.py              # Test LCD
    python test_lcd.py --mock       # Run in mock mode
    python test_lcd.py --address 0x3F  # Use different I2C address
"""

import argparse
import time

try:
    from RPLCD.i2c import CharLCD
    HAS_LCD = True
except ImportError:
    HAS_LCD = False
    print("[WARN] RPLCD not found, running in mock mode")
    print("       Install with: pip install RPLCD")

from config import Config


def test_lcd(config: Config, mock: bool = False, address: int = None):
    """Test the LCD display."""
    print("=" * 50)
    print("LCD 16x2 I2C TEST")
    print("=" * 50)

    lcd_address = address or config.lcd_address
    print(f"\nLCD I2C address: {hex(lcd_address)}")

    if mock or not HAS_LCD:
        print("[MOCK MODE]")
        print("\nSimulating LCD output...")
        print()
        print("┌────────────────┐")
        print("│BOMB DEFUSAL    │")
        print("│Ready...        │")
        print("└────────────────┘")
        time.sleep(1)
        print()
        print("┌────────────────┐")
        print("│Time: 05:00     │")
        print("│Strikes: 0/3    │")
        print("└────────────────┘")
        time.sleep(1)
        print()
        print("┌────────────────┐")
        print("│****BOOM****    │")
        print("│   GAME OVER    │")
        print("└────────────────┘")
        return

    print("\nInitializing LCD...")

    try:
        lcd = CharLCD(
            i2c_expander='PCF8574',
            address=lcd_address,
            port=1,
            cols=16,
            rows=2,
            dotsize=8,
            auto_linebreaks=True
        )
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize LCD: {e}")
        print("\nTroubleshooting:")
        print("  1. Check I2C is enabled: sudo raspi-config")
        print("  2. Check I2C devices: i2cdetect -y 1")
        print("  3. Try different address: --address 0x3F")
        return

    print("LCD initialized!")
    print("\n" + "-" * 50)

    # Test 1: Welcome message
    print("  1. Welcome message...", end=" ", flush=True)
    lcd.clear()
    lcd.write_string("BOMB DEFUSAL")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Ready...")
    print("OK")
    time.sleep(2)

    # Test 2: Timer display
    print("  2. Timer display...", end=" ", flush=True)
    lcd.clear()
    lcd.write_string("Time: 05:00")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Strikes: 0/3")
    print("OK")
    time.sleep(2)

    # Test 3: Countdown simulation
    print("  3. Countdown (5 seconds)...", end=" ", flush=True)
    for i in range(5, 0, -1):
        lcd.cursor_pos = (0, 6)
        lcd.write_string(f"00:0{i}")
        time.sleep(1)
    print("OK")

    # Test 4: Strike display
    print("  4. Strike display...", end=" ", flush=True)
    lcd.clear()
    lcd.write_string("!! STRIKE !!")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Strikes: 1/3")
    print("OK")
    time.sleep(2)

    # Test 5: Code entry simulation
    print("  5. Code entry...", end=" ", flush=True)
    lcd.clear()
    lcd.write_string("Enter code:")
    lcd.cursor_pos = (1, 0)
    for digit in ["_", "7", "7_", "74", "74_", "742"]:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(digit.ljust(16))
        time.sleep(0.5)
    print("OK")
    time.sleep(1)

    # Test 6: Win message
    print("  6. Win message...", end=" ", flush=True)
    lcd.clear()
    lcd.write_string("** DEFUSED! **")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Time: 02:34")
    print("OK")
    time.sleep(2)

    # Test 7: Game over
    print("  7. Game over...", end=" ", flush=True)
    lcd.clear()
    lcd.write_string("****BOOM****")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("  GAME OVER")
    print("OK")
    time.sleep(2)

    # Test 8: Character test
    print("  8. Character test...", end=" ", flush=True)
    lcd.clear()
    lcd.write_string("0123456789ABCDEF")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("!@#$%^&*()+-=<>")
    print("OK")
    time.sleep(2)

    # Clear and finish
    lcd.clear()
    lcd.write_string("Test complete!")
    lcd.close()

    print("\n" + "-" * 50)
    print("LCD test complete!")


def main():
    parser = argparse.ArgumentParser(description="Test LCD for Bomb Defusal game")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    parser.add_argument("--address", type=lambda x: int(x, 0), help="I2C address (e.g., 0x27)")
    args = parser.parse_args()

    config = Config.from_env()
    mock = args.mock or not HAS_LCD

    test_lcd(config, mock, args.address)


if __name__ == "__main__":
    main()
