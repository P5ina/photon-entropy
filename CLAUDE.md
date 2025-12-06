# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bomb Defusal is a cooperative party game inspired by "Keep Talking and Nobody Explodes". One player (the Defuser) physically interacts with a "bomb" device built with Raspberry Pi and sensors, while another player (the Expert) reads instructions from an iOS app.

Components:
1. **Raspberry Pi (IoT)** - Physical bomb controller with buttons, LEDs, rotary encoder, sensors
2. **Go Backend** - Game server with state machine, WebSocket communication
3. **iOS Mobile App** - Expert interface with game instructions/manual

## Build & Run Commands

### Backend (Go)

```bash
cd backend

# Development
go run main.go

# Generate sqlc code (after modifying db/queries/*.sql)
sqlc generate

# Docker
docker-compose up -d
```

Environment variables (or `.env` file):
- `DATABASE_PATH` - SQLite path (default: `./data/photon.db`)
- `SERVER_HOST` / `SERVER_PORT` - Server binding (default: `0.0.0.0:8080`)
- `GIN_MODE` - `debug` or `release`

### Raspberry Pi (Python)

```bash
cd raspberrypi
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # Development (mock hardware)
pip install -r requirements-pi.txt     # Raspberry Pi (real hardware)

# Run game controller
python main.py

# Run demo mode (no server)
python main.py --demo

# Connect to specific game
python main.py --game-id ABC123
```

Configure via `.env` file: `SERVER_URL`, `DEVICE_ID`, `MOCK_HARDWARE`

### Mobile (iOS)

Open `mobile/PhotonEntropy.xcodeproj` in Xcode. Target: iOS 16+

## Architecture

### Game Flow

```
Expert creates game → Gets game code → Defuser enters code on device
                                              ↓
                   ← WebSocket sync ← Game starts ← Timer countdown
                                              ↓
Expert reads instructions → Defuser solves modules → Win/Lose
```

### Backend Structure

- `main.go` - Entry point, route setup
- `game/` - Game engine
  - `types.go` - Game state, module types, wire colors
  - `rules.go` - Deterministic rule generation from seed
  - `engine.go` - State machine, action processing
- `handlers/` - HTTP handlers (game, device, stats, websocket)
- `ws/` - WebSocket hub for real-time game events
- `db/queries/` - SQL queries (sqlc generates `db/sqlc/`)
- `db/migrations/` - Goose migrations

### Raspberry Pi Structure

- `main.py` - Entry point, game loop
- `game_controller.py` - Main game controller
- `config.py` - GPIO pin configuration
- `hardware/` - Hardware drivers
  - `lcd.py` - 16x2 I2C LCD display
  - `buzzer.py` - Buzzer with sound patterns
  - `rgb_led.py` - RGB LED with PWM
  - `button.py` - Button with debounce
  - `rotary.py` - Rotary encoder
  - `sensors.py` - Touch, Hall, Tilt sensors, LEDs
- `modules/` - Game modules
  - `base.py` - Base module class
  - `wires.py` - Cut wires in correct order
  - `keypad.py` - Enter code with rotary encoder
  - `simon.py` - Simon Says color sequence
  - `magnet.py` - Apply magnet at correct timing
- `network/` - Server communication
  - `ws_client.py` - WebSocket client

### Mobile Structure (MVVM)

- `Services/`
  - `APIService.swift` - REST client
  - `GameService.swift` - Game-specific API and WebSocket
- `ViewModels/GameViewModel.swift` - Game state management
- `Views/Game/`
  - `GameView.swift` - Main game view
  - `ModuleListView.swift` - Module instructions
- `Models/Game.swift` - Game models

## Game Modules

| Module | Hardware | Description |
|--------|----------|-------------|
| Wires | 4 buttons + 4 LEDs | Cut wires in correct order based on colors |
| Keypad | Rotary encoder | Enter numeric code (0-9 digits) |
| Simon | RGB LED + Touch | Repeat color sequence |
| Magnet | Hall sensor | Apply magnet during safe time windows |

## API Endpoints

```
# Game endpoints
POST /api/v1/game/create    # Create new game
POST /api/v1/game/join      # Join game as expert/defuser
POST /api/v1/game/start     # Start the game
GET  /api/v1/game/state     # Get current game state
GET  /api/v1/game/manual    # Get expert manual/instructions
POST /api/v1/game/action    # Process game action

# Other endpoints
GET  /api/v1/device/status  # Device online status
GET  /api/v1/stats          # Statistics
GET  /ws                    # WebSocket for real-time updates
GET  /health                # Health check
```

## WebSocket Events

```
game_created    # New game created
player_joined   # Player joined game
game_started    # Game timer started
timer_tick      # Timer update (every second)
module_action   # Module interaction
module_solved   # Module completed
strike          # Wrong action (mistake)
game_won        # All modules solved
game_lost       # Time ran out or too many strikes
```

## GPIO Pin Configuration

See `docs/HARDWARE.md` for complete wiring diagram.

| Component | GPIO Pins |
|-----------|-----------|
| Wire buttons | 19, 26, 21, 15 |
| Wire LEDs | 25, 8, 7, 1 |
| Rotary encoder | CLK:5, DT:6, SW:13 |
| RGB LED | R:17, G:27, B:22 |
| Touch sensor | 12 |
| Hall sensor | 16 |
| Buzzer | 18 |
| LCD | I2C (0x27) |

## Key Patterns

- Game uses seed-based deterministic rule generation for synchronized experience
- All hardware drivers support mock mode for testing without Pi
- WebSocket broadcasts all game events in real-time
- Mobile uses async/await for all network calls
