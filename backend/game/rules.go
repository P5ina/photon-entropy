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

// generateWiresModule creates a Wires module
// Hardware has fixed LEDs: Red(1), Blue(2), Green(3), Yellow(4)
// Rule determines which button(s) to press based on game seed
func (r *RuleGenerator) generateWiresModule(id string) Module {
	// Fixed wire colors at positions 0-3: Red, Blue, Green, Yellow
	wires := []WireColor{WireRed, WireBlue, WireGreen, WireYellow}

	// Determine which button to press based on rule set
	correctButton := r.determineCorrectButton()

	config := map[string]interface{}{
		"wires":     wires,
		"cut_wires": []bool{false, false, false, false},
	}

	solution := map[string]interface{}{
		"correct_cuts": []int{correctButton},
	}

	return Module{
		ID:       id,
		Type:     ModuleWires,
		State:    ModuleStateActive,
		Config:   config,
		Solution: solution,
	}
}

// determineCorrectButton picks which button to press based on rule set
// Positions: 0=Red, 1=Blue, 2=Green, 3=Yellow
func (r *RuleGenerator) determineCorrectButton() int {
	// Randomly select which button is correct (0-3)
	return r.rng.Intn(4)
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
// Fixed layout: Button 1=Red, 2=Blue, 3=Green, 4=Yellow
// The correct button is determined by game seed
func (r *RuleGenerator) GetWiresManual() []string {
	correctButton := r.rng.Intn(4)
	colors := []string{"RED", "BLUE", "GREEN", "YELLOW"}

	return []string{
		fmt.Sprintf("Press the %s button.", colors[correctButton]),
	}
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
