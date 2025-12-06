"""Sensor drivers for touch, Hall, and tilt sensors."""
import time
from typing import Callable, Optional

try:
    import RPi.GPIO as GPIO
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

    def setup(self):
        """Initialize touch sensor GPIO."""
        if self.mock:
            print(f"[Touch] Mock mode - pin {self.pin}")
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(
            self.pin,
            GPIO.RISING,
            callback=self._handle_touch,
            bouncetime=100
        )

    def _handle_touch(self, channel):
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
        return GPIO.input(self.pin) == GPIO.HIGH

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
        if not self.mock:
            try:
                GPIO.remove_event_detect(self.pin)
            except:
                pass


class HallSensor:
    """Hall effect sensor (KY-003) driver for magnet detection."""

    def __init__(self, pin: int, mock: bool = False):
        self.pin = pin
        self.mock = mock or not HAS_GPIO
        self._magnet_detected = False
        self.on_magnet: Optional[Callable[[bool], None]] = None

    def setup(self):
        """Initialize Hall sensor GPIO."""
        if self.mock:
            print(f"[Hall] Mock mode - pin {self.pin}")
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(
            self.pin,
            GPIO.BOTH,
            callback=self._handle_change,
            bouncetime=50
        )

    def _handle_change(self, channel):
        """Handle magnet state change."""
        detected = GPIO.input(self.pin) == GPIO.LOW
        if detected != self._magnet_detected:
            self._magnet_detected = detected
            if self.on_magnet:
                self.on_magnet(detected)

    def is_magnet_present(self) -> bool:
        """Check if magnet is currently detected."""
        if self.mock:
            return self._magnet_detected
        return GPIO.input(self.pin) == GPIO.LOW

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
        if not self.mock:
            try:
                GPIO.remove_event_detect(self.pin)
            except:
                pass


class TiltSensor:
    """Tilt sensor (KY-017) driver for stability monitoring."""

    def __init__(self, pin: int, mock: bool = False):
        self.pin = pin
        self.mock = mock or not HAS_GPIO
        self._tilted = False
        self._tilt_count = 0
        self.on_tilt: Optional[Callable[[], None]] = None

    def setup(self):
        """Initialize tilt sensor GPIO."""
        if self.mock:
            print(f"[Tilt] Mock mode - pin {self.pin}")
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(
            self.pin,
            GPIO.BOTH,
            callback=self._handle_tilt,
            bouncetime=100
        )

    def _handle_tilt(self, channel):
        """Handle tilt event."""
        self._tilted = True
        self._tilt_count += 1
        if self.on_tilt:
            self.on_tilt()

    def is_tilted(self) -> bool:
        """Check if currently tilted."""
        if self.mock:
            return False
        # Sensor outputs LOW when tilted
        return GPIO.input(self.pin) == GPIO.LOW

    def was_tilted(self) -> bool:
        """Check if was tilted (clears flag)."""
        if self._tilted:
            self._tilted = False
            return True
        return False

    def get_tilt_count(self) -> int:
        """Get number of tilt events."""
        return self._tilt_count

    def reset_tilt_count(self):
        """Reset tilt counter."""
        self._tilt_count = 0

    def simulate_tilt(self):
        """Simulate tilt event (for testing)."""
        self._tilted = True
        self._tilt_count += 1
        if self.on_tilt:
            self.on_tilt()

        if self.mock:
            print(f"[Tilt] Tilt detected! (count: {self._tilt_count})")

    def cleanup(self):
        """Clean up GPIO."""
        if not self.mock:
            try:
                GPIO.remove_event_detect(self.pin)
            except:
                pass


class LED:
    """Simple LED driver for wire indicators."""

    def __init__(self, pin: int, mock: bool = False):
        self.pin = pin
        self.mock = mock or not HAS_GPIO
        self._state = False

    def setup(self):
        """Initialize LED GPIO."""
        if self.mock:
            print(f"[LED] Mock mode - pin {self.pin}")
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        """Turn LED on."""
        self._state = True
        if self.mock:
            print(f"[LED {self.pin}] ON")
            return
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        """Turn LED off."""
        self._state = False
        if self.mock:
            print(f"[LED {self.pin}] OFF")
            return
        GPIO.output(self.pin, GPIO.LOW)

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
        self.off()


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
