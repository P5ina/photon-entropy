"""Game controller - manages all game modules and state."""
import asyncio
from typing import Optional, Callable
from enum import Enum

from config import Config
from hardware.lcd import LCD
from hardware.buzzer import Buzzer
from modules import (
    WiresModule,
    KeypadModule,
    SimonModule,
    MagnetModule,
    ModuleState,
)
from network.ws_client import GameClient


class GamePhase(Enum):
    """Game phases."""
    IDLE = "idle"
    WAITING = "waiting"
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


class GameController:
    """Main game controller."""

    def __init__(self, config: Config):
        self.config = config
        self.mock = config.mock_hardware

        # Game state
        self.phase = GamePhase.IDLE
        self.game_id: Optional[str] = None
        self.time_remaining = 0
        self.strikes = 0
        self.max_strikes = 3

        # Hardware
        self.lcd = LCD(config.lcd_address, mock=self.mock)
        self.buzzer = Buzzer(config.buzzer_pin, mock=self.mock)

        # Modules
        self.wires = WiresModule(
            config.wire_buttons,
            config.wire_leds,
            mock=self.mock
        )
        self.keypad = KeypadModule(
            config.rotary_clk,
            config.rotary_dt,
            config.rotary_sw,
            mock=self.mock
        )
        self.simon = SimonModule(
            (config.rgb_red, config.rgb_green, config.rgb_blue),
            config.touch_pin,
            mock=self.mock
        )
        self.magnet = MagnetModule(config.hall_pin, mock=self.mock)

        self.modules = {
            "wires": self.wires,
            "keypad": self.keypad,
            "simon": self.simon,
            "magnet": self.magnet,
        }

        # Network
        self.client: Optional[GameClient] = None

        # Callbacks
        self.on_game_won: Optional[Callable[[], None]] = None
        self.on_game_lost: Optional[Callable[[str], None]] = None

    def setup(self):
        """Initialize all hardware."""
        print("[Controller] Setting up hardware...")

        self.lcd.setup()
        self.buzzer.setup()

        for name, module in self.modules.items():
            print(f"[Controller] Setting up {name}...")
            module.setup()
            module.on_solved = lambda n=name: self._on_module_solved(n)
            module.on_strike = lambda r, n=name: self._on_module_strike(n, r)
            module.on_action = lambda a, d, n=name: self._on_module_action(n, a, d)

        self.lcd.show_message("BOMB DEFUSAL", "Ready...")
        print("[Controller] Hardware ready!")

    async def connect(self, server_url: str):
        """Connect to game server."""
        self.client = GameClient(server_url, self.config.device_id)

        # Set up callbacks
        self.client.on_connect = self._on_connected
        self.client.on_disconnect = self._on_disconnected
        self.client.on_game_started = self._on_game_started
        self.client.on_timer_tick = self._on_timer_tick
        self.client.on_strike = self._on_server_strike
        self.client.on_game_won = self._on_server_game_won
        self.client.on_game_lost = self._on_server_game_lost

        await self.client.connect()
        self.lcd.show_message("Connected!", "Waiting...")

    def _on_connected(self):
        """Handle connection."""
        self.phase = GamePhase.WAITING
        print("[Controller] Connected to server")

    def _on_disconnected(self):
        """Handle disconnection."""
        self.phase = GamePhase.IDLE
        self.lcd.show_message("Disconnected", "Reconnecting...")
        print("[Controller] Disconnected from server")

    def _on_game_started(self, data: dict):
        """Handle game start."""
        self.phase = GamePhase.PLAYING
        self.game_id = data.get("game_id")
        self.time_remaining = data.get("time_limit", 300)
        self.strikes = 0
        self.max_strikes = data.get("max_strikes", 3)

        # Configure modules from server data
        modules_config = data.get("modules", {})
        for name, config in modules_config.items():
            if name in self.modules:
                self.modules[name].configure(config)

        # Activate all modules
        for module in self.modules.values():
            module.activate()

        self.lcd.show_timer(self.time_remaining)
        self.buzzer.tick()
        print(f"[Controller] Game started! Time: {self.time_remaining}s")

    def _on_timer_tick(self, remaining: int):
        """Handle timer tick from server."""
        self.time_remaining = remaining
        self.lcd.show_timer(remaining)

        # Tick sound every second, faster when low
        if remaining <= 10:
            self.buzzer.tick()
        elif remaining % 5 == 0:
            self.buzzer.tick()

    def _on_module_solved(self, module_name: str):
        """Handle module solved."""
        print(f"[Controller] Module solved: {module_name}")
        self.buzzer.play_pattern("success")

        if self.client and self.game_id:
            asyncio.create_task(
                self.client.report_module_solved(module_name)
            )

        # Check if all modules solved
        all_solved = all(m.is_solved for m in self.modules.values())
        if all_solved:
            self._game_won()

    def _on_module_strike(self, module_name: str, reason: str):
        """Handle strike from module."""
        self.strikes += 1
        print(f"[Controller] Strike! {self.strikes}/{self.max_strikes} - {reason}")
        self.buzzer.play_pattern("error")
        self.lcd.show_strikes(self.strikes, self.max_strikes)

        if self.client and self.game_id:
            asyncio.create_task(
                self.client.report_strike(module_name, reason)
            )

        # Check for game over
        if self.strikes >= self.max_strikes:
            self._game_lost("Too many strikes!")

    def _on_module_action(self, module_name: str, action: str, data):
        """Handle module action."""
        if self.client and self.game_id:
            asyncio.create_task(
                self.client.report_module_action(module_name, action, data or {})
            )

    def _on_server_strike(self, count: int):
        """Handle strike count from server."""
        self.strikes = count

    def _on_server_game_won(self):
        """Handle game won from server."""
        self._game_won()

    def _on_server_game_lost(self, reason: str):
        """Handle game lost from server."""
        self._game_lost(reason)

    def _game_won(self):
        """Handle game win."""
        self.phase = GamePhase.WON

        # Deactivate all modules
        for module in self.modules.values():
            module.deactivate()

        self.lcd.show_message("DEFUSED!", f"Time: {self.time_remaining}s")
        self.buzzer.play_pattern("success")
        self.buzzer.play_pattern("success")

        print("[Controller] GAME WON!")
        if self.on_game_won:
            self.on_game_won()

    def _game_lost(self, reason: str):
        """Handle game loss."""
        self.phase = GamePhase.LOST

        # Deactivate all modules
        for module in self.modules.values():
            module.deactivate()

        self.lcd.show_explosion()
        self.buzzer.play_pattern("explosion")

        print(f"[Controller] GAME LOST: {reason}")
        if self.on_game_lost:
            self.on_game_lost(reason)

    async def join_game(self, game_id: str):
        """Join a game."""
        if self.client:
            await self.client.join_game(game_id)
            self.game_id = game_id
            self.lcd.show_message("Joining...", game_id[:16])

    async def run(self):
        """Main game loop."""
        if self.client:
            await self.client.listen()

    def reset(self):
        """Reset game state."""
        self.phase = GamePhase.WAITING
        self.game_id = None
        self.time_remaining = 0
        self.strikes = 0

        for module in self.modules.values():
            module.reset()

        self.lcd.show_message("BOMB DEFUSAL", "Waiting...")

    def cleanup(self):
        """Clean up all resources."""
        print("[Controller] Cleaning up...")

        for module in self.modules.values():
            module.cleanup()

        self.buzzer.cleanup()
        self.lcd.cleanup()

        print("[Controller] Cleanup complete")
