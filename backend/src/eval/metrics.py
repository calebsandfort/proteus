"""FR-7.2: Metrics Collection and Calculation.

This module provides metric calculators for evaluating the agent system
across tool selection, dimension extraction, visualization, and end-to-end accuracy.

FR Requirements:
- FR-7.2: Eval Dimensions and Metrics
  - Tool selection accuracy: target >=90%
  - Dimension extraction accuracy: target >=85%
  - Visualization selection accuracy: target >=85%
  - End-to-end correctness: target >=80%
  - Clarification appropriateness: target mean >=1.5

Models:
    EvalMetrics: Container for all calculated metrics
    MetricCalculator: Class for computing eval metrics
"""

from typing import Dict, List, Optional, Tuple

from src.eval.models import EvalResult, EvalRun, ExpectedParameter, TestFixture


class EvalMetrics:
    """Container for all calculated metrics.

    Attributes:
        tool_selection_accuracy: Percentage of correct tool selections.
        dimension_extraction_accuracy: Percentage of correct dimension extractions.
        visualization_accuracy: Percentage of correct visualization selections.
        end_to_end_accuracy: Percentage of correct end-to-end results.
        clarification_score: Mean clarification appropriateness (0-2 scale).
        total_tests: Total number of tests run.
        passed_tests: Number of tests passed.
        failure_rate: Percentage of tests that failed.
    """

    def __init__(
        self,
        tool_selection_accuracy: float = 0.0,
        dimension_extraction_accuracy: float = 0.0,
        visualization_accuracy: Optional[float] = None,
        end_to_end_accuracy: float = 0.0,
        clarification_score: Optional[float] = None,
        total_tests: int = 0,
        passed_tests: int = 0,
    ):
        self.tool_selection_accuracy = tool_selection_accuracy
        self.dimension_extraction_accuracy = dimension_extraction_accuracy
        self.visualization_accuracy = visualization_accuracy
        self.end_to_end_accuracy = end_to_end_accuracy
        self.clarification_score = clarification_score
        self.total_tests = total_tests
        self.passed_tests = passed_tests

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return ((self.total_tests - self.passed_tests) / self.total_tests) * 100

    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary for serialization."""
        result = {
            "tool_selection_accuracy": self.tool_selection_accuracy,
            "dimension_extraction_accuracy": self.dimension_extraction_accuracy,
            "end_to_end_accuracy": self.end_to_end_accuracy,
            "total_tests": float(self.total_tests),
            "passed_tests": float(self.passed_tests),
            "failure_rate": self.failure_rate,
        }
        if self.visualization_accuracy is not None:
            result["visualization_accuracy"] = self.visualization_accuracy
        if self.clarification_score is not None:
            result["clarification_score"] = self.clarification_score
        return result

    def meets_targets(self) -> Dict[str, bool]:
        """Check if metrics meet the target thresholds.

        Returns:
            Dict mapping metric name to whether target is met.
        """
        return {
            "tool_selection": self.tool_selection_accuracy >= 90.0,
            "dimension_extraction": self.dimension_extraction_accuracy >= 85.0,
            "visualization": (
                self.visualization_accuracy is not None
                and self.visualization_accuracy >= 85.0
            ),
            "end_to_end": self.end_to_end_accuracy >= 80.0,
            "clarification": (
                self.clarification_score is not None
                and self.clarification_score >= 1.5
            ),
        }


class MetricCalculator:
    """Calculator for computing eval metrics from test results."""

    @staticmethod
    def calculate_tool_selection_accuracy(
        results: List[EvalResult],
        fixtures: Dict[str, TestFixture],
    ) -> float:
        """Calculate tool selection accuracy.

        FR-7.2: Tool selection accuracy = % correct tool(s) selected
        Target: >=90%

        Args:
            results: List of eval results.
            fixtures: Dict mapping fixture ID to TestFixture.

        Returns:
            Percentage of correct tool selections (0-100).
        """
        if not results:
            return 0.0

        correct_count = sum(1 for r in results if r.tool_selection_correct)
        return (correct_count / len(results)) * 100

    @staticmethod
    def calculate_dimension_extraction_accuracy(
        results: List[EvalResult],
        fixtures: Dict[str, TestFixture],
    ) -> float:
        """Calculate dimension extraction accuracy.

        FR-7.2: Dimension extraction accuracy = % correct parameter values
        Target: >=85%

        Args:
            results: List of eval results.
            fixtures: Dict mapping fixture ID to TestFixture.

        Returns:
            Percentage of correct dimension extractions (0-100).
        """
        if not results:
            return 0.0

        correct_count = sum(1 for r in results if r.dimension_extraction_correct)
        return (correct_count / len(results)) * 100

    @staticmethod
    def calculate_visualization_accuracy(
        results: List[EvalResult],
    ) -> Optional[float]:
        """Calculate visualization selection accuracy.

        FR-7.2: Visualization selection accuracy = % correct chart type selected
        Target: >=85%

        Args:
            results: List of eval results.

        Returns:
            Percentage of correct visualization selections, or None if not available.
        """
        results_with_viz = [r for r in results if r.visualization_correct is not None]

        if not results_with_viz:
            return None

        correct_count = sum(1 for r in results_with_viz if r.visualization_correct)
        return (correct_count / len(results_with_viz)) * 100

    @staticmethod
    def calculate_end_to_end_accuracy(
        results: List[EvalResult],
    ) -> float:
        """Calculate end-to-end correctness.

        FR-7.2: A test case passes if 2 of 3 trials return structurally correct results.
        Target: >=80%

        Args:
            results: List of eval results.

        Returns:
            Percentage of test cases that passed (0-100).
        """
        if not results:
            return 0.0

        # Group results by fixture_id
        fixture_results: Dict[str, List[EvalResult]] = {}
        for r in results:
            if r.fixture_id not in fixture_results:
                fixture_results[r.fixture_id] = []
            fixture_results[r.fixture_id].append(r)

        total_fixtures = len(fixture_results)

        # Edge case: if only 1 trial per fixture, pass if that trial passes
        # (Full 2-of-3 requirement applies when 3 trials are run)
        first_trial_results = list(fixture_results.values())[0] if fixture_results else []
        if len(first_trial_results) == 1:
            passed_fixtures = sum(1 for r in first_trial_results if r.end_to_end_correct)
            return (passed_fixtures / total_fixtures * 100) if total_fixtures > 0 else 0.0

        # A fixture passes if at least 2 of 3 trials pass
        passed_fixtures = 0

        for fixture_id, trial_results in fixture_results.items():
            # Count successful trials
            successful_trials = sum(1 for r in trial_results if r.end_to_end_correct)
            if successful_trials >= 2:
                passed_fixtures += 1

        return (passed_fixtures / total_fixtures * 100) if total_fixtures > 0 else 0.0

    @staticmethod
    def calculate_clarification_score(
        results: List[EvalResult],
        clarification_ratings: Dict[str, int],
    ) -> Optional[float]:
        """Calculate clarification appropriateness score.

        FR-7.2: Clarification appropriateness - human-rated 0-2 scale
        Target: mean >=1.5

        Args:
            results: List of eval results.
            clarification_ratings: Dict mapping fixture_id to rating (0-2).

        Returns:
            Mean clarification score, or None if no ratings available.
        """
        if not clarification_ratings:
            return None

        total = sum(clarification_ratings.values())
        count = len(clarification_ratings)

        return total / count if count > 0 else None

    @staticmethod
    def calculate_all_metrics(
        results: List[EvalResult],
        fixtures: Dict[str, TestFixture],
        clarification_ratings: Optional[Dict[str, int]] = None,
    ) -> EvalMetrics:
        """Calculate all metrics from eval results.

        Args:
            results: List of eval results.
            fixtures: Dict mapping fixture ID to TestFixture.
            optional_clarification_ratings: Optional dict of clarification ratings.

        Returns:
            EvalMetrics with all calculated values.
        """
        tool_acc = MetricCalculator.calculate_tool_selection_accuracy(results, fixtures)
        dim_acc = MetricCalculator.calculate_dimension_extraction_accuracy(results, fixtures)
        viz_acc = MetricCalculator.calculate_visualization_accuracy(results)
        e2e_acc = MetricCalculator.calculate_end_to_end_accuracy(results)

        clar_score = None
        if clarification_ratings:
            clar_score = MetricCalculator.calculate_clarification_score(
                results, clarification_ratings
            )

        total_tests = len(set(r.fixture_id for r in results))
        passed_tests = sum(
            1 for r in results
            if r.end_to_end_correct and r.error is None
        )

        return EvalMetrics(
            tool_selection_accuracy=tool_acc,
            dimension_extraction_accuracy=dim_acc,
            visualization_accuracy=viz_acc,
            end_to_end_accuracy=e2e_acc,
            clarification_score=clar_score,
            total_tests=total_tests,
            passed_tests=passed_tests,
        )

    @staticmethod
    def calculate_metrics_by_complexity(
        results: List[EvalResult],
        fixtures: Dict[str, TestFixture],
    ) -> Dict[str, EvalMetrics]:
        """Calculate metrics grouped by complexity level.

        Args:
            results: List of eval results.
            fixtures: Dict mapping fixture ID to TestFixture.

        Returns:
            Dict mapping complexity level to metrics.
        """
        # Group results by complexity level
        results_by_level: Dict[str, List[EvalResult]] = {}

        for result in results:
            fixture = fixtures.get(result.fixture_id)
            if fixture:
                level = fixture.complexity_level.value
                if level not in results_by_level:
                    results_by_level[level] = []
                results_by_level[level].append(result)

        # Calculate metrics for each level
        metrics_by_level = {}
        for level, level_results in results_by_level.items():
            metrics_by_level[level] = MetricCalculator.calculate_all_metrics(
                level_results, fixtures
            )

        return metrics_by_level


def compute_accuracy(expected: List[str], actual: List[str]) -> Tuple[bool, float]:
    """Compute accuracy between expected and actual values.

    Args:
        expected: List of expected values.
        actual: List of actual values.

    Returns:
        Tuple of (is_correct, accuracy_percentage).
    """
    if not expected and not actual:
        return True, 100.0

    if not expected or not actual:
        return False, 0.0

    # Calculate overlap
    expected_set = set(expected)
    actual_set = set(actual)

    overlap = len(expected_set.intersection(actual_set))
    total = len(expected_set)

    accuracy = (overlap / total) * 100 if total > 0 else 0.0
    is_correct = overlap == total

    return is_correct, accuracy


def compute_parameter_accuracy(
    expected_params: List[ExpectedParameter],
    actual_params: Dict[str, List[str]],
) -> Tuple[bool, float]:
    """Compute accuracy for parameter extraction.

    Args:
        expected_params: List of expected parameters.
        actual_params: Dict of actual parameter values.

    Returns:
        Tuple of (is_correct, accuracy_percentage).
    """
    if not expected_params:
        return True, 100.0

    correct_count = 0
    total_count = len(expected_params)

    for expected in expected_params:
        actual_values = actual_params.get(expected.dimension, [])
        is_correct, _ = compute_accuracy(expected.values, actual_values)
        if is_correct:
            correct_count += 1

    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0.0
    is_correct = correct_count == total_count

    return is_correct, accuracy