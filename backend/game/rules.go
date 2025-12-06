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

	// Always include certain modules (keypad removed - no rotary encoder)
	moduleTypes := []ModuleType{
		ModuleWires,  // Cut wires in correct order
		ModuleSimon,  // Color sequence - expert taps on mobile
		ModuleMagnet, // Timing puzzle - apply magnet at right moment
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

// generateWiresModule creates a Wires module
// Hardware has 4 LEDs: Red(0), Blue(1), Green(2), Yellow(3)
// Each game randomly enables/disables wires, rules based on which exist
func (r *RuleGenerator) generateWiresModule(id string) Module {
	// Randomly enable 2-4 wires
	wireEnabled := r.generateEnabledWires()

	// Determine which wire to cut based on rules
	correctWire := r.determineCorrectWire(wireEnabled)

	config := map[string]interface{}{
		"wire_enabled": wireEnabled, // Which wires exist in this game
		"cut_wires":    []bool{false, false, false, false},
	}

	solution := map[string]interface{}{
		"correct_cuts": []int{correctWire},
	}

	return Module{
		ID:       id,
		Type:     ModuleWires,
		State:    ModuleStateActive,
		Config:   config,
		Solution: solution,
	}
}

// generateEnabledWires randomly decides which wires are present (2-4 wires)
func (r *RuleGenerator) generateEnabledWires() []bool {
	// Always have at least 2 wires, up to 4
	numWires := 2 + r.rng.Intn(3) // 2, 3, or 4 wires

	enabled := []bool{false, false, false, false}
	indices := []int{0, 1, 2, 3}

	// Shuffle indices
	for i := len(indices) - 1; i > 0; i-- {
		j := r.rng.Intn(i + 1)
		indices[i], indices[j] = indices[j], indices[i]
	}

	// Enable first numWires
	for i := 0; i < numWires; i++ {
		enabled[indices[i]] = true
	}

	return enabled
}

// determineCorrectWire applies rules based on which wires are enabled
// Positions: 0=Red, 1=Blue, 2=Green, 3=Yellow
func (r *RuleGenerator) determineCorrectWire(wireEnabled []bool) int {
	hasRed := wireEnabled[0]
	hasBlue := wireEnabled[1]
	hasGreen := wireEnabled[2]
	hasYellow := wireEnabled[3]

	// Count enabled wires
	count := 0
	for _, e := range wireEnabled {
		if e {
			count++
		}
	}

	// Rule set based on seed
	ruleSet := r.rng.Intn(4)

	switch ruleSet {
	case 0:
		// If no green wire, cut red. Otherwise cut green.
		if !hasGreen && hasRed {
			return 0 // Red
		}
		if hasGreen {
			return 2 // Green
		}
	case 1:
		// If there are exactly 2 wires, cut yellow. Otherwise cut blue.
		if count == 2 && hasYellow {
			return 3 // Yellow
		}
		if hasBlue {
			return 1 // Blue
		}
	case 2:
		// If no blue wire, cut yellow. Otherwise cut red.
		if !hasBlue && hasYellow {
			return 3 // Yellow
		}
		if hasRed {
			return 0 // Red
		}
	case 3:
		// If both red and blue exist, cut blue. Otherwise cut the last enabled wire.
		if hasRed && hasBlue {
			return 1 // Blue
		}
	}

	// Fallback: cut the first enabled wire
	for i, e := range wireEnabled {
		if e {
			return i
		}
	}
	return 0
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
// Pi shows colors on RGB LED, Expert taps matching colors on mobile app
func (r *RuleGenerator) generateSimonModule(id string) Module {
	colors := []string{"red", "green", "blue"}
	sequenceLength := 3 + r.rng.Intn(2) // 3-4 colors

	sequence := make([]string, sequenceLength)

	for i := 0; i < sequenceLength; i++ {
		colorIdx := r.rng.Intn(len(colors))
		sequence[i] = colors[colorIdx]
	}

	config := map[string]interface{}{
		"sequence":      sequence, // Colors shown on Pi's RGB LED
		"current_index": 0,        // Expert's progress
	}

	solution := map[string]interface{}{
		"expected_colors": sequence, // Expert must tap same colors in order
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
// Rules are based on which wires are present (LEDs on)
func (r *RuleGenerator) GetWiresManual() []string {
	// Generate same enabled wires as generateWiresModule would
	_ = r.generateEnabledWires() // Consume RNG to stay in sync

	ruleSet := r.rng.Intn(4)

	switch ruleSet {
	case 0:
		return []string{
			"If there is NO green wire, cut RED.",
			"Otherwise, cut GREEN.",
		}
	case 1:
		return []string{
			"If there are exactly 2 wires, cut YELLOW.",
			"Otherwise, cut BLUE.",
		}
	case 2:
		return []string{
			"If there is NO blue wire, cut YELLOW.",
			"Otherwise, cut RED.",
		}
	case 3:
		return []string{
			"If both RED and BLUE wires exist, cut BLUE.",
			"Otherwise, cut the first available wire.",
		}
	}

	return []string{"Cut the first wire."}
}

// GetKeypadManual returns the manual/instructions for the Keypad module
func (r *RuleGenerator) GetKeypadManual() []string {
	// Generate the same code that generateKeypadModule produces
	code := fmt.Sprintf("%d%d%d", r.rng.Intn(10), r.rng.Intn(10), r.rng.Intn(10))

	return []string{
		fmt.Sprintf("Enter the code: %s", code),
		"Use the rotary encoder to select each digit.",
		"Press the encoder button to confirm.",
	}
}

// GetSimonManual returns the manual/instructions for the Simon module
func (r *RuleGenerator) GetSimonManual() []string {
	return []string{
		"The defuser will see colors flashing on the RGB LED.",
		"They must tell you the sequence of colors.",
		"Tap the matching color buttons below in the same order.",
		"Get the entire sequence correct to solve the module.",
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
