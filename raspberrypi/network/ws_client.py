"""WebSocket client for game server communication."""
import asyncio
import json
from typing import Callable, Optional, Any
import websockets
from websockets.exceptions import ConnectionClosed
import requests


class WebSocketClient:
    """WebSocket client for real-time game communication."""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._running = False

        # Message handlers by type
        self._handlers: dict[str, list[Callable]] = {}

        # Connection callbacks
        self.on_connect: Optional[Callable[[], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

    @property
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._connected

    def register_handler(self, message_type: str, handler: Callable[[dict], None]):
        """Register a handler for a specific message type."""
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)

    def unregister_handler(self, message_type: str, handler: Callable[[dict], None]):
        """Unregister a handler."""
        if message_type in self._handlers:
            self._handlers[message_type].remove(handler)

    async def connect(self):
        """Connect to WebSocket server."""
        try:
            self._ws = await websockets.connect(self.server_url)
            self._connected = True
            print(f"[WS] Connected to {self.server_url}")

            if self.on_connect:
                self.on_connect()

        except Exception as e:
            print(f"[WS] Connection error: {e}")
            self._connected = False
            if self.on_error:
                self.on_error(e)
            raise

    async def disconnect(self):
        """Disconnect from server."""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        self._connected = False
        print("[WS] Disconnected")

        if self.on_disconnect:
            self.on_disconnect()

    async def send(self, message_type: str, data: dict = None):
        """Send a message to the server."""
        if not self._connected or not self._ws:
            print("[WS] Not connected, cannot send")
            return

        message = {
            "type": message_type,
            "data": data or {}
        }

        try:
            await self._ws.send(json.dumps(message))
        except Exception as e:
            print(f"[WS] Send error: {e}")
            if self.on_error:
                self.on_error(e)

    async def send_action(self, module: str, action: str, data: dict = None):
        """Send a game action."""
        await self.send("module_action", {
            "module": module,
            "action": action,
            **(data or {})
        })

    async def listen(self):
        """Start listening for messages."""
        self._running = True

        while self._running and self._connected:
            try:
                message = await self._ws.recv()
                await self._handle_message(message)

            except ConnectionClosed:
                print("[WS] Connection closed by server")
                self._connected = False
                if self.on_disconnect:
                    self.on_disconnect()
                break

            except Exception as e:
                print(f"[WS] Receive error: {e}")
                if self.on_error:
                    self.on_error(e)

    async def _handle_message(self, raw_message: str):
        """Handle incoming message."""
        try:
            message = json.loads(raw_message)
            msg_type = message.get("type", "unknown")
            data = message.get("data", {})

            # Call registered handlers
            if msg_type in self._handlers:
                for handler in self._handlers[msg_type]:
                    try:
                        handler(data)
                    except Exception as e:
                        print(f"[WS] Handler error for {msg_type}: {e}")

            # Also call wildcard handlers
            if "*" in self._handlers:
                for handler in self._handlers["*"]:
                    try:
                        handler({"type": msg_type, "data": data})
                    except Exception as e:
                        print(f"[WS] Wildcard handler error: {e}")

        except json.JSONDecodeError as e:
            print(f"[WS] Invalid JSON: {e}")

    async def run(self):
        """Connect and start listening."""
        await self.connect()
        await self.listen()

    async def reconnect(self, max_retries: int = 5, delay: float = 2.0):
        """Try to reconnect with retries."""
        for attempt in range(max_retries):
            try:
                print(f"[WS] Reconnect attempt {attempt + 1}/{max_retries}")
                await self.connect()
                return True
            except Exception as e:
                print(f"[WS] Reconnect failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)

        print("[WS] Max reconnect attempts reached")
        return False


class GameClient(WebSocketClient):
    """Game-specific WebSocket client with convenience methods."""

    def __init__(self, server_url: str, device_id: str):
        super().__init__(server_url)
        self.device_id = device_id
        self.game_id: Optional[str] = None
        self.game_code: Optional[str] = None
        self.game_state: Optional[dict] = None

        # Derive HTTP base URL from WebSocket URL
        self.http_base_url = (
            server_url
            .replace("wss://", "https://")
            .replace("ws://", "http://")
            .replace("/ws", "")
        )

        # Game event callbacks
        self.on_game_created: Optional[Callable[[dict], None]] = None
        self.on_game_started: Optional[Callable[[dict], None]] = None
        self.on_timer_tick: Optional[Callable[[int], None]] = None
        self.on_module_solved: Optional[Callable[[str], None]] = None
        self.on_strike: Optional[Callable[[int], None]] = None
        self.on_game_won: Optional[Callable[[], None]] = None
        self.on_game_lost: Optional[Callable[[str], None]] = None

        # Register handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up game event handlers."""
        # Note: game_created is handled via REST API callback, not WebSocket
        self.register_handler("game_started", self._on_game_started)
        self.register_handler("timer_tick", self._on_timer_tick)
        self.register_handler("module_solved", self._on_module_solved)
        self.register_handler("strike", self._on_strike)
        self.register_handler("game_won", self._on_game_won)
        self.register_handler("game_lost", self._on_game_lost)
        self.register_handler("game_state", self._on_game_state)

    def _on_game_created(self, data: dict):
        """Handle game created event."""
        self.game_id = data.get("game_id")
        print(f"[Game] Created: {self.game_id}")
        if self.on_game_created:
            self.on_game_created(data)

    def _on_game_started(self, data: dict):
        """Handle game started event."""
        self.game_state = data
        print(f"[Game] Started! Data keys: {data.keys() if data else 'None'}")
        if self.on_game_started:
            self.on_game_started(data)

    def _on_timer_tick(self, data: dict):
        """Handle timer tick."""
        remaining = data.get("time_left", data.get("remaining", 0))
        if self.on_timer_tick:
            self.on_timer_tick(remaining)

    def _on_module_solved(self, data: dict):
        """Handle module solved."""
        module = data.get("module", "unknown")
        print(f"[Game] Module solved: {module}")
        if self.on_module_solved:
            self.on_module_solved(module)

    def _on_strike(self, data: dict):
        """Handle strike."""
        count = data.get("strikes", 0)
        print(f"[Game] Strike! Total: {count}")
        if self.on_strike:
            self.on_strike(count)

    def _on_game_won(self, data: dict):
        """Handle game won."""
        print("[Game] WON!")
        if self.on_game_won:
            self.on_game_won()

    def _on_game_lost(self, data: dict):
        """Handle game lost."""
        reason = data.get("reason", "unknown")
        print(f"[Game] LOST: {reason}")
        if self.on_game_lost:
            self.on_game_lost(reason)

    def _on_game_state(self, data: dict):
        """Handle game state update."""
        self.game_state = data

    def create_game(self, time_limit: int = 300, max_strikes: int = 3) -> Optional[dict]:
        """Create a new game via REST API and join as bomb."""
        try:
            # Create the game
            url = f"{self.http_base_url}/api/v1/game/create"
            response = requests.post(url, json={
                "time_limit": time_limit,
                "max_strikes": max_strikes
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.game_id = data.get("game_id")
            self.game_code = data.get("code")
            print(f"[Game] Created game: {self.game_code}")

            # Join the game as bomb
            join_result = self.join_game_http(self.game_code)
            if not join_result:
                print(f"[Game] Failed to join game as bomb")
                return None

            if self.on_game_created:
                self.on_game_created(data)
            return data
        except Exception as e:
            print(f"[Game] Failed to create game: {e}")
            return None

    def join_game_http(self, code: str) -> Optional[dict]:
        """Join a game via REST API as bomb/defuser."""
        try:
            url = f"{self.http_base_url}/api/v1/game/join"
            response = requests.post(url, json={
                "code": code,
                "role": "bomb"
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.game_id = data.get("game_id")
            self.game_code = code
            print(f"[Game] Joined game: {self.game_code}")
            return data
        except Exception as e:
            print(f"[Game] Failed to join game: {e}")
            return None

    async def join_game(self, game_id: str):
        """Join a game as defuser."""
        self.game_id = game_id
        await self.send("join_game", {
            "game_id": game_id,
            "device_id": self.device_id,
            "role": "defuser"
        })

    async def report_module_action(self, module: str, action: str, data: dict = None):
        """Report a module action to the server."""
        await self.send("module_action", {
            "game_id": self.game_id,
            "module": module,
            "action": action,
            **(data or {})
        })

    async def report_module_solved(self, module: str):
        """Report module solved."""
        await self.send("module_solved", {
            "game_id": self.game_id,
            "module": module
        })

    async def report_strike(self, module: str, reason: str):
        """Report a strike."""
        await self.send("strike", {
            "game_id": self.game_id,
            "module": module,
            "reason": reason
        })
