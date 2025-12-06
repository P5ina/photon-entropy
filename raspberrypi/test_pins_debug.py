#!/usr/bin/env python3
"""Debug GPIO input reading on Pi 5.

Usage:
    python test_pins_debug.py
"""

import time

# Test 1: Check available GPIO chips
print("=" * 60)
print("GPIO DEBUG TEST")
print("=" * 60)

print("\n1. Checking GPIO chips...")
print("-" * 40)

try:
    import lgpio

    # Try different chip numbers
    for chip in [0, 1, 2, 3, 4]:
        try:
            h = lgpio.gpiochip_open(chip)
            info = f"Chip {chip}: OPENED"
            lgpio.gpiochip_close(h)
            print(f"  {info}")
        except Exception as e:
            print(f"  Chip {chip}: {e}")
except ImportError:
    print("  lgpio not available")

# Test 2: Try gpiozero with explicit factory
print("\n2. Testing gpiozero factories...")
print("-" * 40)

try:
    from gpiozero import Device, DigitalInputDevice
    from gpiozero.pins.lgpio import LGPIOFactory

    # Check current factory
    print(f"  Current factory: {Device.pin_factory}")

    # Try setting LGPIOFactory explicitly
    try:
        Device.pin_factory = LGPIOFactory()
        print(f"  Set LGPIOFactory: {Device.pin_factory}")
    except Exception as e:
        print(f"  LGPIOFactory error: {e}")

except ImportError as e:
    print(f"  Import error: {e}")

# Test 3: Test a button that we KNOW works
print("\n3. Testing GPIO 19 (Wire Button 1 - known working)...")
print("-" * 40)

try:
    from gpiozero import Button

    btn = Button(19, pull_up=True, bounce_time=0.05)
    print(f"  Button created on GPIO 19")
    print(f"  is_pressed: {btn.is_pressed}")
    print(f"  value: {btn.value}")
    print(f"  pin: {btn.pin}")
    print(f"  pin.state: {btn.pin.state}")

    print("\n  Press button 1 within 5 seconds...")
    pressed = btn.wait_for_press(timeout=5)
    if pressed:
        print("  ✓ Button press detected!")
    else:
        print("  ✗ No press detected (timeout)")

    btn.close()
except Exception as e:
    print(f"  Error: {e}")

# Test 4: Try reading pin state differently
print("\n4. Alternative read methods for GPIO 16...")
print("-" * 40)

try:
    import lgpio

    h = lgpio.gpiochip_open(0)
    pin = 16

    # Method A: Claim as input, read
    print(f"  Method A: gpio_claim_input + gpio_read")
    lgpio.gpio_claim_input(h, pin)
    val = lgpio.gpio_read(h, pin)
    print(f"    Value: {val}")
    lgpio.gpio_free(h, pin)

    # Method B: Claim as output first, then input
    print(f"  Method B: output HIGH, then switch to input")
    lgpio.gpio_claim_output(h, pin, 1)  # Drive HIGH
    time.sleep(0.01)
    lgpio.gpio_free(h, pin)
    lgpio.gpio_claim_input(h, pin)
    val = lgpio.gpio_read(h, pin)
    print(f"    Value: {val}")
    lgpio.gpio_free(h, pin)

    lgpio.gpiochip_close(h)
except Exception as e:
    print(f"  Error: {e}")

# Test 5: Check /sys/class/gpio if available
print("\n5. Checking sysfs GPIO (legacy)...")
print("-" * 40)

import os
if os.path.exists("/sys/class/gpio"):
    print("  /sys/class/gpio exists")
    try:
        with open("/sys/class/gpio/export", "w") as f:
            f.write("16")
        time.sleep(0.1)
        with open("/sys/class/gpio/gpio16/direction", "w") as f:
            f.write("in")
        with open("/sys/class/gpio/gpio16/value", "r") as f:
            val = f.read().strip()
        print(f"  GPIO 16 via sysfs: {val}")
        with open("/sys/class/gpio/unexport", "w") as f:
            f.write("16")
    except Exception as e:
        print(f"  sysfs error: {e}")
else:
    print("  /sys/class/gpio not available (Pi 5 uses /dev/gpiochip*)")

# Test 6: Check gpiochip info
print("\n6. GPIO chip device info...")
print("-" * 40)

import subprocess
try:
    result = subprocess.run(["ls", "-la", "/dev/gpiochip*"], capture_output=True, text=True, shell=True)
    print(f"  {result.stdout or result.stderr}")
except:
    pass

try:
    result = subprocess.run(["cat", "/proc/device-tree/model"], capture_output=True, text=True)
    print(f"  Model: {result.stdout.strip()}")
except:
    pass

print("\n" + "=" * 60)
