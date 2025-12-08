"""Game controller - manages all game modules and state."""
import asyncio
from typing import Optional, Callable
from enum import Enum

from config import Config
from hardware.lcd import LCD
from hardware.buzzer import Buzzer
from modules import (
    WiresModule,
    SimonModule,
    MagnetModule,
    ModuleState,
)
from network.ws_client import GameClient
from network.connectivity import wait_for_connection_async


class GamePhase(Enum):
    """Game phases."""
    IDLE = "idle"
    WAITING = "waiting"
    RECONNECTING = "reconnecting"
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
        self.active_module_index = 0

        # Module ID mapping: type -> server module ID
        self.module_ids: dict[str, str] = {}
        # Module order list (matches server order)
        self.module_order: list[str] = []

        # Event loop reference for thread-safe async calls
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Hardware
        self.lcd = LCD(config.lcd_address, mock=self.mock)
        self.buzzer = Buzzer(config.buzzer_pin, mock=self.mock)

        # Shared RGB LED for Simon and Magnet modules
        from hardware.rgb_led import RGBLED
        self.rgb_led = RGBLED(config.rgb_red, config.rgb_green, config.rgb_blue, mock=self.mock)

        # Modules
        self.wires = WiresModule(
            config.wire_buttons,
            config.wire_leds,
            mock=self.mock
        )
        self.simon = SimonModule(
            rgb=self.rgb_led,
            mock=self.mock
        )
        self.magnet = MagnetModule(
            config.hall_pin,
            rgb=self.rgb_led,
            buzzer=self.buzzer,
            mock=self.mock
        )

        self.modules = {
            "wires": self.wires,
            "simon": self.simon,
            "magnet": self.magnet,
        }

        # Network
        self.client: Optional[GameClient] = None

        # Callbacks
        self.on_game_won: Optional[Callable[[], None]] = None
        self.on_game_lost: Optional[Callable[[str], None]] = None

        # Restart event
        self._restart_event: Optional[asyncio.Event] = None

        # Reconnect event for handling connection loss
        self._reconnect_event: Optional[asyncio.Event] = None

    def setup(self):
        """Initialize all hardware."""
        print("[Controller] Setting up hardware...")

        self.lcd.setup()
        self.buzzer.setup()
        self.rgb_led.setup()

        for name, module in self.modules.items():
            print(f"[Controller] Setting up {name}...")
            module.setup()
            module.on_solved = lambda n=name: self._on_module_solved(n)
            module.on_strike = lambda r, n=name: self._on_module_strike(n, r)
            module.on_action = lambda a, d, n=name: self._on_module_action(n, a, d)

        self.lcd.show_idle()
        print("[Controller] Hardware ready!")

    async def connect(self, server_url: str):
        """Connect to game server."""
        self.client = GameClient(server_url, self.config.device_id)

        # Set up callbacks
        self.client.on_connect = self._on_connected
        self.client.on_disconnect = self._on_disconnected
        self.client.on_game_created = self._on_game_created
        self.client.on_game_started = self._on_game_started
        self.client.on_timer_tick = self._on_timer_tick
        self.client.on_module_solved = self._on_server_module_solved
        self.client.on_strike = self._on_server_strike
        self.client.on_game_won = self._on_server_game_won
        self.client.on_game_lost = self._on_server_game_lost
        self.client.on_magnet_state = self._on_magnet_state

        await self.client.connect()
        self.lcd.show_waiting()

    def _on_connected(self):
        """Handle connection."""
        self.phase = GamePhase.WAITING
        print("[Controller] Connected to server")

    def _on_game_created(self, data: dict):
        """Handle game created - display code on LCD."""
        self.game_id = data.get("game_id", "")
        game_code = data.get("code", "")
        print(f"[Controller] Game created: {game_code}")
        self.lcd.show_game_code(game_code)

    def _on_disconnected(self):
        """Handle disconnection."""
        previous_phase = self.phase
        self.phase = GamePhase.RECONNECTING
        self.lcd.show_reconnecting()
        print("[Controller] Disconnected from server")

        # If we were in a game, notify user that game progress may be lost
        if previous_phase == GamePhase.PLAYING:
            print("[Controller] WARNING: Disconnected during active game!")

        # Signal that reconnection is needed
        if self._reconnect_event and self._loop:
            self._loop.call_soon_threadsafe(self._reconnect_event.set)

    def _on_game_started(self, data: dict):
        """Handle game start."""
        self.phase = GamePhase.PLAYING
        self.game_id = data.get("game_id")

        # Restore button callbacks that may have been replaced by restart listeners
        self.wires.buttons.set_all_callbacks(self.wires._on_button_press)

        # Server wraps game data inside "data" field
        game_data = data.get("data", data)
        self.time_remaining = game_data.get("time_limit", 300)
        self.strikes = 0
        self.max_strikes = game_data.get("max_strikes", 3)
        self.active_module_index = game_data.get("active_module_index", 0)

        # Configure modules from server data
        # Server sends modules as array: [{"id": "...", "type": "wires", "config": {...}, "state": "active/inactive"}, ...]
        modules_list = game_data.get("modules", [])
        print(f"[Controller] Received {len(modules_list)} modules")
        self.module_ids = {}  # Reset module ID mapping
        self.module_order = []  # Track order for sequential activation

        for module_data in modules_list:
            module_id = module_data.get("id")
            module_type = module_data.get("type")
            module_config = module_data.get("config", {})
            module_state = module_data.get("state", "inactive")

            if module_type in self.modules:
                # Store module ID mapping and order
                self.module_ids[module_type] = module_id
                self.module_order.append(module_type)
                print(f"[Controller] Configuring {module_type} (id={module_id}, state={module_state})")
                self.modules[module_type].configure(module_config)

                # Only activate the first active module (sequential play)
                if module_state == "active":
                    print(f"[Controller] Activating {module_type}")
                    self.modules[module_type].activate()

        # Show initial game state on LCD
        active_type = ""
        if self.module_order and self.active_module_index < len(self.module_order):
            active_type = self.module_order[self.active_module_index]

        self.lcd.show_playing(self.time_remaining, self.strikes, active_type)
        print(f"[Controller] Game started! Time: {self.time_remaining}s, Active module: {active_type}")

        self.buzzer.tick()

    def _on_timer_tick(self, remaining: int):
        """Handle timer tick from server."""
        # Ignore timer ticks if game is not playing
        if self.phase != GamePhase.PLAYING:
            return

        self.time_remaining = remaining
        self.lcd.show_timer(remaining, self.strikes)

        # Show current active module
        if self.module_order and self.active_module_index < len(self.module_order):
            active_module = self.module_order[self.active_module_index]
            self.lcd.show_module(active_module)

        # Tick sound every second, faster when low
        if remaining <= 10:
            self.buzzer.tick()
        elif remaining % 5 == 0:
            self.buzzer.tick()

    def _on_module_solved(self, module_name: str):
        """Handle module solved (from local module)."""
        print(f"[Controller] Module solved: {module_name}")
        self.buzzer.play_pattern("success")

        # Deactivate the solved module
        if module_name in self.modules:
            self.modules[module_name].deactivate()

        if self.client and self.game_id:
            asyncio.create_task(
                self.client.report_module_solved(module_name)
            )

        # Server will tell us which module to activate next via module_solved event
        # Check if all modules solved (fallback)
        all_solved = all(m.is_solved for m in self.modules.values())
        if all_solved:
            self._game_won()

    def _activate_next_module(self, next_module_id: str):
        """Activate the next module after current one is solved."""
        # Find module type by ID
        next_module_type = None
        for mod_type, mod_id in self.module_ids.items():
            if mod_id == next_module_id:
                next_module_type = mod_type
                break

        if next_module_type and next_module_type in self.modules:
            print(f"[Controller] Activating next module: {next_module_type}")
            self.modules[next_module_type].activate()
            self.active_module_index += 1

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
        if self.client and self.game_id and self._loop:
            # Get the server module ID for this module type
            module_id = self.module_ids.get(module_name, module_name)
            # Use thread-safe method to schedule coroutine from another thread
            asyncio.run_coroutine_threadsafe(
                self.client.report_module_action(module_id, action, data or {}),
                self._loop
            )

    def _on_server_module_solved(self, module_id: str, next_module_id: str):
        """Handle module solved from server (triggered by expert's actions on mobile)."""
        print(f"[Controller] Server: module {module_id} solved, next: {next_module_id}")
        self.buzzer.play_pattern("success")

        # Find and deactivate the solved module
        for mod_type, mod_id in self.module_ids.items():
            if mod_id == module_id:
                if mod_type in self.modules:
                    self.modules[mod_type].deactivate()
                    self.modules[mod_type]._state = ModuleState.SOLVED
                break

        # Activate next module if provided
        if next_module_id:
            self._activate_next_module(next_module_id)

    def _on_server_strike(self, count: int):
        """Handle strike count from server."""
        self.strikes = count
        self.buzzer.play_pattern("error")

    def _on_magnet_state(self, led_color: str, buzzer_active: bool):
        """Handle magnet module state update from server."""
        if self.phase != GamePhase.PLAYING:
            return

        print(f"[Controller] Magnet state: LED={led_color}, Buzzer={buzzer_active}")
        self.magnet.set_state(led_color, buzzer_active)

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

        self.lcd.show_win(self.time_remaining)
        self.buzzer.play_pattern("success")
        self.buzzer.play_pattern("success")

        print("[Controller] GAME WON!")
        if self.on_game_won:
            self.on_game_won()

        # Schedule restart prompt
        self._schedule_restart_prompt()

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

        # Schedule restart prompt
        self._schedule_restart_prompt()

    def create_game(self):
        """Create a new game and display code on LCD."""
        if self.client:
            self.lcd.write("Creating game...", "")
            result = self.client.create_game()
            if not result:
                self.lcd.write("Failed to", "create game")

    def join_game_by_code(self, code: str):
        """Join a game by code via REST API."""
        if self.client:
            self.lcd.write("Joining...", code[:16])
            result = self.client.join_game_http(code)
            if result:
                self.game_id = result.get("game_id")
            else:
                self.lcd.write("Failed to", "join game")

    async def join_game(self, game_id: str):
        """Join a game."""
        if self.client:
            await self.client.join_game(game_id)
            self.game_id = game_id
            self.lcd.show_message("Joining...", game_id[:16])

    async def run(self):
        """Main game loop."""
        # Store event loop reference for thread-safe async calls
        self._loop = asyncio.get_running_loop()
        self._reconnect_event = asyncio.Event()

        if self.client:
            # Run listening with reconnection support
            while True:
                try:
                    await self.client.listen()
                except Exception as e:
                    print(f"[Controller] Connection error: {e}")

                # Check if we need to reconnect
                if self.phase == GamePhase.RECONNECTING:
                    reconnected = await self._attempt_reconnection()
                    if reconnected:
                        continue
                    else:
                        # Failed to reconnect, exit loop
                        break
                else:
                    # Normal exit (game ended or shutdown)
                    break

    async def _attempt_reconnection(self, max_retries: int = 10) -> bool:
        """Attempt to reconnect to the server."""
        server_url = self.client.server_url if self.client else self.config.server_url

        attempt = 0

        def on_waiting(retry_attempt: int):
            self.lcd.show_reconnecting(retry_attempt)

        # Wait for connectivity
        connected = await wait_for_connection_async(
            server_url,
            on_waiting=on_waiting,
            check_interval=3.0,
            max_attempts=max_retries
        )

        if not connected:
            self.lcd.write("Reconnect", "Failed!")
            print("[Controller] Failed to reconnect after max retries")
            return False

        # Try to reconnect WebSocket
        try:
            self.lcd.write("Reconnecting...", "")
            await self.client.connect()
            self.phase = GamePhase.WAITING
            self.lcd.show_waiting()
            print("[Controller] Reconnected successfully!")

            # If we had a game in progress, try to rejoin
            if self.game_id and self.client.game_code:
                self.lcd.write("Rejoining...", self.client.game_code[:16])
                result = self.client.join_game_http(self.client.game_code)
                if result:
                    self.lcd.show_game_code(self.client.game_code)
                    print(f"[Controller] Rejoined game: {self.client.game_code}")
                else:
                    # Game may have ended, just wait for a new game
                    self.game_id = None
                    self.lcd.show_waiting()

            return True
        except Exception as e:
            print(f"[Controller] Reconnection failed: {e}")
            return False

    def reset(self):
        """Reset game state."""
        self.phase = GamePhase.WAITING
        self.game_id = None
        self.time_remaining = 0
        self.strikes = 0
        self._restart_event = None
        self._reconnect_event = None

        for module in self.modules.values():
            module.reset()

        self.lcd.show_waiting()

    def _schedule_restart_prompt(self):
        """Show restart prompt after game ends."""
        import threading

        def show_prompt():
            import time
            time.sleep(3)  # Wait 3 seconds to show result
            if self.phase in (GamePhase.WON, GamePhase.LOST):
                self.lcd.show_restart_prompt()
                print("[Controller] Press any button to restart...")
                # Set up button listeners for restart
                self._setup_restart_listeners()

        thread = threading.Thread(target=show_prompt, daemon=True)
        thread.start()

    def _setup_restart_listeners(self):
        """Set up button listeners to trigger restart."""
        # Use the wire buttons to trigger restart
        def restart_on_any_button(index: int):
            if self.phase in (GamePhase.WON, GamePhase.LOST):
                print(f"[Controller] Restart triggered by button {index}")
                self._trigger_restart()

        self.wires.buttons.set_all_callbacks(restart_on_any_button)

    def _trigger_restart(self):
        """Trigger game restart."""
        if self._restart_event and self._loop:
            self._loop.call_soon_threadsafe(self._restart_event.set)

    async def wait_for_restart(self):
        """Wait for restart to be triggered."""
        self._restart_event = asyncio.Event()
        await self._restart_event.wait()

    async def disconnect(self):
        """Disconnect from server."""
        if self.client:
            await self.client.disconnect()

    def cleanup(self):
        """Clean up all resources."""
        print("[Controller] Cleaning up...")

        for module in self.modules.values():
            module.cleanup()

        self.rgb_led.cleanup()
        self.buzzer.cleanup()
        self.lcd.cleanup()

        print("[Controller] Cleanup complete")
