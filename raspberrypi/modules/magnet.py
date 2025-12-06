"""Magnet module - apply magnet at the right moment."""
from .base import BaseModule, ModuleState
from hardware.sensors import HallSensor
from hardware.rgb_led import RGBLED
from hardware.buzzer import Buzzer


class MagnetModule(BaseModule):
    """
    Magnet module: apply magnet to Hall sensor when conditions are right.
    - LED color and buzzer state change over time (server controlled)
    - Player must apply magnet when LED is green and buzzer is silent
    - Server validates if conditions were correct
    """

    def __init__(self, hall_pin: int, rgb: RGBLED = None, buzzer: Buzzer = None, mock: bool = False):
        super().__init__("magnet", mock)
        self.hall = HallSensor(hall_pin, mock=mock)
        self._magnet_applied = False

        # RGB LED for showing state (shared with Simon)
        self.rgb = rgb  # Shared RGB LED instance

        # Buzzer reference (shared with game controller)
        self.buzzer = buzzer

        # Current state
        self._led_color = "red"
        self._buzzer_active = False

    def setup(self):
        """Initialize hardware (RGB is set up by controller)."""
        self.hall.setup()
        self.hall.on_magnet = self._on_magnet_change
        # RGB LED is shared and set up by game controller

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        if self.mock:
            print(f"[Magnet] Configured: {config}")

    def activate(self):
        """Activate module."""
        self._state = ModuleState.ACTIVE
        self._magnet_applied = False

        # Start with initial state
        self.set_state("red", True)

        if self.mock:
            print("[Magnet] Activated - apply magnet when LED is green and buzzer is silent")

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE

        # Turn off LED and buzzer
        if self.rgb:
            self.rgb.off()
        if self.buzzer:
            self.buzzer.off()

    def reset(self):
        """Reset module state."""
        self._magnet_applied = False
        self._led_color = "red"
        self._buzzer_active = False

    def set_state(self, led_color: str, buzzer_active: bool):
        """Set LED color and buzzer state (called by game controller from server events)."""
        if self._state != ModuleState.ACTIVE:
            return

        self._led_color = led_color
        self._buzzer_active = buzzer_active

        # Update RGB LED
        if self.rgb:
            self.rgb.set_color(led_color)

        # Update buzzer
        if self.buzzer:
            if buzzer_active:
                self.buzzer.on()
            else:
                self.buzzer.off()

        if self.mock:
            print(f"[Magnet] State: LED={led_color}, Buzzer={'ON' if buzzer_active else 'OFF'}")

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

            # Reset for next attempt (in case of strike)
            self._magnet_applied = False

    def simulate_magnet(self, detected: bool = True):
        """Simulate magnet detection (for testing)."""
        if self.mock:
            self.hall.simulate_magnet(detected)

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "magnet_applied": self._magnet_applied,
            "led_color": self._led_color,
            "buzzer_active": self._buzzer_active,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self.hall.cleanup()
        if self.rgb:
            self.rgb.off()
        # Don't cleanup RGB - it's shared and cleaned up by controller
