package game

import (
	"crypto/rand"
	"encoding/binary"
	"fmt"
	"sync"
	"time"
)

// Engine manages all active games
type Engine struct {
	games      map[string]*Game // game ID -> game
	codeIndex  map[string]string // join code -> game ID
	mu         sync.RWMutex

	// Callbacks for events (to be set by handler)
	OnGameEvent func(event GameEvent)
}

// NewEngine creates a new game engine
func NewEngine() *Engine {
	return &Engine{
		games:     make(map[string]*Game),
		codeIndex: make(map[string]string),
	}
}

// CreateGame creates a new game with the specified settings
func (e *Engine) CreateGame(timeLimit, modulesCount, maxStrikes int) (*Game, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Generate unique ID and join code
	gameID := e.generateID()
	joinCode := e.generateJoinCode()

	// Ensure code is unique
	for _, exists := e.codeIndex[joinCode]; exists; {
		joinCode = e.generateJoinCode()
		_, exists = e.codeIndex[joinCode]
	}

	// Generate seed for deterministic rules
	seed := e.generateSeed()

	// Generate modules
	ruleGen := NewRuleGenerator(seed)
	modules := ruleGen.GenerateModules(modulesCount)

	game := &Game{
		ID:           gameID,
		Code:         joinCode,
		State:        StateLobby,
		Seed:         seed,
		TimeLimit:    timeLimit,
		TimeLeft:     timeLimit,
		Strikes:      0,
		MaxStrikes:   maxStrikes,
		Modules:      modules,
		ModulesCount: modulesCount,
		CreatedAt:    time.Now(),
	}

	e.games[gameID] = game
	e.codeIndex[joinCode] = gameID

	// Emit event
	e.emitEvent(GameEvent{
		Type:      EventGameCreated,
		GameID:    gameID,
		Timestamp: time.Now(),
		Data: map[string]interface{}{
			"code":          joinCode,
			"time_limit":    timeLimit,
			"modules_count": modulesCount,
		},
	})

	return game, nil
}

// GetGame returns a game by ID
func (e *Engine) GetGame(gameID string) (*Game, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	game, ok := e.games[gameID]
	return game, ok
}

// GetGameByCode returns a game by join code
func (e *Engine) GetGameByCode(code string) (*Game, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	gameID, ok := e.codeIndex[code]
	if !ok {
		return nil, false
	}

	game, ok := e.games[gameID]
	return game, ok
}

// JoinGame allows a player to join a game
func (e *Engine) JoinGame(code string, role string) (*Game, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	gameID, ok := e.codeIndex[code]
	if !ok {
		return nil, fmt.Errorf("game not found with code: %s", code)
	}

	game, ok := e.games[gameID]
	if !ok {
		return nil, fmt.Errorf("game not found")
	}

	if game.State != StateLobby {
		return nil, fmt.Errorf("game already started")
	}

	game.mu.Lock()
	defer game.mu.Unlock()

	switch role {
	case "bomb":
		if game.BombConnected {
			return nil, fmt.Errorf("bomb already connected")
		}
		game.BombConnected = true
	case "expert":
		if game.ExpertConnected {
			return nil, fmt.Errorf("expert already connected")
		}
		game.ExpertConnected = true
	default:
		return nil, fmt.Errorf("invalid role: %s", role)
	}

	e.emitEvent(GameEvent{
		Type:      EventPlayerJoined,
		GameID:    gameID,
		Timestamp: time.Now(),
		Data: map[string]interface{}{
			"role": role,
		},
	})

	return game, nil
}

