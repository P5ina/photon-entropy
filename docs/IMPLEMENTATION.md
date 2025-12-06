# План реализации Bomb Defusal Game

## Обзор

**Цель:** Кооперативная игра на разминирование с реальным hardware

**Компоненты:**
- Raspberry Pi + датчики = "Бомба"
- Go Backend = Game Engine
- iOS App = Интерфейс эксперта

---

## Этап 1: Backend — Game Engine

### Задачи

1. Создать game state machine (LOBBY → PLAYING → ENDED)
2. Реализовать генератор модулей и правил
3. WebSocket для real-time коммуникации
4. API endpoints для управления игрой

### Файлы

- `game/engine.go` — State machine, таймер
- `game/modules.go` — Определения модулей (Wires, Keypad, Simon, Magnet)
- `game/rules.go` — Генератор правил на основе seed
- `handlers/game.go` — HTTP endpoints
- `ws/hub.go` — WebSocket hub (уже есть, расширить)

### Game State

```go
type GameState string

const (
    StateLobby   GameState = "lobby"
    StatePlaying GameState = "playing"
    StateWin     GameState = "win"
    StateLose    GameState = "lose"
)

type Game struct {
    ID          string
    State       GameState
    Seed        int64           // Для генерации правил
    TimeLimit   int             // Секунды
    TimeLeft    int
    Strikes     int
    MaxStrikes  int
    Modules     []Module
    BombClient  *ws.Client
    ExpertClient *ws.Client
    CreatedAt   time.Time
}

type Module struct {
    ID       string
    Type     ModuleType
    State    ModuleState
    Config   map[string]any  // Module-specific config
    Solution map[string]any  // Correct answer
}
```

### API Endpoints

```go
// POST /api/v1/game/create
type CreateGameRequest struct {
    TimeLimit    int `json:"time_limit"`    // default: 300
    ModulesCount int `json:"modules_count"` // default: 5
}

type CreateGameResponse struct {
    GameID string `json:"game_id"`
    Code   string `json:"code"`  // 6-digit join code
}

// POST /api/v1/game/join
type JoinGameRequest struct {
    Code   string `json:"code"`
    Role   string `json:"role"`  // "bomb" or "expert"
}

// GET /api/v1/game/manual?game_id=xxx
// Returns instructions for expert (based on seed)

// POST /api/v1/game/action
type ActionRequest struct {
    GameID   string `json:"game_id"`
    ModuleID string `json:"module_id"`
    Action   string `json:"action"`
    Value    any    `json:"value"`
}
```

### Миграция БД

```sql
-- 004_add_games.sql
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    state TEXT NOT NULL DEFAULT 'lobby',
    seed INTEGER NOT NULL,
    time_limit INTEGER NOT NULL DEFAULT 300,
    strikes INTEGER NOT NULL DEFAULT 0,
    max_strikes INTEGER NOT NULL DEFAULT 3,
    modules_json TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    ended_at DATETIME
);

CREATE INDEX idx_games_code ON games(code);
CREATE INDEX idx_games_state ON games(state);
```

---

## Этап 2: Raspberry Pi — Bomb Controller

### Задачи

1. Драйверы для всех датчиков
2. LCD display controller
3. WebSocket client
4. Game loop с обработкой событий

### Структура

```
raspberrypi/
├── main.py
├── config.py
├── hardware/
│   ├── __init__.py
│   ├── lcd.py          # LCD 16x2 I2C
│   ├── buzzer.py       # PWM sound
│   ├── rgb_led.py      # Status LED
│   ├── button.py       # Button with debounce
│   ├── rotary.py       # Rotary encoder
│   ├── touch.py        # Touch sensor
│   ├── hall.py         # Hall sensor
│   └── tilt.py         # Tilt sensor
├── modules/
│   ├── __init__.py
│   ├── base.py         # Base class
│   ├── wires.py
│   ├── keypad.py
│   ├── simon.py
│   ├── magnet.py
│   └── stability.py
└── network/
    ├── __init__.py
    └── ws_client.py
```

### Base Module Class

```python
class BaseModule(ABC):
    def __init__(self, module_id: str, config: dict):
        self.id = module_id
        self.config = config
        self.solved = False
        self.on_action: Callable = None

    @abstractmethod
    def setup(self):
        """Initialize hardware"""
        pass

    @abstractmethod
    def update(self):
        """Called every frame"""
        pass

    @abstractmethod
    def cleanup(self):
        """Release hardware"""
        pass

    def emit_action(self, action: str, value: any):
        if self.on_action:
            self.on_action(self.id, action, value)
```

### Wires Module

```python
class WiresModule(BaseModule):
    """
    4 buttons = 4 wires
    4 LEDs show wire colors (R, B, W, O)
    Press button = "cut" wire
    """

    COLORS = ["red", "blue", "white", "orange"]

    def __init__(self, module_id: str, config: dict):
        super().__init__(module_id, config)
        # config: {"wires": ["red", "blue", "white", "orange"], "cut_order": [2, 0]}
        self.wires = config["wires"]
        self.cut = [False] * 4
        self.buttons = []
        self.leds = []

    def setup(self):
        for i, pin in enumerate(WIRE_BUTTON_PINS):
            btn = Button(pin, callback=lambda i=i: self._on_cut(i))
            self.buttons.append(btn)

        for i, pin in enumerate(WIRE_LED_PINS):
            led = LED(pin)
            led.on()  # All wires start connected
            self.leds.append(led)

    def _on_cut(self, wire_index: int):
        if self.cut[wire_index]:
            return  # Already cut

        self.cut[wire_index] = True
        self.leds[wire_index].off()

        self.emit_action("cut_wire", {
            "wire_index": wire_index,
            "wire_color": self.wires[wire_index]
        })
```

