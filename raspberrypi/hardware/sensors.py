"""Sensor drivers for touch, Hall, and tilt sensors using gpiozero (Pi 5 compatible)."""
import time
from typing import Callable, Optional

try:
    from gpiozero import Button as GPIOButton, DigitalInputDevice, LED as GPIOLED
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class TouchSensor:
    """Touch sensor (KY-036) driver."""

    def __init__(self, pin: int, mock: bool = False):
        self.pin = pin
        self.mock = mock or not HAS_GPIO
        self._touched = False
        self._tap_count = 0
        self._last_tap_time = 0
        self.on_touch: Optional[Callable[[], None]] = None
        self._sensor: Optional[GPIOButton] = None

    def setup(self):
        """Initialize touch sensor GPIO."""
        if self.mock:
            print(f"[Touch] Mock mode - pin {self.pin}")
            return

        # Touch sensor outputs HIGH when touched
        self._sensor = GPIOButton(self.pin, pull_up=False, bounce_time=0.1)
        self._sensor.when_pressed = self._handle_touch

    def _handle_touch(self):
        """Handle touch event."""
        current_time = time.time()

        # Reset tap count if too much time passed
        if current_time - self._last_tap_time > 0.5:
            self._tap_count = 0

        self._tap_count += 1
        self._last_tap_time = current_time
        self._touched = True

        if self.on_touch:
            self.on_touch()

    def is_touched(self) -> bool:
        """Check if sensor is currently touched."""
        if self.mock:
            return False
        if self._sensor:
            return self._sensor.is_pressed
        return False

    def was_touched(self) -> bool:
        """Check if sensor was touched (clears flag)."""
        if self._touched:
            self._touched = False
            return True
        return False

    def get_tap_count(self) -> int:
        """Get number of taps in recent window."""
        current_time = time.time()
        if current_time - self._last_tap_time > 0.5:
            self._tap_count = 0
        return self._tap_count

    def reset_tap_count(self):
        """Reset tap counter."""
        self._tap_count = 0

    def simulate_tap(self, count: int = 1):
        """Simulate touch taps (for testing)."""
        for _ in range(count):
            self._tap_count += 1
            self._last_tap_time = time.time()
            self._touched = True
            if self.on_touch:
                self.on_touch()
            time.sleep(0.1)

        if self.mock:
            print(f"[Touch] Tapped {count} times")

    def cleanup(self):
        """Clean up GPIO."""
        if self._sensor:
            self._sensor.close()
            self._sensor = None


class HallSensor:
    """Hall effect sensor (KY-003) driver for magnet detection."""

    def __init__(self, pin: int, mock: bool = False):
        self.pin = pin
        self.mock = mock or not HAS_GPIO
        self._magnet_detected = False
        self.on_magnet: Optional[Callable[[bool], None]] = None
        self._sensor: Optional[DigitalInputDevice] = None

    def setup(self):
        """Initialize Hall sensor GPIO."""
        if self.mock:
            print(f"[Hall] Mock mode - pin {self.pin}")
            return

        # Hall sensor outputs LOW when magnet is present (active low)
        self._sensor = DigitalInputDevice(self.pin, pull_up=True, bounce_time=0.05)
        self._sensor.when_activated = lambda: self._handle_change(True)
        self._sensor.when_deactivated = lambda: self._handle_change(False)

    def _handle_change(self, detected: bool):
        """Handle magnet state change."""
        # Invert because sensor is active low
        detected = not detected
        if detected != self._magnet_detected:
            self._magnet_detected = detected
            if self.on_magnet:
                self.on_magnet(detected)

    def is_magnet_present(self) -> bool:
        """Check if magnet is currently detected."""
        if self.mock:
            return self._magnet_detected
        if self._sensor:
            # Invert because sensor is active low
            return not self._sensor.value
        return False

    def was_magnet_applied(self) -> bool:
        """Check if magnet was applied (clears flag)."""
        if self._magnet_detected:
            self._magnet_detected = False
            return True
        return False

    def simulate_magnet(self, present: bool = True):
        """Simulate magnet presence (for testing)."""
        self._magnet_detected = present
        if self.on_magnet:
            self.on_magnet(present)

        if self.mock:
            print(f"[Hall] Magnet {'detected' if present else 'removed'}")

    def cleanup(self):
        """Clean up GPIO."""
        if self._sensor:
            self._sensor.close()
            self._sensor = None


class LED:
    """Simple LED driver for wire indicators."""

    def __init__(self, pin: int, mock: bool = False):
        self.pin = pin
        self.mock = mock or not HAS_GPIO
        self._state = False
        self._led: Optional[GPIOLED] = None

    def setup(self):
        """Initialize LED GPIO."""
        if self.mock:
            print(f"[LED] Mock mode - pin {self.pin}")
            return

        self._led = GPIOLED(self.pin)

    def on(self):
        """Turn LED on."""
        self._state = True
        if self.mock:
            print(f"[LED {self.pin}] ON")
            return
        if self._led:
            self._led.on()

    def off(self):
        """Turn LED off."""
        self._state = False
        if self.mock:
            print(f"[LED {self.pin}] OFF")
            return
        if self._led:
            self._led.off()

    def toggle(self):
        """Toggle LED state."""
        if self._state:
            self.off()
        else:
            self.on()

    def set(self, state: bool):
        """Set LED state."""
        if state:
            self.on()
        else:
            self.off()

    @property
    def is_on(self) -> bool:
        """Check if LED is on."""
        return self._state

    def cleanup(self):
        """Clean up GPIO."""
        if self._led:
            self._led.off()
            self._led.close()
            self._led = None


class LEDGroup:
    """Group of LEDs for wire indicators."""

    def __init__(self, pins: tuple, mock: bool = False):
        self.pins = pins
        self.mock = mock
        self.leds: list[LED] = []

    def setup(self):
        """Initialize all LEDs."""
        for pin in self.pins:
            led = LED(pin, mock=self.mock)
            led.setup()
            self.leds.append(led)

    def all_on(self):
        """Turn all LEDs on."""
        for led in self.leds:
            led.on()

    def all_off(self):
        """Turn all LEDs off."""
        for led in self.leds:
            led.off()

    def set(self, index: int, state: bool):
        """Set specific LED state."""
        if 0 <= index < len(self.leds):
            self.leds[index].set(state)

    def set_pattern(self, pattern: list[bool]):
        """Set pattern of LEDs."""
        for i, state in enumerate(pattern):
            if i < len(self.leds):
                self.leds[i].set(state)

    def cleanup(self):
        """Clean up all LEDs."""
        for led in self.leds:
            led.cleanup()
