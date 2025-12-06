"""Wires module - cut the correct wire."""
from .base import BaseModule, ModuleState
from hardware.button import ButtonGroup
from hardware.sensors import LEDGroup


class WiresModule(BaseModule):
    """
    Wires module: 4 colored LEDs (Red, Blue, Green, Yellow) with buttons.
    Each game enables/disables some wires (LEDs on/off).
    Player must cut the correct wire based on rules.
    Server validates which wire is correct.
    """

    def __init__(self, button_pins: tuple, led_pins: tuple, mock: bool = False):
        super().__init__("wires", mock)
        self.buttons = ButtonGroup(button_pins, mock=mock)
        self.leds = LEDGroup(led_pins, mock=mock)

        # Wire colors: Red(0), Blue(1), Green(2), Yellow(3)
        self.wire_colors = ["red", "blue", "green", "yellow"]
        self._wire_enabled = [True, True, True, True]  # Which wires exist
        self._wire_cut = [False, False, False, False]  # Which wires are cut

    def setup(self):
        """Initialize hardware."""
        self.buttons.setup()
        self.leds.setup()
        self.buttons.set_all_callbacks(self._on_button_press)

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        # Config contains: wire_enabled (which wires exist)
        self._wire_enabled = config.get("wire_enabled", [True, True, True, True])
        if self.mock:
            enabled_colors = [self.wire_colors[i] for i, e in enumerate(self._wire_enabled) if e]
            print(f"[Wires] Enabled wires: {enabled_colors}")

    def activate(self):
        """Activate module - turn on enabled wire LEDs."""
        self._state = ModuleState.ACTIVE
        self._wire_cut = [False, False, False, False]

        # Turn on only enabled wires
        for i, enabled in enumerate(self._wire_enabled):
            self.leds.set(i, enabled)

        if self.mock:
            enabled_colors = [self.wire_colors[i] for i, e in enumerate(self._wire_enabled) if e]
            print(f"[Wires] Activated - wires present: {enabled_colors}")

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE
        self.leds.all_off()

    def reset(self):
        """Reset module state."""
        self._wire_cut = [False, False, False, False]
        if self._state == ModuleState.ACTIVE:
            for i, enabled in enumerate(self._wire_enabled):
                self.leds.set(i, enabled)

    def _on_button_press(self, index: int):
        """Handle button press (wire cut) - send to server for validation."""
        if self._state != ModuleState.ACTIVE:
            return

        # Can't cut a wire that doesn't exist
        if not self._wire_enabled[index]:
            if self.mock:
                print(f"[Wires] Button {index} pressed but wire not present")
            return

        # Can't cut a wire that's already cut
        if self._wire_cut[index]:
            return

        # Cut the wire - turn off LED
        self._wire_cut[index] = True
        self.leds.set(index, False)

        color = self.wire_colors[index]
        if self.mock:
            print(f"[Wires] Cut wire {index} ({color})")

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

    def simulate_cut(self, wire_index: int):
        """Simulate cutting a wire (for testing)."""
        if self.mock:
            self._on_button_press(wire_index)

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "wire_enabled": self._wire_enabled,
            "wire_cut": self._wire_cut,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self.leds.all_off()
        self.buttons.cleanup()
        self.leds.cleanup()
