# PhotonEntropy — Bomb Defusal Game

Кооперативная игра на разминирование бомбы с реальными датчиками. Один игрок (Сапёр) взаимодействует с физической "бомбой", второй (Эксперт) читает инструкции с телефона.

**Курсовая работа** — Mobile & IoT

## Концепция

Вдохновлено игрой "Keep Talking and Nobody Explodes", но с реальным hardware.

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Raspberry Pi   │       │    Go Backend    │       │   iOS App        │
│   "THE BOMB"     │       │   Game Engine    │       │   "EXPERT"       │
│                  │       │                  │       │                  │
│  ┌────────────┐  │  WS   │  ┌────────────┐  │  WS   │  ┌────────────┐  │
│  │ Sensors    │  │◀─────▶│  │ Game State │  │◀─────▶│  │ Manual     │  │
│  │ LCD 16x2   │  │       │  │ Rules Gen  │  │       │  │ Instructions│  │
│  │ LEDs/Buzzer│  │       │  └────────────┘  │       │  └────────────┘  │
│  └────────────┘  │       │                  │       │                  │
│                  │       │  SQLite + API    │       │  Swift/SwiftUI   │
│  DEFUSER plays   │       │                  │       │  EXPERT reads    │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

## Игровой процесс

1. **Эксперт** создаёт игру в приложении
2. **Сапёр** подключает "бомбу" (Raspberry Pi)
3. Сервер генерирует случайные модули и правила
4. **Таймер запускается** — у команды 5 минут
5. **Эксперт** видит инструкции, но НЕ видит бомбу
6. **Сапёр** видит бомбу, но НЕ видит инструкции
7. Игроки общаются голосом, решают головоломки
8. 3 ошибки (strikes) = взрыв
9. Все модули решены до истечения времени = победа!

## Модули

| Модуль | Датчики | Механика |
|--------|---------|----------|
| **Wires** | 4 кнопки + 4 LED | "Перережь" правильные провода |
| **Keypad** | Rotary encoder | Введи 3-значный код |
| **Simon** | RGB LED + Touch | Повтори последовательность цветов |
| **Magnet** | Hall sensor | Поднеси магнит в нужный момент |

## Архитектура

### API Endpoints

```
Game Flow:
  POST /api/v1/game/create        Создать новую игру
  POST /api/v1/game/join          Присоединиться (bomb/expert)
  POST /api/v1/game/start         Запустить таймер
  GET  /api/v1/game/state         Текущее состояние
  GET  /api/v1/game/manual        Инструкции для эксперта

Actions:
  POST /api/v1/game/action        Действие от бомбы

WebSocket:
  GET  /ws                        Real-time updates

Health:
  GET  /health                    Проверка сервера
```

### WebSocket Events

```
bomb → server:
  module_action { module_id, action, value }

server → expert:
  game_state { time_left, strikes, modules_solved }
  module_update { module_id, state }
  game_over { win: bool, reason: string }

server → bomb:
  game_start { modules, time_limit, seed }
  action_result { module_id, success, message }
  strike { count, reason }
  game_over { win: bool }
```

## Структура проекта

```
photon-entropy/
├── README.md
├── docs/
│   ├── HARDWARE.md              # Список компонентов и схемы
│   └── IMPLEMENTATION.md        # План разработки
│
├── raspberrypi/                 # "Бомба"
│   ├── requirements.txt
│   ├── config.py
│   ├── main.py                  # Game loop
│   ├── hardware/
│   │   ├── lcd.py               # LCD 16x2 I2C driver
│   │   ├── buzzer.py            # Sound effects
│   │   └── rgb_led.py           # Status LED
│   ├── modules/
│   │   ├── base.py              # Base module class
│   │   ├── wires.py             # Wires module
│   │   ├── keypad.py            # Keypad module
│   │   ├── simon.py             # Simon Says module
│   │   └── magnet.py            # Magnet module
│   └── network/
│       └── ws_client.py         # WebSocket client
│
├── backend/                     # Game server
│   ├── Dockerfile
│   ├── compose.yml
│   ├── main.go
│   ├── config/
│   ├── db/
│   │   ├── migrations/
│   │   ├── queries/
│   │   └── sqlc/
│   ├── handlers/
│   │   ├── game.go              # Game endpoints
│   │   └── websocket.go         # WebSocket handler
│   ├── game/
│   │   ├── engine.go            # Game state machine
│   │   ├── modules.go           # Module definitions
│   │   └── rules.go             # Rule generation
│   └── ws/
│       └── hub.go               # WebSocket hub
│
└── mobile/                      # Expert app
    └── PhotonEntropy/
        ├── PhotonEntropyApp.swift
        ├── Models/
        │   ├── Game.swift
        │   └── Module.swift
        ├── Services/
        │   ├── GameService.swift
        │   └── WebSocketService.swift
        ├── ViewModels/
        │   ├── LobbyViewModel.swift
        │   └── GameViewModel.swift
        └── Views/
            ├── LobbyView.swift      # Create/join game
            ├── GameView.swift       # Main game screen
            ├── ManualView.swift     # Instructions
            └── Modules/
                ├── WiresManualView.swift
                ├── KeypadManualView.swift
                ├── SimonManualView.swift
                └── MagnetManualView.swift
```

## Hardware

Полный список компонентов: [docs/HARDWARE.md](docs/HARDWARE.md)

### Основные компоненты

| Компонент | Описание |
|-----------|----------|
| Raspberry Pi 4/5 | Контроллер "бомбы" |
| LCD 16x2 I2C | Таймер и подсказки |
| 4× Tactile Button | Модуль "Wires" |
| 4× LED (R, B, W, O) | Индикаторы проводов |
| KY-040 Rotary Encoder | Модуль "Keypad" |
| KY-016 RGB LED | Модуль "Simon" + статус |
| KY-036 Touch Sensor | Ввод для Simon |
| KY-003 Hall Sensor | Модуль "Magnet" |
| KY-012 Buzzer | Звуковые эффекты |

## Быстрый старт

### 1. Backend

```bash
cd backend
docker-compose up -d
# или
go run main.go
```

Сервер: `http://localhost:8080`

### 2. Raspberry Pi (Bomb)

```bash
cd raspberrypi
pip install -r requirements.txt
python main.py --server ws://your-server:8080/ws
```

### 3. iOS (Expert)

Открыть `mobile/PhotonEntropy.xcodeproj` в Xcode и запустить.

## Конфигурация

### Raspberry Pi

```python
# config.py
SERVER_URL = "ws://192.168.1.100:8080/ws"
DEVICE_ID = "bomb-001"

# GPIO pins
WIRE_BUTTONS = [19, 26, 21, 20]
WIRE_LEDS = [25, 8, 7, 1]
ROTARY_CLK = 5
ROTARY_DT = 6
ROTARY_SW = 13
RGB_PINS = {"r": 17, "g": 27, "b": 22}
TOUCH_PIN = 12
HALL_PIN = 16
BUZZER_PIN = 18
```

### Backend

```yaml
# config.yaml
server:
  port: 8080

game:
  time_limit: 300      # 5 minutes
  max_strikes: 3
  modules_count: 5

database:
  path: "./data/bomb.db"
```

## Технологии

- **Bomb (Raspberry Pi)**: Python 3, RPi.GPIO, websockets
- **Backend**: Go, Gin, Gorilla WebSocket, SQLite
- **Expert (iOS)**: Swift 5, SwiftUI, URLSession WebSocket

## Лицензия

MIT

## Автор

Timur ([P5ina](https://github.com/P5ina)) — Курсовая работа, Mobile & IoT, 2025
