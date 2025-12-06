package game

import (
	"fmt"
	"math/rand"
)

// RuleGenerator generates deterministic rules based on a seed
type RuleGenerator struct {
	rng *rand.Rand
}

// NewRuleGenerator creates a new rule generator with the given seed
func NewRuleGenerator(seed int64) *RuleGenerator {
	return &RuleGenerator{
		rng: rand.New(rand.NewSource(seed)),
	}
}

// GenerateModules generates a set of modules for a game
func (r *RuleGenerator) GenerateModules(count int) []Module {
	modules := make([]Module, 0, count)

	// Always include certain modules
	moduleTypes := []ModuleType{
		ModuleWires,  // Always first - it's the most iconic
		ModuleKeypad, // Code entry
		ModuleSimon,  // Memory game
		ModuleMagnet, // Timing puzzle
	}

	// Shuffle module order
	r.shuffleModuleTypes(moduleTypes)

	// Take requested number of modules
	for i := 0; i < count && i < len(moduleTypes); i++ {
		modType := moduleTypes[i]
		module := r.generateModule(fmt.Sprintf("mod_%d", i+1), modType)
		modules = append(modules, module)
	}

	return modules
}

func (r *RuleGenerator) shuffleModuleTypes(types []ModuleType) {
	for i := len(types) - 1; i > 0; i-- {
		j := r.rng.Intn(i + 1)
		types[i], types[j] = types[j], types[i]
	}
}

func (r *RuleGenerator) generateModule(id string, modType ModuleType) Module {
	switch modType {
	case ModuleWires:
		return r.generateWiresModule(id)
	case ModuleKeypad:
		return r.generateKeypadModule(id)
	case ModuleSimon:
		return r.generateSimonModule(id)
	case ModuleMagnet:
		return r.generateMagnetModule(id)
	default:
		return Module{ID: id, Type: modType, State: ModuleStateActive}
	}
}

// generateWiresModule creates a Wires module with random wire configuration
func (r *RuleGenerator) generateWiresModule(id string) Module {
	// Shuffle wire colors
	wires := make([]WireColor, len(AllWireColors))
	copy(wires, AllWireColors)
	r.shuffleWireColors(wires)

	// Determine which wires need to be cut based on rules
	correctCuts := r.determineWireCuts(wires)

	config := map[string]interface{}{
		"wires":     wires,
		"cut_wires": []bool{false, false, false, false},
	}

	solution := map[string]interface{}{
		"correct_cuts": correctCuts,
	}

	return Module{
		ID:       id,
		Type:     ModuleWires,
		State:    ModuleStateActive,
		Config:   config,
		Solution: solution,
	}
}

func (r *RuleGenerator) shuffleWireColors(colors []WireColor) {
	for i := len(colors) - 1; i > 0; i-- {
		j := r.rng.Intn(i + 1)
		colors[i], colors[j] = colors[j], colors[i]
	}
}

// determineWireCuts applies rules to determine which wires to cut
// With 4 unique colors (red, blue, green, yellow), rules are based on positions
func (r *RuleGenerator) determineWireCuts(wires []WireColor) []int {
	// Rule set (varies by seed via random selection)
	ruleSet := r.rng.Intn(4)

	// Helper to find position of a color
	findColor := func(color WireColor) int {
		for i, w := range wires {
			if w == color {
				return i
			}
		}
		return -1
	}

	switch ruleSet {
	case 0:
		// If red is before blue, cut the red wire
		// Otherwise, cut the third wire
		redPos := findColor(WireRed)
		bluePos := findColor(WireBlue)
		if redPos < bluePos {
			return []int{redPos}
		}
		return []int{2}

	case 1:
		// If yellow is last, cut the first wire
		// Otherwise, cut the wire after blue
		if wires[3] == WireYellow {
			return []int{0}
		}
		bluePos := findColor(WireBlue)
		if bluePos < 3 {
			return []int{bluePos + 1}
		}
		return []int{0}

	case 2:
		// If green is in first or second position, cut green
		// Otherwise, cut the last wire
		greenPos := findColor(WireGreen)
		if greenPos <= 1 {
			return []int{greenPos}
		}
		return []int{3}

	case 3:
		// If blue is adjacent to yellow, cut blue
		// Otherwise, cut the second wire
		bluePos := findColor(WireBlue)
		yellowPos := findColor(WireYellow)
		if bluePos == yellowPos+1 || bluePos == yellowPos-1 {
			return []int{bluePos}
		}
		return []int{1}
	}

	return []int{0}
}

