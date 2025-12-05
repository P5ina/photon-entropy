package verifier

type Tests struct {
	Frequency TestResult `json:"frequency"`
	Runs      TestResult `json:"runs"`
	ChiSquare TestResult `json:"chi_square"`
	Variance  TestResult `json:"variance"`
}

type VerifyResult struct {
	Quality float64 `json:"quality"`
	Tests   Tests   `json:"tests"`
}

type Verifier struct{}

func New() *Verifier {
	return &Verifier{}
}

func (v *Verifier) Verify(samples []int) VerifyResult {
	tests := Tests{
		Frequency: FrequencyTest(samples),
		Runs:      RunsTest(samples),
		ChiSquare: ChiSquareTest(samples),
		Variance:  VarianceTest(samples),
	}

	passed := 0
	if tests.Frequency.Passed {
		passed++
	}
	if tests.Runs.Passed {
		passed++
	}
	if tests.ChiSquare.Passed {
		passed++
	}
	if tests.Variance.Passed {
		passed++
	}

	return VerifyResult{
		Quality: float64(passed) / 4.0,
		Tests:   tests,
	}
}
