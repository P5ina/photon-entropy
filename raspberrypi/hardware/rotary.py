"""Rotary encoder driver using gpiozero (Pi 5 compatible)."""
import time
import threading
from typing import Callable, Optional

try:
    from gpiozero import RotaryEncoder as GPIORotaryEncoder, Button as GPIOButton
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class RotaryEncoder:
    """Rotary encoder with button for keypad module."""

    def __init__(self, clk_pin: int, dt_pin: int, sw_pin: int,
                 min_val: int = 0, max_val: int = 9, mock: bool = False):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.min_val = min_val
        self.max_val = max_val
        self.mock = mock or not HAS_GPIO

        self._value = min_val
        self._button_pressed = False

        # Callbacks
        self.on_change: Optional[Callable[[int], None]] = None
        self.on_button: Optional[Callable[[], None]] = None

        self._lock = threading.Lock()
        self._encoder: Optional[GPIORotaryEncoder] = None
        self._button: Optional[GPIOButton] = None

    def setup(self):
        """Initialize the rotary encoder GPIO."""
        if self.mock:
            print(f"[Rotary] Mock mode - CLK:{self.clk_pin} DT:{self.dt_pin} SW:{self.sw_pin}")
            return

        # Setup rotary encoder
        self._encoder = GPIORotaryEncoder(self.clk_pin, self.dt_pin, max_steps=0)
        self._encoder.when_rotated = self._handle_rotation

        # Setup button
        self._button = GPIOButton(self.sw_pin, pull_up=True, bounce_time=0.2)
        self._button.when_pressed = self._handle_button

    def _handle_rotation(self):
        """Handle rotary encoder rotation."""
        with self._lock:
            # Get the step count from the encoder
            steps = self._encoder.steps
            self._encoder.steps = 0  # Reset steps

            if steps > 0:
                # Clockwise
                if self._value < self.max_val:
                    self._value += 1
            elif steps < 0:
                # Counter-clockwise
                if self._value > self.min_val:
                    self._value -= 1

            if self.on_change:
                self.on_change(self._value)

    def _handle_button(self):
        """Handle button press."""
        self._button_pressed = True
        if self.on_button:
            self.on_button()

    @property
    def value(self) -> int:
        """Get current value."""
        return self._value

    @value.setter
    def value(self, val: int):
        """Set current value."""
        self._value = max(self.min_val, min(self.max_val, val))

    def reset(self):
        """Reset value to minimum."""
        self._value = self.min_val

    def was_button_pressed(self) -> bool:
        """Check if button was pressed (clears flag)."""
        if self._button_pressed:
            self._button_pressed = False
            return True
        return False

    def is_button_pressed(self) -> bool:
        """Check if button is currently pressed."""
        if self.mock:
            return False
        if self._button:
            return self._button.is_pressed
        return False

    def simulate_rotate(self, direction: int):
        """Simulate rotation (for testing). direction: 1=CW, -1=CCW."""
        if direction > 0 and self._value < self.max_val:
            self._value += 1
        elif direction < 0 and self._value > self.min_val:
            self._value -= 1

        if self.on_change:
            self.on_change(self._value)

        if self.mock:
            print(f"[Rotary] Value: {self._value}")

    def simulate_button(self):
        """Simulate button press (for testing)."""
        self._button_pressed = True
        if self.on_button:
            self.on_button()

        if self.mock:
            print(f"[Rotary] Button pressed, value: {self._value}")

    def cleanup(self):
        """Clean up GPIO."""
        if self._encoder:
            self._encoder.close()
            self._encoder = None
        if self._button:
            self._button.close()
            self._button = None
