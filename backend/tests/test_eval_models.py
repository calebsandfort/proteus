"""Test suite for FR-7.1-7.6: Eval Framework.

Tests for:
- FR-7.1: Eval Suite Size (200+ test cases across 5 complexity levels)
- FR-7.2: Eval Dimensions and Metrics
- FR-7.4: Test Case Structure
- FR-7.5: Anomaly Injection
"""

import pytest
from src.eval.anomalies import (
    ANOMALY_TEST_CASES,
    AnomalyTestCase,
    get_anomaly_by_name,
    get_anomalies_by_category,
)
from src.eval.metrics import (
    EvalMetrics,
    MetricCalculator,
    compute_accuracy,
    compute_parameter_accuracy,
)
from src.eval.models import (
    ComplexityLevel,
    EvalResult,
    EvalRun,
    ExpectedParameter,
    TestFixture,
)


class TestTestFixture:
    """Tests for TestFixture model (FR-7.4)."""

    def test_test_fixture_creation(self):
        """Test creating a valid TestFixture."""
        fixture = TestFixture(
            id="test_001",
            description="Test fixture for market share query",
            natural_language_input="What is Walmart's market share in grocery?",
            expected_tools=["market_share_query"],
            expected_parameters=[
                ExpectedParameter(dimension="brand", values=["Walmart"])
            ],
            expected_result_characteristics={"type": "single_value"},
            complexity_level=ComplexityLevel.LEVEL_1_SIMPLE,
            category="market_share",
        )

        assert fixture.id == "test_001"
        assert fixture.natural_language_input == "What is Walmart's market share in grocery?"
        assert fixture.expected_tools == ["market_share_query"]
        assert len(fixture.expected_parameters) == 1
        assert fixture.expected_parameters[0].dimension == "brand"
        assert fixture.complexity_level == ComplexityLevel.LEVEL_1_SIMPLE

    def test_test_fixture_with_synonym_variations(self):
        """Test fixture with synonym variations (FR-7.4)."""
        fixture = TestFixture(
            id="test_002",
            description="Test with synonyms",
            natural_language_input="Walmart grocery share",
            expected_tools=["market_share_query"],
            expected_parameters=[
                ExpectedParameter(dimension="brand", values=["Walmart"])
            ],
            expected_result_characteristics={"type": "single_value"},
            complexity_level=ComplexityLevel.LEVEL_1_SIMPLE,
            synonym_variations=[
                "Walmart's share of grocery market",
                "Walmart grocery market share",
            ],
            category="market_share",
        )

        assert len(fixture.synonym_variations) == 2

    def test_complexity_level_enum(self):
        """Test all complexity levels are defined (FR-7.1)."""
        levels = [
            ComplexityLevel.LEVEL_1_SIMPLE,
            ComplexityLevel.LEVEL_2_MODERATE,
            ComplexityLevel.LEVEL_3_COMPLEX,
            ComplexityLevel.LEVEL_4_MULTI_TOOL,
            ComplexityLevel.LEVEL_5_AMBIGUOUS,
        ]

        assert len(levels) == 5
        assert all(isinstance(l.value, str) for l in levels)


class TestEvalResult:
    """Tests for EvalResult model (FR-7.4)."""

    def test_eval_result_creation(self):
        """Test creating a valid EvalResult."""
        result = EvalResult(
            fixture_id="test_001",
            trial_number=1,
            temperature=0.0,
            actual_tools=["market_share_query"],
            actual_parameters={"brand": ["Walmart"]},
            tool_selection_correct=True,
            dimension_extraction_correct=True,
            end_to_end_correct=True,
            latency_ms=150,
        )

        assert result.fixture_id == "test_001"
        assert result.trial_number == 1
        assert result.tool_selection_correct is True
        assert result.dimension_extraction_correct is True
        assert result.end_to_end_correct is True
        assert result.latency_ms == 150
        assert result.error is None

    def test_eval_result_with_error(self):
        """Test eval result with error."""
        result = EvalResult(
            fixture_id="test_001",
            trial_number=1,
            temperature=0.0,
            actual_tools=[],
            actual_parameters={},
            tool_selection_correct=False,
            dimension_extraction_correct=False,
            end_to_end_correct=False,
            latency_ms=50,
            error="Connection timeout",
        )

        assert result.error == "Connection timeout"

    def test_eval_result_trial_bounds(self):
        """Test trial number must be 1-3 (FR-7.2)."""
        with pytest.raises(Exception):
            EvalResult(
                fixture_id="test_001",
                trial_number=0,  # Invalid
                temperature=0.0,
                actual_tools=[],
                actual_parameters={},
                tool_selection_correct=False,
                dimension_extraction_correct=False,
                end_to_end_correct=False,
                latency_ms=0,
            )


