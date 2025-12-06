"""Simon module - repeat the color sequence."""
import time
import threading
from typing import Optional
from .base import BaseModule, ModuleState
from hardware.rgb_led import RGBLED
from hardware.sensors import TouchSensor


class SimonModule(BaseModule):
    """
    Simon Says module: watch the color sequence, repeat it with touch sensor.
    - RGB LED shows a sequence of colors
    - Player touches sensor when correct color is shown
    - Sequence gets longer each round
    """

    # Colors used in Simon
    COLORS = ["red", "green", "blue", "yellow"]

    def __init__(self, rgb_pins: tuple, touch_pin: int, mock: bool = False):
        super().__init__("simon", mock)
        self.rgb = RGBLED(rgb_pins[0], rgb_pins[1], rgb_pins[2], mock=mock)
        self.touch = TouchSensor(touch_pin, mock=mock)

        self._sequence: list[str] = []  # Full sequence to match
        self._current_round = 0  # Current round (sequence length)
        self._player_position = 0  # Current position in sequence
        self._showing_sequence = False
        self._current_color_index = 0
        self._sequence_thread: Optional[threading.Thread] = None
        self._stop_sequence = threading.Event()

    def setup(self):
        """Initialize hardware."""
        self.rgb.setup()
        self.touch.setup()
        self.touch.on_touch = self._on_touch

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        # Config contains: sequence (list of color names), rounds (number of rounds)
        self._sequence = config.get("sequence", ["red", "green", "blue"])
        self._total_rounds = config.get("rounds", 3)
        if self.mock:
            print(f"[Simon] Sequence: {self._sequence[:self._total_rounds]}")

    def activate(self):
        """Activate module and start first round."""
        self._state = ModuleState.ACTIVE
        self._current_round = 1
        self._player_position = 0
        self._stop_sequence.clear()

        if self.mock:
            print(f"[Simon] Activated - Round 1/{self._total_rounds}")

        # Show first sequence
        self._show_sequence()

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE
        self._stop_sequence.set()
        if self._sequence_thread:
            self._sequence_thread.join(timeout=1)
        self.rgb.off()

    def reset(self):
        """Reset module state."""
        self._current_round = 1
        self._player_position = 0
        self._stop_sequence.set()
        if self._sequence_thread:
            self._sequence_thread.join(timeout=1)
        self.rgb.off()

    def _show_sequence(self):
        """Show the current sequence to the player."""
        self._showing_sequence = True
        self._player_position = 0

        def display_sequence():
            # Brief pause before starting
            time.sleep(0.5)

            for i in range(self._current_round):
                if self._stop_sequence.is_set():
                    break

                color = self._sequence[i]
                self._current_color_index = i

                self.rgb.set_color(color)
                self._report_action("show_color", {"color": color, "index": i})

                if self.mock:
                    print(f"[Simon] Showing: {color}")

                time.sleep(0.6)
                self.rgb.off()
                time.sleep(0.3)

            self._showing_sequence = False
            self._start_player_input()

        self._sequence_thread = threading.Thread(target=display_sequence)
        self._sequence_thread.daemon = True
        self._sequence_thread.start()

    def _start_player_input(self):
        """Start accepting player input."""
        self._player_position = 0
        self._cycle_colors()

    def _cycle_colors(self):
        """Cycle through colors for player to select."""
        if self._state != ModuleState.ACTIVE or self._showing_sequence:
            return

        def color_cycle():
            color_index = 0
            while not self._stop_sequence.is_set() and self._state == ModuleState.ACTIVE:
                if self._showing_sequence:
                    time.sleep(0.1)
                    continue

                color = self.COLORS[color_index % len(self.COLORS)]
                self._current_color_index = color_index % len(self.COLORS)
                self.rgb.set_color(color)

                time.sleep(0.8)  # Time to see/touch each color
                color_index += 1

        cycle_thread = threading.Thread(target=color_cycle)
        cycle_thread.daemon = True
        cycle_thread.start()

    def _on_touch(self):
        """Handle touch sensor press."""
        if self._state != ModuleState.ACTIVE or self._showing_sequence:
            return

        selected_color = self.COLORS[self._current_color_index]
        expected_color = self._sequence[self._player_position]

        self._report_action("touch", {
            "selected": selected_color,
            "position": self._player_position
        })

        if self.mock:
            print(f"[Simon] Touched: {selected_color}, expected: {expected_color}")

        if selected_color == expected_color:
            self._player_position += 1

            if self.mock:
                print(f"[Simon] Correct! {self._player_position}/{self._current_round}")

            # Flash to confirm
            self.rgb.flash("white", 0.1)

            # Check if round complete
            if self._player_position >= self._current_round:
                self._current_round += 1

                if self._current_round > self._total_rounds:
                    # All rounds complete!
                    self._report_solved()
                    self.rgb.set_color("green")
                    if self.mock:
                        print("[Simon] SOLVED!")
                else:
                    # Next round
                    if self.mock:
                        print(f"[Simon] Round {self._current_round}/{self._total_rounds}")
                    time.sleep(0.5)
                    self._show_sequence()
        else:
            self._report_strike(f"Wrong color: {selected_color}, expected {expected_color}")
            self.rgb.flash("red", 0.3)
            # Reset to beginning of current round
            self._player_position = 0
            if self.mock:
                print(f"[Simon] STRIKE! Reset to round start")

    def simulate_touch(self):
        """Simulate touch (for testing)."""
        if self.mock:
            self.touch.simulate_tap()

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "current_round": self._current_round,
            "total_rounds": self._total_rounds,
            "player_position": self._player_position,
            "showing_sequence": self._showing_sequence,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self._stop_sequence.set()
        if self._sequence_thread:
            self._sequence_thread.join(timeout=1)
        self.rgb.cleanup()
        self.touch.cleanup()
