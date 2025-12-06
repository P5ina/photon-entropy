"""Magnet module - apply magnet at the right moment."""
from .base import BaseModule, ModuleState
from hardware.sensors import HallSensor


class MagnetModule(BaseModule):
    """
    Magnet module: apply magnet to Hall sensor when conditions are right.
    - LED color and buzzer state change over time (server controlled)
    - Player must apply magnet when LED is green and buzzer is silent
    - Server validates if conditions were correct
    """

    def __init__(self, hall_pin: int, mock: bool = False):
        super().__init__("magnet", mock)
        self.hall = HallSensor(hall_pin, mock=mock)
        self._magnet_applied = False

    def setup(self):
        """Initialize hardware."""
        self.hall.setup()
        self.hall.on_magnet = self._on_magnet_change

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        if self.mock:
            print(f"[Magnet] Configured: {config}")

    def activate(self):
        """Activate module."""
        self._state = ModuleState.ACTIVE
        self._magnet_applied = False

        if self.mock:
            print("[Magnet] Activated - apply magnet when LED is green and buzzer is silent")

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE

    def reset(self):
        """Reset module state."""
        self._magnet_applied = False

    def _on_magnet_change(self, detected: bool):
        """Handle magnet detection - send to server for validation."""
        if self._state != ModuleState.ACTIVE:
            return

        if detected and not self._magnet_applied:
            self._magnet_applied = True
            if self.mock:
                print("[Magnet] Magnet detected! Sending to server...")

            # Send to server - server will check if conditions are right
            self._report_action("apply_magnet", {})

    def simulate_magnet(self, detected: bool = True):
        """Simulate magnet detection (for testing)."""
        if self.mock:
            self.hall.simulate_magnet(detected)

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "magnet_applied": self._magnet_applied,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self.hall.cleanup()