// StartGame starts the game timer
func (e *Engine) StartGame(gameID string) error {
	e.mu.Lock()
	game, ok := e.games[gameID]
	e.mu.Unlock()

	if !ok {
		return fmt.Errorf("game not found")
	}

	game.mu.Lock()
	defer game.mu.Unlock()

	if game.State != StateLobby {
		return fmt.Errorf("game not in lobby state")
	}

	if !game.BombConnected {
		return fmt.Errorf("bomb not connected")
	}

	now := time.Now()
	game.State = StatePlaying
	game.StartedAt = &now
	game.ActiveModuleIndex = 0

	// Set first module as active, rest as inactive
	for i := range game.Modules {
		if i == 0 {
			game.Modules[i].State = ModuleStateActive
		} else {
			game.Modules[i].State = ModuleStateInactive
		}
	}

	e.emitEvent(GameEvent{
		Type:      EventGameStarted,
		GameID:    gameID,
		Timestamp: now,
		Data: map[string]interface{}{
			"time_limit":          game.TimeLimit,
			"modules":             game.Modules,
			"active_module_index": game.ActiveModuleIndex,
		},
	})

	// Start timer goroutine
	go e.runTimer(gameID)

	return nil
}

// runTimer manages the game countdown
func (e *Engine) runTimer(gameID string) {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		e.mu.RLock()
		game, ok := e.games[gameID]
		e.mu.RUnlock()

		if !ok {
			return
		}

		game.mu.Lock()

		if game.State != StatePlaying {
			game.mu.Unlock()
			return
		}

		game.TimeLeft--

		if game.TimeLeft <= 0 {
			game.State = StateLose
			now := time.Now()
			game.EndedAt = &now
			game.mu.Unlock()

			e.emitEvent(GameEvent{
				Type:      EventGameLost,
				GameID:    gameID,
				Timestamp: now,
				Data: map[string]interface{}{
					"reason": "time_expired",
				},
			})
			return
		}

		timeLeft := game.TimeLeft
		game.mu.Unlock()

		e.emitEvent(GameEvent{
			Type:      EventTimerTick,
			GameID:    gameID,
			Timestamp: time.Now(),
			Data: map[string]interface{}{
				"time_left": timeLeft,
			},
		})
	}
}

// ProcessAction processes a player action on a module
func (e *Engine) ProcessAction(gameID, moduleID, action string, value interface{}) (*ActionResult, error) {
	e.mu.RLock()
	game, ok := e.games[gameID]
	e.mu.RUnlock()

	if !ok {
		return nil, fmt.Errorf("game not found")
	}

	game.mu.Lock()
	defer game.mu.Unlock()

	if game.State != StatePlaying {
		return nil, fmt.Errorf("game not in playing state")
	}

	// Find module
	var module *Module
	for i := range game.Modules {
		if game.Modules[i].ID == moduleID {
			module = &game.Modules[i]
			break
		}
	}

	if module == nil {
		return nil, fmt.Errorf("module not found: %s", moduleID)
	}

	if module.State != ModuleStateActive {
		return nil, fmt.Errorf("module not active")
	}

	// Process action based on module type
	result := e.processModuleAction(game, module, action, value)

	// Emit action event
	e.emitEvent(GameEvent{
		Type:      EventModuleAction,
		GameID:    gameID,
		ModuleID:  moduleID,
		Timestamp: time.Now(),
		Data: map[string]interface{}{
			"action":  action,
			"value":   value,
			"success": result.Success,
			"message": result.Message,
		},
	})

	// Check if strike occurred
	if result.Strike {
		game.Strikes++
		e.emitEvent(GameEvent{
			Type:      EventStrike,
			GameID:    gameID,
			ModuleID:  moduleID,
			Timestamp: time.Now(),
			Data: map[string]interface{}{
				"strikes":     game.Strikes,
				"max_strikes": game.MaxStrikes,
				"reason":      result.Message,
			},
		})

		if game.Strikes >= game.MaxStrikes {
			game.State = StateLose
			now := time.Now()
			game.EndedAt = &now

			e.emitEvent(GameEvent{
				Type:      EventGameLost,
				GameID:    gameID,
				Timestamp: now,
				Data: map[string]interface{}{
					"reason": "max_strikes",
				},
			})
		}
	}

	// Check if module was solved
	if result.Solved {
		module.State = ModuleStateSolved

		// Activate next module (sequential play)
		nextModuleID := ""
		if game.ActiveModuleIndex+1 < len(game.Modules) {
			game.ActiveModuleIndex++
			game.Modules[game.ActiveModuleIndex].State = ModuleStateActive
			nextModuleID = game.Modules[game.ActiveModuleIndex].ID
		}

		e.emitEvent(GameEvent{
			Type:      EventModuleSolved,
			GameID:    gameID,
			ModuleID:  moduleID,
			Timestamp: time.Now(),
			Data: map[string]interface{}{
				"next_module_id":      nextModuleID,
				"active_module_index": game.ActiveModuleIndex,
			},
		})

		// Check if all modules are solved
		if e.allModulesSolved(game) {
			game.State = StateWin
			now := time.Now()
			game.EndedAt = &now

			e.emitEvent(GameEvent{
				Type:      EventGameWon,
				GameID:    gameID,
				Timestamp: now,
				Data: map[string]interface{}{
					"time_remaining": game.TimeLeft,
				},
			})
		}
	}

	return result, nil
}

