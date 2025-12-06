"""Wires module - press the correct button."""
from .base import BaseModule, ModuleState
from hardware.button import ButtonGroup
from hardware.sensors import LEDGroup


class WiresModule(BaseModule):
    """
    Wires module: 4 colored LEDs (Red, Blue, Green, Yellow) with buttons.
    LEDs are static indicators. Player must press the correct button.
    Server validates which button is correct.
    """

    def __init__(self, button_pins: tuple, led_pins: tuple, mock: bool = False):
        super().__init__("wires", mock)
        self.buttons = ButtonGroup(button_pins, mock=mock)
        self.leds = LEDGroup(led_pins, mock=mock)

        # Fixed wire colors: Red(0), Blue(1), Green(2), Yellow(3)
        self.wire_colors = ["red", "blue", "green", "yellow"]
        self._button_states = [False, False, False, False]  # Track pressed buttons

    def setup(self):
        """Initialize hardware."""
        self.buttons.setup()
        self.leds.setup()
        self.buttons.set_all_callbacks(self._on_button_press)

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        # Config only contains display info (wires, cut_wires)
        # Solution (correct button) is hidden - server validates
        if self.mock:
            print(f"[Wires] Configured with: {config}")

    def activate(self):
        """Activate module - turn on all LEDs."""
        self._state = ModuleState.ACTIVE
        self._button_states = [False, False, False, False]

        # Turn on all LEDs (static color indicators)
        self.leds.all_on()

        if self.mock:
            print("[Wires] Activated - waiting for button press")

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE
        self.leds.all_off()

    def reset(self):
        """Reset module state."""
        self._button_states = [False, False, False, False]
        if self._state == ModuleState.ACTIVE:
            self.leds.all_on()

    def _on_button_press(self, index: int):
        """Handle button press - send to server for validation."""
        if self._state != ModuleState.ACTIVE:
            return

        if self._button_states[index]:
            return  # Already pressed this button

        self._button_states[index] = True
        color = self.wire_colors[index]

        # Turn off the LED for this button
        self.leds.set(index, False)

        if self.mock:
            print(f"[Wires] Pressed button {index} ({color})")

        # Report action to server - server will validate and respond
        self._report_action("cut_wire", {"wire": index, "color": color})

    def handle_server_response(self, success: bool, solved: bool = False):
        """Handle validation response from server."""
        if solved:
            self._report_solved()
            if self.mock:
                print("[Wires] SOLVED!")
        elif not success:
            if self.mock:
                print("[Wires] STRIKE from server!")

    def simulate_press(self, button_index: int):
        """Simulate pressing a button (for testing)."""
        if self.mock:
            self._on_button_press(button_index)

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "button_states": self._button_states,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self.leds.all_off()
        self.buttons.cleanup()
        self.leds.cleanup()
