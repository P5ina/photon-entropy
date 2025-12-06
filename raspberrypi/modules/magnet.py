"""Magnet module - apply magnet at the right moment."""
import time
import threading
from typing import Optional
from .base import BaseModule, ModuleState
from hardware.sensors import HallSensor


class MagnetModule(BaseModule):
    """
    Magnet module: apply magnet to Hall sensor at specific times.
    - Timer counts through zones
    - Player must apply magnet during correct time window
    - Based on rules, specific zones are "safe"
    """

    def __init__(self, hall_pin: int, mock: bool = False):
        super().__init__("magnet", mock)
        self.hall = HallSensor(hall_pin, mock=mock)

        self._safe_zones: list[tuple[int, int]] = []  # (start_second, end_second)
        self._required_applications = 0
        self._successful_applications = 0
        self._current_time = 0
        self._magnet_was_applied = False
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_timer = threading.Event()

    def setup(self):
        """Initialize hardware."""
        self.hall.setup()
        self.hall.on_magnet = self._on_magnet_change

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        # Config contains: safe_zones (list of (start, end) tuples), required (number)
        self._safe_zones = config.get("safe_zones", [(5, 10), (20, 25)])
        self._required_applications = config.get("required", 2)
        if self.mock:
            print(f"[Magnet] Safe zones: {self._safe_zones}, required: {self._required_applications}")

    def activate(self):
        """Activate module and start timer."""
        self._state = ModuleState.ACTIVE
        self._successful_applications = 0
        self._current_time = 0
        self._magnet_was_applied = False
        self._stop_timer.clear()

        if self.mock:
            print(f"[Magnet] Activated - need {self._required_applications} magnet applications")

        # Start timer thread
        self._timer_thread = threading.Thread(target=self._timer_loop)
        self._timer_thread.daemon = True
        self._timer_thread.start()

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE
        self._stop_timer.set()
        if self._timer_thread:
            self._timer_thread.join(timeout=1)

    def reset(self):
        """Reset module state."""
        self._successful_applications = 0
        self._current_time = 0
        self._magnet_was_applied = False

    def _timer_loop(self):
        """Background timer loop."""
        while not self._stop_timer.is_set() and self._state == ModuleState.ACTIVE:
            self._current_time += 1

            # Check if we're in a safe zone
            in_safe_zone = self._is_in_safe_zone(self._current_time)

            # Report time tick
            self._report_action("tick", {
                "time": self._current_time,
                "in_safe_zone": in_safe_zone
            })

            # Reset magnet flag when entering new zone
            if in_safe_zone and not self._was_in_safe_zone(self._current_time - 1):
                self._magnet_was_applied = False

            time.sleep(1)

    def _is_in_safe_zone(self, t: int) -> bool:
        """Check if time is in a safe zone."""
        for start, end in self._safe_zones:
            if start <= t <= end:
                return True
        return False

    def _was_in_safe_zone(self, t: int) -> bool:
        """Check if previous time was in same safe zone."""
        if t < 0:
            return False
        return self._is_in_safe_zone(t)

    def _on_magnet_change(self, detected: bool):
        """Handle magnet detection change."""
        if self._state != ModuleState.ACTIVE:
            return

        if detected:
            in_safe_zone = self._is_in_safe_zone(self._current_time)

            self._report_action("magnet_applied", {
                "time": self._current_time,
                "in_safe_zone": in_safe_zone
            })

            if self.mock:
                print(f"[Magnet] Applied at t={self._current_time}, safe={in_safe_zone}")

            if in_safe_zone:
                if not self._magnet_was_applied:
                    self._magnet_was_applied = True
                    self._successful_applications += 1

                    if self.mock:
                        print(f"[Magnet] Success! {self._successful_applications}/{self._required_applications}")

                    # Check if complete
                    if self._successful_applications >= self._required_applications:
                        self._report_solved()
                        if self.mock:
                            print("[Magnet] SOLVED!")
            else:
                self._report_strike(f"Magnet applied at wrong time: {self._current_time}")
                if self.mock:
                    print(f"[Magnet] STRIKE! Wrong timing")

    def simulate_magnet(self, detected: bool = True):
        """Simulate magnet detection (for testing)."""
        if self.mock:
            self.hall.simulate_magnet(detected)

    def get_current_time(self) -> int:
        """Get current timer value."""
        return self._current_time

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "current_time": self._current_time,
            "successful_applications": self._successful_applications,
            "required": self._required_applications,
            "in_safe_zone": self._is_in_safe_zone(self._current_time),
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self._stop_timer.set()
        if self._timer_thread:
            self._timer_thread.join(timeout=1)
        self.hall.cleanup()