// ActionResult represents the result of a player action
type ActionResult struct {
	Success bool   `json:"success"`
	Strike  bool   `json:"strike"`
	Solved  bool   `json:"solved"`
	Message string `json:"message"`
}

// processModuleAction handles action logic for each module type
func (e *Engine) processModuleAction(game *Game, module *Module, action string, value interface{}) *ActionResult {
	switch module.Type {
	case ModuleWires:
		return e.processWiresAction(module, action, value)
	case ModuleKeypad:
		return e.processKeypadAction(module, action, value)
	case ModuleSimon:
		return e.processSimonAction(module, action, value)
	case ModuleMagnet:
		return e.processMagnetAction(module, action, value)
	default:
		return &ActionResult{Success: false, Message: "unknown module type"}
	}
}

// processWiresAction handles cutting wires
func (e *Engine) processWiresAction(module *Module, action string, value interface{}) *ActionResult {
	if action != "cut_wire" {
		return &ActionResult{Success: false, Message: "invalid action"}
	}

	wireIndex, ok := value.(float64)
	if !ok {
		return &ActionResult{Success: false, Message: "invalid wire index"}
	}
	idx := int(wireIndex)

	if idx < 0 || idx > 3 {
		return &ActionResult{Success: false, Message: "wire index out of range"}
	}

	// Get current state
	cutWires, ok := module.Config["cut_wires"].([]interface{})
	if !ok {
		// Initialize if needed
		cutWires = []interface{}{false, false, false, false}
	}

	// Check if already cut
	if cut, ok := cutWires[idx].(bool); ok && cut {
		return &ActionResult{Success: false, Message: "wire already cut"}
	}

	// Mark as cut
	newCutWires := make([]bool, 4)
	for i, v := range cutWires {
		if b, ok := v.(bool); ok {
			newCutWires[i] = b
		}
	}
	newCutWires[idx] = true
	module.Config["cut_wires"] = newCutWires

	// Check if correct
	correctCuts, ok := module.Solution["correct_cuts"].([]int)
	if !ok {
		return &ActionResult{Success: false, Message: "invalid solution"}
	}

	// Check if this was a correct cut
	isCorrect := false
	for _, correctIdx := range correctCuts {
		if correctIdx == idx {
			isCorrect = true
			break
		}
	}

	if !isCorrect {
		return &ActionResult{
			Success: true,
			Strike:  true,
			Message: "wrong wire cut",
		}
	}

	// Check if all correct wires are cut
	allCut := true
	for _, correctIdx := range correctCuts {
		if !newCutWires[correctIdx] {
			allCut = false
			break
		}
	}

	if allCut {
		return &ActionResult{
			Success: true,
			Solved:  true,
			Message: "module solved",
		}
	}

	return &ActionResult{
		Success: true,
		Message: "correct wire cut",
	}
}