// generateKeypadModule creates a Keypad module with a random code
func (r *RuleGenerator) generateKeypadModule(id string) Module {
	// Generate a 3-digit code
	code := fmt.Sprintf("%d%d%d", r.rng.Intn(10), r.rng.Intn(10), r.rng.Intn(10))

	config := map[string]interface{}{
		"display_code": "_ _ _",
		"current_code": "",
		"code_length":  3,
	}

	solution := map[string]interface{}{
		"correct_code": code,
	}

	return Module{
		ID:       id,
		Type:     ModuleKeypad,
		State:    ModuleStateActive,
		Config:   config,
		Solution: solution,
	}
}

// generateSimonModule creates a Simon Says module with a color sequence
func (r *RuleGenerator) generateSimonModule(id string) Module {
	colors := []string{"red", "green", "blue"}
	sequenceLength := 3 + r.rng.Intn(2) // 3-4 colors

	sequence := make([]string, sequenceLength)
	expectedTaps := make([]int, sequenceLength)

	for i := 0; i < sequenceLength; i++ {
		colorIdx := r.rng.Intn(len(colors))
		sequence[i] = colors[colorIdx]

		// Taps based on color (rule varies by seed)
		switch sequence[i] {
		case "red":
			expectedTaps[i] = 1
		case "green":
			expectedTaps[i] = 2
		case "blue":
			expectedTaps[i] = 0 // Wait, don't tap
		}
	}

	config := map[string]interface{}{
		"sequence":       sequence,
		"current_index":  0,
		"showing_color":  "",
		"awaiting_input": false,
	}

	solution := map[string]interface{}{
		"expected_taps": expectedTaps,
	}

	return Module{
		ID:       id,
		Type:     ModuleSimon,
		State:    ModuleStateActive,
		Config:   config,
		Solution: solution,
	}
}

// generateMagnetModule creates a Magnet module with timing conditions
func (r *RuleGenerator) generateMagnetModule(id string) Module {
	config := map[string]interface{}{
		"led_color":     "red",
		"buzzer_active": true,
		"safe_window":   false,
	}

	// Safe condition: LED must be green AND buzzer must be silent
	solution := map[string]interface{}{
		"safe_conditions": map[string]interface{}{
			"led_color":     "green",
			"buzzer_active": false,
		},
	}

	return Module{
		ID:       id,
		Type:     ModuleMagnet,
		State:    ModuleStateActive,
		Config:   config,
		Solution: solution,
	}
}

// GetWiresManual returns the manual/instructions for the Wires module
func (r *RuleGenerator) GetWiresManual() []string {
	ruleSet := r.rng.Intn(4)

	switch ruleSet {
	case 0:
		return []string{
			"If red is before blue (reading left to right), cut the red wire.",
			"Otherwise, cut the third wire.",
		}
	case 1:
		return []string{
			"If yellow is in the last position, cut the first wire.",
			"Otherwise, cut the wire immediately after blue.",
		}
	case 2:
		return []string{
			"If green is in position 1 or 2, cut the green wire.",
			"Otherwise, cut the last wire.",
		}
	case 3:
		return []string{
			"If blue is next to yellow, cut the blue wire.",
			"Otherwise, cut the second wire.",
		}
	}

	return []string{"Cut the first wire."}
}

// GetKeypadManual returns the manual/instructions for the Keypad module
func (r *RuleGenerator) GetKeypadManual() []string {
	return []string{
		"The keypad requires a 3-digit code.",
		"Calculate the code as follows:",
		"  First digit: Number of RED wires",
		"  Second digit: Position of first BLUE wire (1-4, or 0 if none)",
		"  Third digit: Total number of wires NOT cut",
		"Use the rotary encoder to enter each digit.",
		"Press the encoder button to confirm each digit.",
	}
}

// GetSimonManual returns the manual/instructions for the Simon module
func (r *RuleGenerator) GetSimonManual() []string {
	return []string{
		"The RGB LED will flash a sequence of colors.",
		"For each color in the sequence:",
		"  RED: Tap the touch sensor ONCE",
		"  GREEN: Tap the touch sensor TWICE",
		"  BLUE: Do NOT tap - wait for the next color",
		"Complete the entire sequence correctly to solve the module.",
	}
}

// GetMagnetManual returns the manual/instructions for the Magnet module
func (r *RuleGenerator) GetMagnetManual() []string {
	return []string{
		"The magnet must be applied at the correct moment.",
		"Watch the LED indicator and listen to the buzzer.",
		"Apply the magnet ONLY when:",
		"  - The LED is GREEN",
		"  - AND the buzzer is SILENT",
		"Applying the magnet at any other time will cause a strike!",
	}
}

// GetFullManual returns the complete manual for all modules
func (r *RuleGenerator) GetFullManual() map[string][]string {
	// Reset RNG to ensure consistent manual generation
	r.rng = rand.New(rand.NewSource(r.rng.Int63()))

	return map[string][]string{
		"wires":  r.GetWiresManual(),
		"keypad": r.GetKeypadManual(),
		"simon":  r.GetSimonManual(),
		"magnet": r.GetMagnetManual(),
	}
}
