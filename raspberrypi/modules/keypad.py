"""Keypad module - enter the correct code using rotary encoder."""
from typing import Optional
from .base import BaseModule, ModuleState
from hardware.rotary import RotaryEncoder


class KeypadModule(BaseModule):
    """
    Keypad module: use rotary encoder to enter a numeric code.
    - Rotate to select digit (0-9)
    - Press button to confirm digit
    - Enter full code to solve
    """

    def __init__(self, clk_pin: int, dt_pin: int, sw_pin: int, mock: bool = False):
        super().__init__("keypad", mock)
        self.encoder = RotaryEncoder(
            clk_pin, dt_pin, sw_pin,
            min_val=0, max_val=9,
            mock=mock
        )

        self._code: list[int] = []  # Required code
        self._entered: list[int] = []  # Digits entered so far
        self._current_digit = 0

    def setup(self):
        """Initialize hardware."""
        self.encoder.setup()
        self.encoder.on_change = self._on_rotate
        self.encoder.on_button = self._on_confirm

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        # Config contains: code (list of digits)
        self._code = config.get("code", [1, 2, 3, 4])
        if self.mock:
            print(f"[Keypad] Code: {self._code}")

    def activate(self):
        """Activate module."""
        self._state = ModuleState.ACTIVE
        self._entered = []
        self._current_digit = 0
        self.encoder.reset()

        if self.mock:
            print(f"[Keypad] Activated - code length: {len(self._code)}")

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE

    def reset(self):
        """Reset module state."""
        self._entered = []
        self._current_digit = 0
        self.encoder.reset()

    def _on_rotate(self, value: int):
        """Handle encoder rotation."""
        if self._state != ModuleState.ACTIVE:
            return

        self._current_digit = value
        self._report_action("rotate", {"digit": value})

        if self.mock:
            print(f"[Keypad] Current digit: {value}")

    def _on_confirm(self):
        """Handle button press (confirm digit)."""
        if self._state != ModuleState.ACTIVE:
            return

        digit = self._current_digit
        position = len(self._entered)

        self._report_action("confirm", {"digit": digit, "position": position})

        if self.mock:
            print(f"[Keypad] Confirmed digit: {digit}")

        # Check if digit is correct
        if position < len(self._code):
            expected = self._code[position]
            if digit == expected:
                self._entered.append(digit)
                if self.mock:
                    print(f"[Keypad] Correct! {len(self._entered)}/{len(self._code)}")

                # Reset encoder for next digit
                self.encoder.reset()
                self._current_digit = 0

                # Check if code complete
                if len(self._entered) == len(self._code):
                    self._report_solved()
                    if self.mock:
                        print("[Keypad] SOLVED!")
            else:
                self._report_strike(f"Wrong digit: entered {digit}, expected {expected}")
                # Reset progress on wrong digit
                self._entered = []
                self.encoder.reset()
                self._current_digit = 0
                if self.mock:
                    print(f"[Keypad] STRIKE! Wrong digit, progress reset")

    def simulate_rotate(self, direction: int):
        """Simulate encoder rotation (for testing)."""
        if self.mock:
            self.encoder.simulate_rotate(direction)

    def simulate_confirm(self):
        """Simulate button press (for testing)."""
        if self.mock:
            self.encoder.simulate_button()

    def get_progress(self) -> int:
        """Get number of correct digits entered."""
        return len(self._entered)

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "entered_count": len(self._entered),
            "current_digit": self._current_digit,
            "total_digits": len(self._code),
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self.encoder.cleanup()