// processKeypadAction handles code entry
func (e *Engine) processKeypadAction(module *Module, action string, value interface{}) *ActionResult {
	if action != "enter_digit" && action != "submit_code" {
		return &ActionResult{Success: false, Message: "invalid action"}
	}

	correctCode, ok := module.Solution["correct_code"].(string)
	if !ok {
		return &ActionResult{Success: false, Message: "invalid solution"}
	}

	if action == "enter_digit" {
		digit, ok := value.(string)
		if !ok {
			return &ActionResult{Success: false, Message: "invalid digit"}
		}

		currentCode, _ := module.Config["current_code"].(string)
		codeLength, _ := module.Config["code_length"].(int)
		if codeLength == 0 {
			codeLength = 3
		}

		if len(currentCode) >= codeLength {
			return &ActionResult{Success: false, Message: "code already complete"}
		}

		currentCode += digit
		module.Config["current_code"] = currentCode
		module.Config["display_code"] = formatCodeDisplay(currentCode, codeLength)

		return &ActionResult{
			Success: true,
			Message: fmt.Sprintf("digit entered: %s", digit),
		}
	}

	// submit_code
	currentCode, _ := module.Config["current_code"].(string)

	if currentCode == correctCode {
		return &ActionResult{
			Success: true,
			Solved:  true,
			Message: "correct code",
		}
	}

	// Wrong code - reset and strike
	module.Config["current_code"] = ""
	module.Config["display_code"] = "_ _ _"

	return &ActionResult{
		Success: true,
		Strike:  true,
		Message: "incorrect code",
	}
}

func formatCodeDisplay(code string, length int) string {
	display := ""
	for i := 0; i < length; i++ {
		if i < len(code) {
			display += string(code[i])
		} else {
			display += "_"
		}
		if i < length-1 {
			display += " "
		}
	}
	return display
}

// processSimonAction handles Simon Says input (expert taps colors on mobile)
func (e *Engine) processSimonAction(module *Module, action string, value interface{}) *ActionResult {
	if action != "color_tap" {
		return &ActionResult{Success: false, Message: "invalid action"}
	}

	tappedColor, ok := value.(string)
	if !ok {
		return &ActionResult{Success: false, Message: "invalid color"}
	}

	// Get expected colors from solution
	expectedColors, ok := module.Solution["expected_colors"].([]string)
	if !ok {
		// Try to convert from interface slice
		if colorsInterface, ok := module.Solution["expected_colors"].([]interface{}); ok {
			expectedColors = make([]string, len(colorsInterface))
			for i, v := range colorsInterface {
				if s, ok := v.(string); ok {
					expectedColors[i] = s
				}
			}
		} else {
			return &ActionResult{Success: false, Message: "invalid solution"}
		}
	}

	currentIndex, _ := module.Config["current_index"].(int)
	if currentIndexF, ok := module.Config["current_index"].(float64); ok {
		currentIndex = int(currentIndexF)
	}

	if currentIndex >= len(expectedColors) {
		return &ActionResult{Success: false, Message: "sequence complete"}
	}

	if tappedColor != expectedColors[currentIndex] {
		// Wrong color - reset to beginning
		module.Config["current_index"] = 0
		return &ActionResult{
			Success: true,
			Strike:  true,
			Message: fmt.Sprintf("wrong color: expected %s", expectedColors[0]),
		}
	}

	currentIndex++
	module.Config["current_index"] = currentIndex

	if currentIndex >= len(expectedColors) {
		return &ActionResult{
			Success: true,
			Solved:  true,
			Message: "sequence complete",
		}
	}

	return &ActionResult{
		Success: true,
		Message: fmt.Sprintf("correct, %d remaining", len(expectedColors)-currentIndex),
	}
}

