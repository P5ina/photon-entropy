import math
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    passed: bool
    value: float


@dataclass
class TestResults:
    frequency: TestResult
    runs: TestResult
    chi_square: TestResult
    variance: TestResult

    @property
    def quality(self) -> float:
        passed = sum([
            self.frequency.passed,
            self.runs.passed,
            self.chi_square.passed,
            self.variance.passed,
        ])
        return passed / 4.0

    @property
    def all_passed(self) -> bool:
        return all([
            self.frequency.passed,
            self.runs.passed,
            self.chi_square.passed,
            self.variance.passed,
        ])


class EntropyTester:
    def test(self, samples: List[int]) -> TestResults:
        return TestResults(
            frequency=self.frequency_test(samples),
            runs=self.runs_test(samples),
            chi_square=self.chi_square_test(samples),
            variance=self.variance_test(samples),
        )

    def frequency_test(self, samples: List[int]) -> TestResult:
        """Check if ratio of 1s to 0s in LSBs is balanced (45-55%)."""
        if not samples:
            return TestResult(passed=False, value=0.0)

        ones = 0
        total = 0

        for sample in samples:
            for i in range(4):
                bit = (sample >> i) & 1
                ones += bit
                total += 1

        ratio = ones / total if total > 0 else 0

        passed = 0.45 <= ratio <= 0.55
        logger.debug(f"Frequency test: ratio={ratio:.4f}, passed={passed}")

        return TestResult(passed=passed, value=ratio)

    def runs_test(self, samples: List[int]) -> TestResult:
        """Check for absence of long consecutive sequences of same bits."""
        if not samples:
            return TestResult(passed=False, value=0.0)

        bits = []
        for sample in samples:
            for i in range(4):
                bits.append((sample >> i) & 1)

        if len(bits) < 2:
            return TestResult(passed=False, value=0.0)

        max_run = 1
        current_run = 1

        for i in range(1, len(bits)):
            if bits[i] == bits[i - 1]:
                current_run += 1
                if current_run > max_run:
                    max_run = current_run
            else:
                current_run = 1

        # Max acceptable run length is 2 * log2(n)
        n = len(bits)
        max_acceptable = 2 * math.log2(n)

        passed = max_run < max_acceptable
        logger.debug(f"Runs test: max_run={max_run}, max_acceptable={max_acceptable:.1f}, passed={passed}")

        return TestResult(passed=passed, value=float(max_run))

    def chi_square_test(self, samples: List[int]) -> TestResult:
        """Check uniformity of 2-bit combinations."""
        if len(samples) < 2:
            return TestResult(passed=False, value=0.0)

        counts = [0, 0, 0, 0]  # 00, 01, 10, 11

        for sample in samples:
            for i in range(3):
                pair = (sample >> i) & 3
                counts[pair] += 1

        total = sum(counts)
        if total == 0:
            return TestResult(passed=False, value=0.0)

        expected = total / 4.0
        chi_square = sum((observed - expected) ** 2 / expected for observed in counts)

        # Chi-square critical value for 3 degrees of freedom at 0.05 significance
        passed = chi_square < 7.81
        logger.debug(f"Chi-square test: chi_square={chi_square:.4f}, passed={passed}")

        return TestResult(passed=passed, value=chi_square)

    def variance_test(self, samples: List[int]) -> TestResult:
        """Check if variance of LSBs is within expected range."""
        if len(samples) < 2:
            return TestResult(passed=False, value=0.0)

        lsbs = [sample & 0xF for sample in samples]
        mean = sum(lsbs) / len(lsbs)
        variance = sum((lsb - mean) ** 2 for lsb in lsbs) / (len(samples) - 1)

        # Expected variance for uniform distribution [0, 15]: (16^2 - 1) / 12 ≈ 21.25
        expected_variance = 21.25
        ratio = variance / expected_variance

        passed = 0.5 <= ratio <= 1.5
        logger.debug(f"Variance test: variance={variance:.4f}, ratio={ratio:.4f}, passed={passed}")

        return TestResult(passed=passed, value=variance)
