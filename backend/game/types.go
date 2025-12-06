package game

import (
	"sync"
	"time"
)

// GameState represents the current state of a game
type GameState string

const (
	StateLobby   GameState = "lobby"   // Waiting for players
	StatePlaying GameState = "playing" // Game in progress
	StateWin     GameState = "win"     // Bomb defused
	StateLose    GameState = "lose"    // Bomb exploded
)

// ModuleType represents different puzzle modules
type ModuleType string

const (
	ModuleWires  ModuleType = "wires"
	ModuleKeypad ModuleType = "keypad"
	ModuleSimon  ModuleType = "simon"
	ModuleMagnet ModuleType = "magnet"
)

// ModuleState represents the state of a module
type ModuleState string

const (
	ModuleStateInactive ModuleState = "inactive" // Not yet activated (sequential play)
	ModuleStateActive   ModuleState = "active"
	ModuleStateSolved   ModuleState = "solved"
	ModuleStateFailed   ModuleState = "failed"
)

// WireColor represents wire colors for the Wires module
type WireColor string

const (
	WireRed    WireColor = "red"
	WireBlue   WireColor = "blue"
	WireGreen  WireColor = "green"
	WireYellow WireColor = "yellow"
)

// AllWireColors is a list of all available wire colors
var AllWireColors = []WireColor{WireRed, WireBlue, WireGreen, WireYellow}

// Module represents a single puzzle module on the bomb
type Module struct {
	ID       string                 `json:"id"`
	Type     ModuleType             `json:"type"`
	State    ModuleState            `json:"state"`
	Config   map[string]interface{} `json:"config"`   // Module-specific configuration
	Solution map[string]interface{} `json:"-"`        // Correct answer (hidden from clients)
}

// Game represents a single game session
type Game struct {
	ID                string      `json:"id"`
	Code              string      `json:"code"` // 6-character join code
	State             GameState   `json:"state"`
	Seed              int64       `json:"seed"`
	TimeLimit         int         `json:"time_limit"`          // Total time in seconds
	TimeLeft          int         `json:"time_left"`           // Remaining time
	Strikes           int         `json:"strikes"`             // Current strikes
	MaxStrikes        int         `json:"max_strikes"`         // Max strikes before explosion
	Modules           []Module    `json:"modules"`
	ModulesCount      int         `json:"modules_count"`
	ActiveModuleIndex int         `json:"active_module_index"` // Current active module (sequential play)
	CreatedAt         time.Time   `json:"created_at"`
	StartedAt         *time.Time  `json:"started_at,omitempty"`
	EndedAt           *time.Time  `json:"ended_at,omitempty"`

	// Client tracking (not serialized to JSON)
	BombConnected   bool `json:"bomb_connected"`
	ExpertConnected bool `json:"expert_connected"`

	mu sync.RWMutex
}

// WiresConfig holds configuration for the Wires module
type WiresConfig struct {
	Wires    []WireColor `json:"wires"`     // Wire colors in order
	CutWires []bool      `json:"cut_wires"` // Which wires have been cut
}

// WiresSolution holds the solution for the Wires module
type WiresSolution struct {
	CorrectCuts []int `json:"correct_cuts"` // Indices of wires to cut (in order)
}

// KeypadConfig holds configuration for the Keypad module
type KeypadConfig struct {
	DisplayCode string `json:"display_code"` // What's shown on LCD (e.g., "_ _ _")
	CurrentCode string `json:"current_code"` // What user has entered so far
	CodeLength  int    `json:"code_length"`
}

// KeypadSolution holds the solution for the Keypad module
type KeypadSolution struct {
	CorrectCode string `json:"correct_code"`
}

// SimonConfig holds configuration for the Simon module
type SimonConfig struct {
	Sequence     []string `json:"sequence"`      // Color sequence to display on RGB LED
	CurrentIndex int      `json:"current_index"` // Current position in sequence (expert's progress)
}

// SimonSolution holds the solution for the Simon module
type SimonSolution struct {
	ExpectedColors []string `json:"expected_colors"` // Colors expert must tap in order
}

// MagnetConfig holds configuration for the Magnet module
type MagnetConfig struct {
	LEDColor     string `json:"led_color"`     // Current LED color
	BuzzerActive bool   `json:"buzzer_active"` // Is buzzer making sound
	SafeWindow   bool   `json:"safe_window"`   // Is it safe to use magnet now
}

// MagnetSolution holds the solution for the Magnet module
type MagnetSolution struct {
	SafeConditions map[string]interface{} `json:"safe_conditions"`
}

// GameEvent represents an event that occurred in the game
type GameEvent struct {
	Type      string                 `json:"type"`
	GameID    string                 `json:"game_id"`
	ModuleID  string                 `json:"module_id,omitempty"`
	Data      map[string]interface{} `json:"data,omitempty"`
	Timestamp time.Time              `json:"timestamp"`
}

// Event types
const (
	EventGameCreated    = "game_created"
	EventPlayerJoined   = "player_joined"
	EventGameStarted    = "game_started"
	EventTimerTick      = "timer_tick"
	EventModuleAction   = "module_action"
	EventModuleSolved   = "module_solved"
	EventStrike         = "strike"
	EventGameWon        = "game_won"
	EventGameLost       = "game_lost"
	EventMagnetState    = "magnet_state" // LED/buzzer state update for magnet module
)
