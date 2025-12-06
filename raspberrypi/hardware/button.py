"""Button driver with debouncing using gpiozero (Pi 5 compatible).

Buttons use internal pull-up resistor:
  GPIO -> Button -> GND (no external resistor needed)
"""
import time
from typing import Callable, Optional

try:
    from gpiozero import Button as GPIOButton
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class Button:
    """Single button with debounce and callback support."""

    def __init__(self, pin: int, callback: Optional[Callable] = None,
                 debounce_ms: int = 50, mock: bool = False):
        self.pin = pin
        self.callback = callback
        self.debounce_ms = debounce_ms
        self.mock = mock or not HAS_GPIO
        self._last_press_time = 0
        self._pressed = False
        self._gpio_button: Optional[GPIOButton] = None

    def setup(self):
        """Initialize the button GPIO."""
        if self.mock:
            print(f"[Button] Mock mode - pin {self.pin}")
            return

        # Use internal pull-up: button connects GPIO to GND when pressed
        self._gpio_button = GPIOButton(
            self.pin,
            pull_up=True,
            bounce_time=self.debounce_ms / 1000.0
        )
        self._gpio_button.when_pressed = self._handle_press

    def _handle_press(self):
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
        if self._gpio_button:
            return self._gpio_button.is_pressed
        return False

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
        """Clean up GPIO."""
        if self._gpio_button:
            self._gpio_button.close()
            self._gpio_button = None


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