class TestAnomalyTestCase:
    """Tests for AnomalyTestCase (FR-7.5)."""

    def test_anomaly_test_case_creation(self):
        """Test creating a valid AnomalyTestCase."""
        anomaly = AnomalyTestCase(
            name="holiday_spike_q4",
            description="Q4 holiday spike for retail",
            query="Show retail market share Q4 2024",
            expected_impact="Visible spike in December",
            injected_anomaly={"type": "seasonal", "months": [11, 12], "magnitude": 1.35},
            category="seasonal",
        )

        assert anomaly.name == "holiday_spike_q4"
        assert anomaly.category == "seasonal"
        assert anomaly.injected_anomaly["magnitude"] == 1.35

    def test_get_anomaly_by_name(self):
        """Test retrieving anomaly by name."""
        anomaly = get_anomaly_by_name("holiday_spike_q4_retail")
        assert anomaly is not None
        assert "holiday" in anomaly.name

    def test_get_anomaly_by_name_not_found(self):
        """Test retrieving non-existent anomaly raises error."""
        with pytest.raises(ValueError):
            get_anomaly_by_name("nonexistent_anomaly")

    def test_get_anomalies_by_category(self):
        """Test filtering anomalies by category."""
        seasonal_anomalies = get_anomalies_by_category("seasonal")
        assert len(seasonal_anomalies) > 0
        assert all(a.category == "seasonal" for a in seasonal_anomalies)

    def test_anomaly_test_cases_exist(self):
        """Test that anomaly test cases are defined (FR-7.5)."""
        assert len(ANOMALY_TEST_CASES) >= 5


class TestEvalMetrics:
    """Tests for EvalMetrics (FR-7.2)."""

    def test_eval_metrics_creation(self):
        """Test creating EvalMetrics."""
        metrics = EvalMetrics(
            tool_selection_accuracy=92.5,
            dimension_extraction_accuracy=87.0,
            end_to_end_accuracy=85.0,
            total_tests=100,
            passed_tests=85,
        )

        assert metrics.tool_selection_accuracy == 92.5
        assert metrics.dimension_extraction_accuracy == 87.0
        assert metrics.end_to_end_accuracy == 85.0

    def test_failure_rate_calculation(self):
        """Test failure rate calculation."""
        metrics = EvalMetrics(
            tool_selection_accuracy=90.0,
            dimension_extraction_accuracy=85.0,
            end_to_end_accuracy=80.0,
            total_tests=100,
            passed_tests=80,
        )

        assert metrics.failure_rate == 20.0

    def test_failure_rate_zero(self):
        """Test failure rate when all tests pass."""
        metrics = EvalMetrics(
            tool_selection_accuracy=100.0,
            dimension_extraction_accuracy=100.0,
            end_to_end_accuracy=100.0,
            total_tests=10,
            passed_tests=10,
        )

        assert metrics.failure_rate == 0.0

    def test_meets_targets(self):
        """Test target threshold checking (FR-7.2)."""
        metrics = EvalMetrics(
            tool_selection_accuracy=92.0,
            dimension_extraction_accuracy=88.0,
            end_to_end_accuracy=82.0,
            total_tests=100,
            passed_tests=82,
        )

        targets = metrics.meets_targets()
        assert targets["tool_selection"] is True
        assert targets["dimension_extraction"] is True
        assert targets["end_to_end"] is True

    def test_meets_targets_not_met(self):
        """Test targets not met scenario."""
        metrics = EvalMetrics(
            tool_selection_accuracy=85.0,  # Below 90
            dimension_extraction_accuracy=80.0,  # Below 85
            end_to_end_accuracy=75.0,  # Below 80
            total_tests=100,
            passed_tests=75,
        )

        targets = metrics.meets_targets()
        assert targets["tool_selection"] is False
        assert targets["dimension_extraction"] is False
        assert targets["end_to_end"] is False


