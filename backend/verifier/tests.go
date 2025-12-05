package verifier

import (
	"math"
)

type TestResult struct {
	Passed bool    `json:"passed"`
	Value  float64 `json:"value"`
}

// FrequencyTest checks if the ratio of 1s to 0s in the LSBs is balanced (45-55%)
func FrequencyTest(samples []int) TestResult {
	if len(samples) == 0 {
		return TestResult{Passed: false, Value: 0}
	}

	ones := 0
	total := 0

	for _, sample := range samples {
		for i := 0; i < 4; i++ {
			bit := (sample >> i) & 1
			ones += bit
			total++
		}
	}

	ratio := float64(ones) / float64(total)

	return TestResult{
		Passed: ratio >= 0.45 && ratio <= 0.55,
		Value:  ratio,
	}
}

// RunsTest checks for absence of long consecutive sequences of same bits
func RunsTest(samples []int) TestResult {
	if len(samples) == 0 {
		return TestResult{Passed: false, Value: 0}
	}

	bits := make([]int, 0, len(samples)*4)
	for _, sample := range samples {
		for i := 0; i < 4; i++ {
			bits = append(bits, (sample>>i)&1)
		}
	}

	if len(bits) < 2 {
		return TestResult{Passed: false, Value: 0}
	}

	maxRun := 1
	currentRun := 1
	totalRuns := 1

	for i := 1; i < len(bits); i++ {
		if bits[i] == bits[i-1] {
			currentRun++
			if currentRun > maxRun {
				maxRun = currentRun
			}
		} else {
			currentRun = 1
			totalRuns++
		}
	}

	// Max acceptable run length is 2 * log2(n)
	n := float64(len(bits))
	maxAcceptable := 2 * math.Log2(n)

	return TestResult{
		Passed: float64(maxRun) < maxAcceptable,
		Value:  float64(maxRun),
	}
}

// ChiSquareTest checks uniformity of 2-bit combinations
func ChiSquareTest(samples []int) TestResult {
	if len(samples) < 2 {
		return TestResult{Passed: false, Value: 0}
	}

	counts := make([]int, 4) // 00, 01, 10, 11

	for _, sample := range samples {
		for i := 0; i < 3; i++ {
			pair := (sample >> i) & 3
			counts[pair]++
		}
	}

	total := 0
	for _, c := range counts {
		total += c
	}

	if total == 0 {
		return TestResult{Passed: false, Value: 0}
	}

	expected := float64(total) / 4.0
	chiSquare := 0.0

	for _, observed := range counts {
		diff := float64(observed) - expected
		chiSquare += (diff * diff) / expected
	}

	// Chi-square critical value for 3 degrees of freedom at 0.05 significance
	return TestResult{
		Passed: chiSquare < 7.81,
		Value:  chiSquare,
	}
}

// VarianceTest checks if variance of LSBs is within expected range
func VarianceTest(samples []int) TestResult {
	if len(samples) < 2 {
		return TestResult{Passed: false, Value: 0}
	}

	lsbs := make([]float64, len(samples))
	sum := 0.0

	for i, sample := range samples {
		lsbs[i] = float64(sample & 0xF)
		sum += lsbs[i]
	}

	mean := sum / float64(len(samples))

	variance := 0.0
	for _, lsb := range lsbs {
		diff := lsb - mean
		variance += diff * diff
	}
	variance /= float64(len(samples) - 1)

	// Expected variance for uniform distribution [0, 15]: (16^2 - 1) / 12 ≈ 21.25
	expectedVariance := 21.25
	ratio := variance / expectedVariance

	return TestResult{
		Passed: ratio >= 0.5 && ratio <= 1.5,
		Value:  variance,
	}
}
