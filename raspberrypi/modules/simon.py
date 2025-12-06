"""Simon module - display color sequence on RGB LED for defuser to relay to expert."""
import time
import threading
from typing import Optional
from .base import BaseModule, ModuleState
from hardware.rgb_led import RGBLED


class SimonModule(BaseModule):
    """
    Simon Says module: RGB LED shows colors, expert taps matching colors on mobile.

    - LED shows a sequence of colors (red, green, blue) repeatedly
    - Defuser tells expert what colors they see
    - Expert taps matching color buttons on mobile app
    - Server validates colors and tracks progress
    """

    def __init__(self, rgb: RGBLED, mock: bool = False):
        super().__init__("simon", mock)
        self.rgb = rgb  # Shared RGB LED instance

        self._sequence: list[str] = []
        self._current_index = 0
        self._sequence_thread: Optional[threading.Thread] = None
        self._stop_sequence = threading.Event()

    def setup(self):
        """Initialize hardware (RGB is set up by controller)."""
        pass  # RGB LED is shared and set up by game controller

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        self._sequence = config.get("sequence", [])
        self._current_index = config.get("current_index", 0)
        if self.mock:
            print(f"[Simon] Sequence: {self._sequence}")

    def activate(self):
        """Activate module and start showing sequence on loop."""
        self._state = ModuleState.ACTIVE
        self._stop_sequence.clear()

        if self.mock:
            print(f"[Simon] Activated - showing {len(self._sequence)} colors on loop")

        # Start sequence display loop in background
        self._sequence_thread = threading.Thread(target=self._sequence_loop, daemon=True)
        self._sequence_thread.start()

    def _sequence_loop(self):
        """Continuously show the color sequence."""
        while not self._stop_sequence.is_set() and self._state == ModuleState.ACTIVE:
            for i, color in enumerate(self._sequence):
                if self._stop_sequence.is_set() or self._state != ModuleState.ACTIVE:
                    break

                if self.mock:
                    print(f"[Simon] Showing color {i + 1}/{len(self._sequence)}: {color}")

                # Show color
                self.rgb.set_color(color)
                time.sleep(1.0)

                # Brief off between colors
                self.rgb.off()
                time.sleep(0.3)

            # Pause between sequence repeats
            if not self._stop_sequence.is_set() and self._state == ModuleState.ACTIVE:
                time.sleep(1.5)

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE
        self._stop_sequence.set()
        self.rgb.off()

    def reset(self):
        """Reset module state."""
        self._current_index = 0
        self._stop_sequence.set()
        self.rgb.off()

    def update_progress(self, current_index: int):
        """Update current progress from server."""
        self._current_index = current_index
        if self.mock:
            print(f"[Simon] Progress updated: {current_index}/{len(self._sequence)}")

    def flash_feedback(self, success: bool):
        """Flash LED to indicate correct/wrong answer."""
        self._stop_sequence.set()
        time.sleep(0.1)

        if success:
            self.rgb.flash("green", 0.3)
        else:
            self.rgb.flash("red", 0.5)

        # Resume sequence if still active
        if self._state == ModuleState.ACTIVE:
            self._stop_sequence.clear()
            self._sequence_thread = threading.Thread(target=self._sequence_loop, daemon=True)
            self._sequence_thread.start()

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "current_index": self._current_index,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self._stop_sequence.set()
        self.rgb.off()
        # Don't cleanup RGB - it's shared and cleaned up by controller