class TestMetricCalculator:
    """Tests for MetricCalculator (FR-7.2)."""

    def test_calculate_tool_selection_accuracy(self):
        """Test tool selection accuracy calculation."""
        results = [
            EvalResult(
                fixture_id="test_001",
                trial_number=1,
                tool_selection_correct=True,
                dimension_extraction_correct=True,
                end_to_end_correct=True,
                latency_ms=100,
            ),
            EvalResult(
                fixture_id="test_002",
                trial_number=1,
                tool_selection_correct=True,
                dimension_extraction_correct=True,
                end_to_end_correct=True,
                latency_ms=100,
            ),
            EvalResult(
                fixture_id="test_003",
                trial_number=1,
                tool_selection_correct=False,  # Wrong tool
                dimension_extraction_correct=True,
                end_to_end_correct=False,
                latency_ms=100,
            ),
        ]

        fixtures = {
            "test_001": TestFixture(
                id="test_001",
                description="test",
                natural_language_input="test",
                expected_tools=["tool1"],
                expected_parameters=[],
                expected_result_characteristics={},
                complexity_level=ComplexityLevel.LEVEL_1_SIMPLE,
                category="test",
            ),
            "test_002": TestFixture(
                id="test_002",
                description="test",
                natural_language_input="test",
                expected_tools=["tool2"],
                expected_parameters=[],
                expected_result_characteristics={},
                complexity_level=ComplexityLevel.LEVEL_1_SIMPLE,
                category="test",
            ),
            "test_003": TestFixture(
                id="test_003",
                description="test",
                natural_language_input="test",
                expected_tools=["tool3"],
                expected_parameters=[],
                expected_result_characteristics={},
                complexity_level=ComplexityLevel.LEVEL_1_SIMPLE,
                category="test",
            ),
        }

        accuracy = MetricCalculator.calculate_tool_selection_accuracy(results, fixtures)
        assert accuracy == pytest.approx(66.67, rel=0.1)

    def test_calculate_dimension_extraction_accuracy(self):
        """Test dimension extraction accuracy calculation."""
        results = [
            EvalResult(
                fixture_id="test_001",
                trial_number=1,
                tool_selection_correct=True,
                dimension_extraction_correct=True,
                end_to_end_correct=True,
                latency_ms=100,
            ),
            EvalResult(
                fixture_id="test_002",
                trial_number=1,
                tool_selection_correct=True,
                dimension_extraction_correct=False,  # Wrong dimensions
                end_to_end_correct=False,
                latency_ms=100,
            ),
        ]

        fixtures = {
            "test_001": TestFixture(
                id="test_001",
                description="test",
                natural_language_input="test",
                expected_tools=["tool1"],
                expected_parameters=[],
                expected_result_characteristics={},
                complexity_level=ComplexityLevel.LEVEL_1_SIMPLE,
                category="test",
            ),
            "test_002": TestFixture(
                id="test_002",
                description="test",
                natural_language_input="test",
                expected_tools=["tool2"],
                expected_parameters=[],
                expected_result_characteristics={},
                complexity_level=ComplexityLevel.LEVEL_1_SIMPLE,
                category="test",
            ),
        }

        accuracy = MetricCalculator.calculate_dimension_extraction_accuracy(results, fixtures)
        assert accuracy == 50.0

    def test_calculate_end_to_end_accuracy(self):
        """Test end-to-end accuracy calculation (FR-7.2: 2 of 3 trials pass)."""
        results = [
            # Fixture 1: 2 of 3 pass -> should pass
            EvalResult(
                fixture_id="test_001", trial_number=1, tool_selection_correct=True,
                dimension_extraction_correct=True, end_to_end_correct=True, latency_ms=100
            ),
            EvalResult(
                fixture_id="test_001", trial_number=2, tool_selection_correct=True,
                dimension_extraction_correct=True, end_to_end_correct=True, latency_ms=100
            ),
            EvalResult(
                fixture_id="test_001", trial_number=3, tool_selection_correct=False,
                dimension_extraction_correct=False, end_to_end_correct=False, latency_ms=100
            ),
            # Fixture 2: 1 of 3 pass -> should fail
            EvalResult(
                fixture_id="test_002", trial_number=1, tool_selection_correct=True,
                dimension_extraction_correct=True, end_to_end_correct=True, latency_ms=100
            ),
            EvalResult(
                fixture_id="test_002", trial_number=2, tool_selection_correct=False,
                dimension_extraction_correct=False, end_to_end_correct=False, latency_ms=100
            ),
            EvalResult(
                fixture_id="test_002", trial_number=3, tool_selection_correct=False,
                dimension_extraction_correct=False, end_to_end_correct=False, latency_ms=100
            ),
        ]

        accuracy = MetricCalculator.calculate_end_to_end_accuracy(results)
        assert accuracy == 50.0  # 1 of 2 fixtures pass

    def test_calculate_all_metrics(self):
        """Test calculating all metrics at once."""
        # End-to-end accuracy requires 2 of 3 trials to pass per FR-7.2
        results = [
            # Need at least 2 trials that pass for a fixture to pass
            EvalResult(
                fixture_id="test_001", trial_number=1, tool_selection_correct=True,
                dimension_extraction_correct=True, end_to_end_correct=True, latency_ms=100
            ),
            EvalResult(
                fixture_id="test_001", trial_number=2, tool_selection_correct=True,
                dimension_extraction_correct=True, end_to_end_correct=True, latency_ms=100
            ),
            EvalResult(
                fixture_id="test_001", trial_number=3, tool_selection_correct=True,
                dimension_extraction_correct=True, end_to_end_correct=True, latency_ms=100
            ),
        ]

        fixtures = {
            "test_001": TestFixture(
                id="test_001",
                description="test",
                natural_language_input="test",
                expected_tools=["tool1"],
                expected_parameters=[],
                expected_result_characteristics={},
                complexity_level=ComplexityLevel.LEVEL_1_SIMPLE,
                category="test",
            ),
        }

        metrics = MetricCalculator.calculate_all_metrics(results, fixtures)

        assert metrics.tool_selection_accuracy == 100.0
        assert metrics.dimension_extraction_accuracy == 100.0
        assert metrics.end_to_end_accuracy == 100.0  # 2+ of 3 trials pass = pass


