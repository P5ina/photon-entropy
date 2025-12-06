"""Wires module - cut the correct wires in order."""
from typing import Optional
from .base import BaseModule, ModuleState
from hardware.button import ButtonGroup
from hardware.sensors import LEDGroup


class WiresModule(BaseModule):
    """
    Wires module: 4 colored wires (LEDs) with buttons to "cut" them.
    Player must cut wires in the correct order based on rules.
    """

    def __init__(self, button_pins: tuple, led_pins: tuple, mock: bool = False):
        super().__init__("wires", mock)
        self.buttons = ButtonGroup(button_pins, mock=mock)
        self.leds = LEDGroup(led_pins, mock=mock)

        # Wire colors: Red, Blue, Green, Yellow (index 0-3)
        self.wire_colors = ["red", "blue", "green", "yellow"]
        self._cut_order: list[int] = []  # Required cut order
        self._cuts_made: list[int] = []  # Wires already cut
        self._wire_states: list[bool] = [True, True, True, True]  # True = intact

    def setup(self):
        """Initialize hardware."""
        self.buttons.setup()
        self.leds.setup()
        self.buttons.set_all_callbacks(self._on_button_press)

    def configure(self, config: dict):
        """Configure with game rules."""
        super().configure(config)
        # Config contains: wire_order (list of wire indices to cut in order)
        self._cut_order = config.get("wire_order", [])
        if self.mock:
            print(f"[Wires] Cut order: {self._cut_order}")

    def activate(self):
        """Activate module - turn on all wire LEDs."""
        self._state = ModuleState.ACTIVE
        self._cuts_made = []
        self._wire_states = [True, True, True, True]

        # Turn on all LEDs (wires intact)
        self.leds.all_on()

        if self.mock:
            print(f"[Wires] Activated - cut order: {[self.wire_colors[i] for i in self._cut_order]}")

    def deactivate(self):
        """Deactivate module."""
        self._state = ModuleState.INACTIVE
        self.leds.all_off()

    def reset(self):
        """Reset module state."""
        self._cuts_made = []
        self._wire_states = [True, True, True, True]
        if self._state == ModuleState.ACTIVE:
            self.leds.all_on()

    def _on_button_press(self, index: int):
        """Handle button press (wire cut attempt)."""
        if self._state != ModuleState.ACTIVE:
            return

        # Check if wire already cut
        if not self._wire_states[index]:
            return

        # Cut the wire (turn off LED)
        self._wire_states[index] = False
        self.leds.set(index, False)

        color = self.wire_colors[index]
        self._report_action("cut_wire", {"wire": index, "color": color})

        if self.mock:
            print(f"[Wires] Cut wire {index} ({color})")

        # Check if correct
        expected_index = len(self._cuts_made)
        if expected_index < len(self._cut_order):
            expected_wire = self._cut_order[expected_index]
            if index == expected_wire:
                self._cuts_made.append(index)
                if self.mock:
                    print(f"[Wires] Correct! {len(self._cuts_made)}/{len(self._cut_order)}")

                # Check if all correct wires cut
                if len(self._cuts_made) == len(self._cut_order):
                    self._report_solved()
                    if self.mock:
                        print("[Wires] SOLVED!")
            else:
                self._report_strike(f"Wrong wire: cut {color}, expected {self.wire_colors[expected_wire]}")
                if self.mock:
                    print(f"[Wires] STRIKE! Wrong wire")

    def simulate_cut(self, wire_index: int):
        """Simulate cutting a wire (for testing)."""
        if self.mock:
            self._on_button_press(wire_index)

    def get_state(self) -> dict:
        """Get current module state for sync."""
        return {
            "wire_states": self._wire_states,
            "cuts_made": self._cuts_made,
            "solved": self.is_solved,
        }

    def cleanup(self):
        """Clean up hardware."""
        self.leds.all_off()
        self.buttons.cleanup()
        self.leds.cleanup()