### Game Loop

```python
async def main():
    # Connect to server
    ws = WebSocketClient(SERVER_URL)
    await ws.connect()

    # Wait for game start
    game_config = await ws.wait_for("game_start")

    # Initialize modules
    modules = []
    for mod_config in game_config["modules"]:
        module = create_module(mod_config)
        module.on_action = lambda mid, act, val: ws.send_action(mid, act, val)
        module.setup()
        modules.append(module)

    # Start timer display
    lcd.show_timer(game_config["time_limit"])
    buzzer.start_ticking()

    # Main loop
    try:
        while True:
            # Update all modules
            for module in modules:
                module.update()

            # Handle server messages
            msg = await ws.receive_nowait()
            if msg:
                handle_message(msg, modules, lcd, buzzer)

            await asyncio.sleep(0.01)  # 100 FPS

    finally:
        for module in modules:
            module.cleanup()
```

---

## Этап 3: iOS — Expert Interface

### Задачи

1. Lobby screen (create/join game)
2. Game screen (timer, strikes, module status)
3. Manual view (instructions for each module)
4. WebSocket for real-time updates

### Структура

```
Views/
├── LobbyView.swift         # Create or join game
├── GameView.swift          # Main game screen
├── ManualView.swift        # Tab view with all manuals
└── Modules/
    ├── WiresManualView.swift
    ├── KeypadManualView.swift
    ├── SimonManualView.swift
    ├── MagnetManualView.swift
    └── StabilityManualView.swift
```

### Game View

```swift
struct GameView: View {
    @StateObject var viewModel: GameViewModel

    var body: some View {
        VStack {
            // Timer
            TimerView(timeLeft: viewModel.timeLeft)

            // Strikes
            StrikesView(strikes: viewModel.strikes, max: 3)

            // Module status
            ModuleStatusGrid(modules: viewModel.modules)

            // Manual button
            Button("Open Manual") {
                viewModel.showManual = true
            }
        }
        .sheet(isPresented: $viewModel.showManual) {
            ManualView(seed: viewModel.seed)
        }
        .onAppear {
            viewModel.connectWebSocket()
        }
    }
}
```

### Manual Generation (based on seed)

```swift
struct WiresManual {
    let seed: Int

    var rules: [WireRule] {
        var rng = SeededRandom(seed: seed)

        // Generate deterministic rules based on seed
        return [
            WireRule(
                condition: "If there are more than 2 red wires",
                action: "Cut the last red wire"
            ),
            WireRule(
                condition: "If the last wire is white",
                action: "Cut the first wire"
            ),
            // ... more rules
        ]
    }
}
```

---

## Этап 4: Модули — Детальные правила

### Wires Module

**Визуал на бомбе:**
- 4 LED разных цветов (R, B, W, O)
- 4 кнопки под ними

**Правила (генерируются из seed):**
```
Если красных проводов больше двух → режь последний красный
Если последний провод белый → режь первый
Если синих проводов нет → режь второй
Иначе → режь последний
```

### Keypad Module

**Визуал на бомбе:**
- LCD показывает "CODE: _ _ _"
- Rotary encoder для выбора цифры
- Кнопка encoder для подтверждения

**Правила:**
```
Код = (количество проводов × позиция синего) + цвет последнего LED
R=1, B=2, W=3, O=4
```

### Simon Module

**Визуал на бомбе:**
- RGB LED мигает последовательностью
- Touch sensor для ввода

**Правила:**
```
Когда LED красный → тапни 1 раз
Когда LED зелёный → тапни 2 раза
Когда LED синий → подожди
```

### Magnet Module

**Визуал на бомбе:**
- RGB LED показывает состояние
- Hall sensor ждёт магнит

**Правила:**
```
Поднеси магнит ТОЛЬКО когда:
- LED зелёный И buzzer молчит
Если поднести в другое время → strike
```

---

## Этап 5: Тестирование

### Unit Tests

- [ ] Game state transitions
- [ ] Rule generation determinism (same seed = same rules)
- [ ] Module action validation

### Integration Tests

- [ ] WebSocket connection bomb ↔ server
- [ ] WebSocket connection expert ↔ server
- [ ] Full game flow (create → join → play → win/lose)

### Hardware Tests

- [ ] Each sensor individually
- [ ] LCD display
- [ ] Buzzer tones
- [ ] All modules together

---

## GPIO Reference

```python
# config.py

# Wires module
WIRE_BUTTONS = [19, 26, 21, 20]  # GPIO pins for 4 buttons
WIRE_LEDS = [25, 8, 7, 1]        # GPIO pins for 4 LEDs

# Keypad module
ROTARY_CLK = 5
ROTARY_DT = 6
ROTARY_SW = 13

# Simon module
RGB_RED = 17
RGB_GREEN = 27
RGB_BLUE = 22
TOUCH_PIN = 12

# Magnet module
HALL_PIN = 16

# Output
BUZZER_PIN = 18

# I2C (LCD)
# SDA = GPIO 2 (Pin 3)
# SCL = GPIO 3 (Pin 5)
```

---

## Зависимости

### Backend (Go)

```
github.com/gin-gonic/gin
github.com/gorilla/websocket
modernc.org/sqlite
github.com/pressly/goose/v3
```

### Raspberry Pi (Python)

```
RPi.GPIO
RPLCD
websockets
python-dotenv
```

### iOS

- SwiftUI
- Combine
- URLSession (WebSocket)
