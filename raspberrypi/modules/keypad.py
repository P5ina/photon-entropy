"""Keypad module - enter the correct code using rotary encoder."""
from .base import BaseModule, ModuleState
from hardware.rotary import RotaryEncoder


class KeypadModule(BaseModule):
    """
    Keypad module: use rotary encoder to enter a numeric code.
    - Rotate to select digit (0-9)
    - Press button to confirm digit
    - Server validates if digit/code is correct
    """

    def __init__(self, clk_pin: int, dt_pin: int, sw_pin: int, mock: bool = False):
        super().__init__("keypad", mock)
        self.encoder = RotaryEncoder(
            clk_pin, dt_pin, sw_pin,
            min_val=0, max_val=9,
            mock=mock
        )

        self._code_length = 3
        self._current_digit = 0

    def setup(self):
        """Initialize hardware."""
        self.encoder.setup()
        self.encoder.on_change = self._on_rotate
        self.encoder.on_button = self._on_confirm

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        self._code_length = config.get("code_length", 3)
        if self.mock:
            print(f"[Keypad] Code length: {self._code_length}")

    def activate(self):
        """Activate module."""
        self._state = ModuleState.ACTIVE
        self._current_digit = 0
        self.encoder.reset()

        if self.mock:
            print(f"[Keypad] Activated - enter {self._code_length} digits")

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE

    def reset(self):
        """Reset module state."""
        self._current_digit = 0
        self.encoder.reset()

    def _on_rotate(self, value: int):
        """Handle encoder rotation - local display only."""
        if self._state != ModuleState.ACTIVE:
            return

        self._current_digit = value
        if self.mock:
            print(f"[Keypad] Current digit: {value}")

    def _on_confirm(self):
        """Handle button press - send digit to server."""
        if self._state != ModuleState.ACTIVE:
            return

        digit = self._current_digit
        if self.mock:
            print(f"[Keypad] Confirmed digit: {digit}")

        # Send digit to server for validation
        self._report_action("enter_digit", {"digit": str(digit)})

        # Reset encoder for next digit
        self.encoder.reset()
        self._current_digit = 0

    def simulate_rotate(self, direction: int):
        """Simulate encoder rotation (for testing)."""
        if self.mock:
            self.encoder.simulate_rotate(direction)

    def simulate_confirm(self):
        """Simulate button press (for testing)."""
        if self.mock:
            self.encoder.simulate_button()

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "current_digit": self._current_digit,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self.encoder.cleanup()
