"""Button driver with debouncing."""
import time
from typing import Callable, Optional

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class Button:
    """Single button with debounce and callback support."""

    def __init__(self, pin: int, callback: Optional[Callable] = None,
                 pull_up: bool = False, debounce_ms: int = 50, mock: bool = False):
        self.pin = pin
        self.callback = callback
        self.pull_up = pull_up
        self.debounce_ms = debounce_ms
        self.mock = mock or not HAS_GPIO
        self._last_press_time = 0
        self._pressed = False

    def setup(self):
        """Initialize the button GPIO."""
        if self.mock:
            print(f"[Button] Mock mode - pin {self.pin}")
            return

        GPIO.setmode(GPIO.BCM)

        if self.pull_up:
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        else:
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Add event detection
        edge = GPIO.FALLING if self.pull_up else GPIO.RISING
        GPIO.add_event_detect(
            self.pin,
            edge,
            callback=self._handle_press,
            bouncetime=self.debounce_ms
        )

    def _handle_press(self, channel):
        """Handle button press with debounce."""
        current_time = time.time() * 1000
        if current_time - self._last_press_time > self.debounce_ms:
            self._last_press_time = current_time
            self._pressed = True
            if self.callback:
                self.callback()

    def is_pressed(self) -> bool:
        """Check if button is currently pressed."""
        if self.mock:
            return False

        if self.pull_up:
            return GPIO.input(self.pin) == GPIO.LOW
        else:
            return GPIO.input(self.pin) == GPIO.HIGH

    def was_pressed(self) -> bool:
        """Check if button was pressed since last check (clears flag)."""
        if self._pressed:
            self._pressed = False
            return True
        return False

    def wait_for_press(self, timeout: float = None) -> bool:
        """Wait for button press."""
        start = time.time()
        while True:
            if self.was_pressed():
                return True
            if timeout and (time.time() - start) > timeout:
                return False
            time.sleep(0.01)

    def simulate_press(self):
        """Simulate a button press (for testing)."""
        if self.mock:
            print(f"[Button] Pin {self.pin} pressed (simulated)")
            self._pressed = True
            if self.callback:
                self.callback()

    def cleanup(self):
        """Clean up GPIO event detection."""
        if not self.mock:
            try:
                GPIO.remove_event_detect(self.pin)
            except:
                pass


class ButtonGroup:
    """Group of buttons for wire module."""

    def __init__(self, pins: tuple, mock: bool = False):
        self.pins = pins
        self.mock = mock
        self.buttons: list[Button] = []
        self._press_callbacks: list[Optional[Callable]] = [None] * len(pins)

    def setup(self):
        """Initialize all buttons."""
        for i, pin in enumerate(self.pins):
            btn = Button(
                pin,
                callback=lambda idx=i: self._on_press(idx),
                mock=self.mock
            )
            btn.setup()
            self.buttons.append(btn)

    def _on_press(self, index: int):
        """Handle press for specific button."""
        if self._press_callbacks[index]:
            self._press_callbacks[index](index)

    def set_callback(self, index: int, callback: Callable):
        """Set callback for specific button."""
        if 0 <= index < len(self._press_callbacks):
            self._press_callbacks[index] = callback

    def set_all_callbacks(self, callback: Callable):
        """Set same callback for all buttons."""
        for i in range(len(self._press_callbacks)):
            self._press_callbacks[i] = callback

    def get_pressed(self) -> list[int]:
        """Get list of button indices that were pressed."""
        pressed = []
        for i, btn in enumerate(self.buttons):
            if btn.was_pressed():
                pressed.append(i)
        return pressed

    def simulate_press(self, index: int):
        """Simulate pressing a specific button."""
        if 0 <= index < len(self.buttons):
            self.buttons[index].simulate_press()

    def cleanup(self):
        """Clean up all buttons."""
        for btn in self.buttons:
            btn.cleanup()
