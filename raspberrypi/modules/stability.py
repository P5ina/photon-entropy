"""Stability module - keep the device stable."""
import time
import threading
from typing import Optional
from .base import BaseModule, ModuleState
from hardware.sensors import TiltSensor


class StabilityModule(BaseModule):
    """
    Stability module: keep the device stable for a duration.
    - Tilt sensor detects movement
    - Player must keep device still while solving other modules
    - Too many tilts = strike
    """

    def __init__(self, tilt_pin: int, mock: bool = False):
        super().__init__("stability", mock)
        self.tilt = TiltSensor(tilt_pin, mock=mock)

        self._max_tilts = 3  # Maximum allowed tilts
        self._tilt_count = 0
        self._stable_duration = 30  # Seconds to remain stable
        self._stable_time = 0  # Time spent stable
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()

    def setup(self):
        """Initialize hardware."""
        self.tilt.setup()
        self.tilt.on_tilt = self._on_tilt

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        # Config contains: max_tilts, stable_duration
        self._max_tilts = config.get("max_tilts", 3)
        self._stable_duration = config.get("stable_duration", 30)
        if self.mock:
            print(f"[Stability] Max tilts: {self._max_tilts}, duration: {self._stable_duration}s")

    def activate(self):
        """Activate module and start monitoring."""
        self._state = ModuleState.ACTIVE
        self._tilt_count = 0
        self._stable_time = 0
        self._stop_monitor.clear()
        self._monitoring = True
        self.tilt.reset_tilt_count()

        if self.mock:
            print(f"[Stability] Activated - keep stable for {self._stable_duration}s")

        # Start stability monitor
        self._monitor_thread = threading.Thread(target=self._monitor_stability)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE
        self._monitoring = False
        self._stop_monitor.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

    def reset(self):
        """Reset module state."""
        self._tilt_count = 0
        self._stable_time = 0
        self.tilt.reset_tilt_count()

    def _monitor_stability(self):
        """Background stability monitoring."""
        last_tilt_count = 0

        while not self._stop_monitor.is_set() and self._state == ModuleState.ACTIVE:
            current_tilts = self.tilt.get_tilt_count()

            # Check for new tilts
            if current_tilts > last_tilt_count:
                # Tilt detected, reset stable time
                self._stable_time = 0
            else:
                # No tilt, increment stable time
                self._stable_time += 1

            last_tilt_count = current_tilts

            # Report status
            self._report_action("stability_check", {
                "stable_time": self._stable_time,
                "tilt_count": self._tilt_count,
                "max_tilts": self._max_tilts
            })

            # Check if stable long enough
            if self._stable_time >= self._stable_duration:
                self._report_solved()
                if self.mock:
                    print("[Stability] SOLVED! Stayed stable!")
                break

            time.sleep(1)

    def _on_tilt(self):
        """Handle tilt event."""
        if self._state != ModuleState.ACTIVE:
            return

        self._tilt_count += 1
        self._stable_time = 0  # Reset stable counter

        self._report_action("tilt", {
            "count": self._tilt_count,
            "max": self._max_tilts
        })

        if self.mock:
            print(f"[Stability] Tilt! {self._tilt_count}/{self._max_tilts}")

        # Check if too many tilts
        if self._tilt_count >= self._max_tilts:
            self._report_strike(f"Too many tilts: {self._tilt_count}")
            self._tilt_count = 0  # Reset after strike
            if self.mock:
                print(f"[Stability] STRIKE! Too unstable")

    def simulate_tilt(self):
        """Simulate tilt (for testing)."""
        if self.mock:
            self.tilt.simulate_tilt()

    def get_stable_time(self) -> int:
        """Get current stable time."""
        return self._stable_time

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "stable_time": self._stable_time,
            "stable_duration": self._stable_duration,
            "tilt_count": self._tilt_count,
            "max_tilts": self._max_tilts,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self._stop_monitor.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        self.tilt.cleanup()
