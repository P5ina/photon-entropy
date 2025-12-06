"""Simon module - respond to color sequence with correct taps."""
import time
import threading
from typing import Optional
from .base import BaseModule, ModuleState
from hardware.rgb_led import RGBLED
from hardware.sensors import TouchSensor


class SimonModule(BaseModule):
    """
    Simon Says module: RGB LED shows colors, player responds with taps.
    - LED shows a sequence of colors (red, green, blue)
    - For each color: RED=1 tap, GREEN=2 taps, BLUE=0 taps (wait)
    - Server validates tap count for each color in sequence
    """

    def __init__(self, rgb_pins: tuple, touch_pin: int, mock: bool = False):
        super().__init__("simon", mock)
        self.rgb = RGBLED(rgb_pins[0], rgb_pins[1], rgb_pins[2], mock=mock)
        self.touch = TouchSensor(touch_pin, mock=mock)

        self._sequence: list[str] = []
        self._current_index = 0
        self._tap_count = 0
        self._awaiting_input = False
        self._sequence_thread: Optional[threading.Thread] = None
        self._stop_sequence = threading.Event()
        self._input_timeout: Optional[threading.Timer] = None

    def setup(self):
        """Initialize hardware."""
        self.rgb.setup()
        self.touch.setup()
        self.touch.on_touch = self._on_touch

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        self._sequence = config.get("sequence", [])
        self._current_index = config.get("current_index", 0)
        if self.mock:
            print(f"[Simon] Sequence: {self._sequence}")

    def activate(self):
        """Activate module and start showing sequence."""
        self._state = ModuleState.ACTIVE
        self._current_index = 0
        self._tap_count = 0
        self._awaiting_input = False
        self._stop_sequence.clear()

        if self.mock:
            print(f"[Simon] Activated - {len(self._sequence)} colors")

        # Start showing sequence
        self._show_next_color()

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE
        self._stop_sequence.set()
        self._cancel_input_timeout()
        self.rgb.off()

    def reset(self):
        """Reset module state."""
        self._current_index = 0
        self._tap_count = 0
        self._awaiting_input = False
        self._cancel_input_timeout()
        self.rgb.off()

    def _show_next_color(self):
        """Show the next color in sequence."""
        if self._state != ModuleState.ACTIVE:
            return

        if self._current_index >= len(self._sequence):
            # Sequence complete - should be solved by server
            return

        color = self._sequence[self._current_index]
        if self.mock:
            print(f"[Simon] Showing color {self._current_index + 1}/{len(self._sequence)}: {color}")

        # Show color
        self.rgb.set_color(color)

        # After showing color, wait for input
        def start_input():
            time.sleep(1.0)  # Show color for 1 second
            if self._state == ModuleState.ACTIVE:
                self._awaiting_input = True
                self._tap_count = 0
                self.rgb.off()
                if self.mock:
                    print(f"[Simon] Awaiting input for {color}")
                # Set timeout for input
                self._start_input_timeout()

        thread = threading.Thread(target=start_input)
        thread.daemon = True
        thread.start()

    def _start_input_timeout(self):
        """Start timeout for player input."""
        self._cancel_input_timeout()

        def on_timeout():
            if self._awaiting_input and self._state == ModuleState.ACTIVE:
                # Time's up - submit current tap count
                self._submit_taps()

        self._input_timeout = threading.Timer(2.0, on_timeout)
        self._input_timeout.daemon = True
        self._input_timeout.start()

    def _cancel_input_timeout(self):
        """Cancel input timeout."""
        if self._input_timeout:
            self._input_timeout.cancel()
            self._input_timeout = None

    def _on_touch(self):
        """Handle touch sensor tap."""
        if self._state != ModuleState.ACTIVE or not self._awaiting_input:
            return

        self._tap_count += 1
        if self.mock:
            print(f"[Simon] Tap! Count: {self._tap_count}")

        # Flash to confirm tap
        self.rgb.flash("white", 0.1)

        # Reset timeout
        self._start_input_timeout()

    def _submit_taps(self):
        """Submit tap count to server."""
        if not self._awaiting_input:
            return

        self._awaiting_input = False
        self._cancel_input_timeout()

        if self.mock:
            print(f"[Simon] Submitting {self._tap_count} taps for index {self._current_index}")

        # Send tap count to server
        self._report_action("tap", {"taps": self._tap_count})

        # Move to next color (server will tell us if it was right/wrong)
        self._current_index += 1

        # Brief pause then show next color
        time.sleep(0.5)
        self._show_next_color()

    def simulate_touch(self):
        """Simulate touch (for testing)."""
        if self.mock:
            self._on_touch()

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "current_index": self._current_index,
            "tap_count": self._tap_count,
            "awaiting_input": self._awaiting_input,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self._stop_sequence.set()
        self._cancel_input_timeout()
        self.rgb.cleanup()
        self.touch.cleanup()