class TestComputeAccuracy:
    """Tests for compute_accuracy helper function."""

    def test_exact_match(self):
        """Test exact match returns 100% accuracy."""
        is_correct, accuracy = compute_accuracy(
            ["Walmart", "Target"], ["Walmart", "Target"]
        )
        assert is_correct is True
        assert accuracy == 100.0

    def test_partial_match(self):
        """Test partial match returns fractional accuracy."""
        is_correct, accuracy = compute_accuracy(
            ["Walmart", "Target", "Costco"], ["Walmart", "Target"]
        )
        assert is_correct is False
        assert accuracy == pytest.approx(66.67, rel=0.1)

    def test_no_match(self):
        """Test no match returns 0% accuracy."""
        is_correct, accuracy = compute_accuracy(
            ["Walmart"], ["Target"]
        )
        assert is_correct is False
        assert accuracy == 0.0

    def test_empty_expected(self):
        """Test empty expected returns 100% if actual also empty."""
        is_correct, accuracy = compute_accuracy([], [])
        assert is_correct is True
        assert accuracy == 100.0

    def test_empty_actual(self):
        """Test empty actual with non-empty expected returns 0%."""
        is_correct, accuracy = compute_accuracy(["Walmart"], [])
        assert is_correct is False
        assert accuracy == 0.0


class TestComputeParameterAccuracy:
    """Tests for compute_parameter_accuracy helper function."""

    def test_all_parameters_match(self):
        """Test all parameters matching."""
        expected_params = [
            ExpectedParameter(dimension="brand", values=["Walmart", "Target"]),
            ExpectedParameter(dimension="geography", values=["TX", "CA"]),
        ]
        actual_params = {
            "brand": ["Walmart", "Target"],
            "geography": ["TX", "CA"],
        }

        is_correct, accuracy = compute_parameter_accuracy(expected_params, actual_params)
        assert is_correct is True
        assert accuracy == 100.0

    def test_partial_parameters_match(self):
        """Test some parameters matching."""
        expected_params = [
            ExpectedParameter(dimension="brand", values=["Walmart", "Target"]),
            ExpectedParameter(dimension="geography", values=["TX", "CA"]),
        ]
        actual_params = {
            "brand": ["Walmart", "Target"],
            "geography": ["FL"],  # Missing TX, CA
        }

        is_correct, accuracy = compute_parameter_accuracy(expected_params, actual_params)
        assert is_correct is False
        assert accuracy == 50.0  # 1 of 2 correct

    def test_missing_dimension(self):
        """Test missing dimension in actual."""
        expected_params = [
            ExpectedParameter(dimension="brand", values=["Walmart"]),
        ]
        actual_params = {}  # Missing brand

        is_correct, accuracy = compute_parameter_accuracy(expected_params, actual_params)
        assert is_correct is False
        assert accuracy == 0.0


class TestEvalRun:
    """Tests for EvalRun model."""

    def test_eval_run_creation(self):
        """Test creating an EvalRun."""
        results = [
            EvalResult(
                fixture_id="test_001",
                trial_number=1,
                tool_selection_correct=True,
                dimension_extraction_correct=True,
                end_to_end_correct=True,
                latency_ms=100,
            ),
        ]

        run = EvalRun(
            run_id="run_001",
            fixture_results=results,
            aggregate_metrics={
                "tool_selection_accuracy": 100.0,
                "dimension_extraction_accuracy": 100.0,
                "end_to_end_accuracy": 100.0,
            },
            total_tests=1,
            passed_tests=1,
        )

        assert run.run_id == "run_001"
        assert len(run.fixture_results) == 1
        assert run.total_tests == 1
        assert run.passed_tests == 1