// processMagnetAction handles magnet application
func (e *Engine) processMagnetAction(module *Module, action string, value interface{}) *ActionResult {
	if action != "apply_magnet" {
		return &ActionResult{Success: false, Message: "invalid action"}
	}

	safeConditions, ok := module.Solution["safe_conditions"].(map[string]interface{})
	if !ok {
		return &ActionResult{Success: false, Message: "invalid solution"}
	}

	// Check if current conditions match safe conditions
	ledColor, _ := module.Config["led_color"].(string)
	buzzerActive, _ := module.Config["buzzer_active"].(bool)

	safeLED, _ := safeConditions["led_color"].(string)
	safeBuzzer, _ := safeConditions["buzzer_active"].(bool)

	if ledColor == safeLED && buzzerActive == safeBuzzer {
		return &ActionResult{
			Success: true,
			Solved:  true,
			Message: "magnet applied successfully",
		}
	}

	return &ActionResult{
		Success: true,
		Strike:  true,
		Message: "unsafe conditions - do not apply magnet",
	}
}

// allModulesSolved checks if all solvable modules are solved
func (e *Engine) allModulesSolved(game *Game) bool {
	for _, module := range game.Modules {
		if module.State != ModuleStateSolved {
			return false
		}
	}
	return true
}

// GetManual returns the manual for a game based on its seed
func (e *Engine) GetManual(gameID string) (map[string][]string, error) {
	e.mu.RLock()
	game, ok := e.games[gameID]
	e.mu.RUnlock()

	if !ok {
		return nil, fmt.Errorf("game not found")
	}

	ruleGen := NewRuleGenerator(game.Seed)
	return ruleGen.GetFullManual(), nil
}

// UpdateMagnetState updates the magnet module state (called by timer)
func (e *Engine) UpdateMagnetState(gameID string) {
	e.mu.RLock()
	game, ok := e.games[gameID]
	e.mu.RUnlock()

	if !ok || game.State != StatePlaying {
		return
	}

	game.mu.Lock()
	defer game.mu.Unlock()

	for i := range game.Modules {
		if game.Modules[i].Type == ModuleMagnet && game.Modules[i].State == ModuleStateActive {
			// Cycle through states based on time
			timeLeft := game.TimeLeft

			// Change state every 5 seconds
			phase := (timeLeft / 5) % 4

			switch phase {
			case 0:
				game.Modules[i].Config["led_color"] = "red"
				game.Modules[i].Config["buzzer_active"] = true
				game.Modules[i].Config["safe_window"] = false
			case 1:
				game.Modules[i].Config["led_color"] = "green"
				game.Modules[i].Config["buzzer_active"] = true
				game.Modules[i].Config["safe_window"] = false
			case 2:
				game.Modules[i].Config["led_color"] = "green"
				game.Modules[i].Config["buzzer_active"] = false
				game.Modules[i].Config["safe_window"] = true // SAFE!
			case 3:
				game.Modules[i].Config["led_color"] = "blue"
				game.Modules[i].Config["buzzer_active"] = false
				game.Modules[i].Config["safe_window"] = false
			}
		}
	}
}

// CleanupGame removes a game from memory
func (e *Engine) CleanupGame(gameID string) {
	e.mu.Lock()
	defer e.mu.Unlock()

	if game, ok := e.games[gameID]; ok {
		delete(e.codeIndex, game.Code)
		delete(e.games, gameID)
	}
}

// Helper functions

func (e *Engine) generateID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return fmt.Sprintf("%x", b)
}

func (e *Engine) generateJoinCode() string {
	const charset = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" // Removed confusing chars
	b := make([]byte, 6)
	rand.Read(b)
	code := make([]byte, 6)
	for i := 0; i < 6; i++ {
		code[i] = charset[int(b[i])%len(charset)]
	}
	return string(code)
}

func (e *Engine) generateSeed() int64 {
	b := make([]byte, 8)
	rand.Read(b)
	return int64(binary.BigEndian.Uint64(b))
}

func (e *Engine) emitEvent(event GameEvent) {
	if e.OnGameEvent != nil {
		e.OnGameEvent(event)
	}
}
