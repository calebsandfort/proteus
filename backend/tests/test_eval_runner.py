"""Test suite for EvalRunner class."""

import asyncio
import pytest
from src.eval.runner import EvalRunner, EvalRunnerConfig
from src.eval.models import ComplexityLevel


class TestEvalRunnerConfig:
    """Tests for EvalRunnerConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = EvalRunnerConfig()
        assert config.num_trials == 3
        assert config.temperature == 0.0
        assert config.parallel_execution is True
        assert config.max_concurrent == 10

    def test_custom_config(self):
        """Test custom configuration."""
        config = EvalRunnerConfig(
            num_trials=5,
            temperature=0.5,
            parallel_execution=False,
        )
        assert config.num_trials == 5
        assert config.temperature == 0.5
        assert config.parallel_execution is False


class TestEvalRunner:
    """Tests for EvalRunner class."""

    def test_runner_initialization(self):
        """Test creating an EvalRunner."""
        runner = EvalRunner()
        assert runner.config.num_trials == 3
        assert runner._fixtures_loaded is False

    def test_load_fixtures_creates_defaults(self):
        """Test loading fixtures creates default fixtures."""
        runner = EvalRunner()
        runner.load_fixtures()

        assert runner._fixtures_loaded is True
        assert len(runner.fixtures) > 0

    def test_fixture_count_distribution(self):
        """Test that fixtures are created for all complexity levels."""
        runner = EvalRunner()
        runner.load_fixtures()

        # Count by complexity level
        by_level = {}
        for fixture in runner.fixtures.values():
            level = fixture.complexity_level.value
            by_level[level] = by_level.get(level, 0) + 1

        # Should have fixtures for all 5 levels
        assert len(by_level) == 5

        # FR-7.1 distribution: Level 1 (30%), Level 2 (35%), Level 3 (15%), Level 4 (10%), Level 5 (10%)
        # Our default fixtures have at least some for each
        assert "level_1_simple" in by_level
        assert "level_2_moderate" in by_level
        assert "level_3_complex" in by_level
        assert "level_4_multi_tool" in by_level
        assert "level_5_ambiguous" in by_level

    def test_run_single_fixture_mock(self):
        """Test running a single fixture with mock execution."""
        runner = EvalRunner()
        runner.load_fixtures()

        # Get first fixture
        fixture = next(iter(runner.fixtures.values()))

        # Run without agent executor (mock)
        result = asyncio.run(runner.run_single_fixture(fixture, 1, None))

        assert result.fixture_id == fixture.id
        assert result.trial_number == 1
        assert result.temperature == runner.config.temperature

    def test_run_eval_filters_by_complexity(self):
        """Test filtering fixtures by complexity level."""
        runner = EvalRunner()
        runner.load_fixtures()

        # Run eval with complexity filter
        eval_run = asyncio.run(runner.run_eval(
            filter_complexity=ComplexityLevel.LEVEL_1_SIMPLE
        ))

        # Should only run Level 1 fixtures
        level_1_results = [r for r in eval_run.fixture_results
                          if r.fixture_id.startswith("level_1")]

        # At least some Level 1 fixtures should exist
        assert len(level_1_results) > 0

    def test_run_eval_filters_by_category(self):
        """Test filtering fixtures by category."""
        runner = EvalRunner()
        runner.load_fixtures()

        # Run eval with category filter
        eval_run = asyncio.run(runner.run_eval(
            filter_category="market_share"
        ))

        # Should only run market_share category fixtures
        assert eval_run.total_tests > 0

    def test_evaluate_tool_selection(self):
        """Test tool selection evaluation logic."""
        runner = EvalRunner()

        # Exact match
        assert runner._evaluate_tool_selection(
            ["tool1", "tool2"],
            ["tool1", "tool2"]
        ) is True

        # Subset match (actual contains all expected)
        assert runner._evaluate_tool_selection(
            ["tool1"],
            ["tool1", "tool2"]
        ) is True

        # Mismatch
        assert runner._evaluate_tool_selection(
            ["tool1"],
            ["tool2"]
        ) is False

        # Empty
        assert runner._evaluate_tool_selection([], []) is False

    def test_evaluate_dimension_extraction(self):
        """Test dimension extraction evaluation logic."""
        runner = EvalRunner()

        from src.eval.models import ExpectedParameter

        # Exact match
        assert runner._evaluate_dimension_extraction(
            [ExpectedParameter(dimension="brand", values=["Walmart", "Target"])],
            {"brand": ["Walmart", "Target"]}
        ) is True

        # Partial match (at least one value overlaps)
        assert runner._evaluate_dimension_extraction(
            [ExpectedParameter(dimension="brand", values=["Walmart", "Target"])],
            {"brand": ["Walmart", "Costco"]}
        ) is True

        # No match
        assert runner._evaluate_dimension_extraction(
            [ExpectedParameter(dimension="brand", values=["Walmart"])],
            {"brand": ["Target"]}
        ) is False

        # Missing dimension
        assert runner._evaluate_dimension_extraction(
            [ExpectedParameter(dimension="brand", values=["Walmart"])],
            {"geography": ["TX"]}
        ) is False

    def test_extract_brand_from_query(self):
        """Test brand extraction from query."""
        runner = EvalRunner()

        brands = runner._extract_brand_from_query("Walmart grocery market share")
        assert "Walmart" in brands

        brands = runner._extract_brand_from_query("McDonald's vs Burger King")
        assert "Mcdonald" in brands
        assert "Burger King" in brands

        brands = runner._extract_brand_from_query("Show me trends")
        assert brands == ["unknown"]

    def test_extract_geo_from_query(self):
        """Test geography extraction from query."""
        runner = EvalRunner()

        geos = runner._extract_geo_from_query("Compare Texas and California")
        assert "TX" in geos
        assert "CA" in geos

        geos = runner._extract_geo_from_query("Florida market")
        assert "FL" in geos

    def test_summary_generation(self):
        """Test eval run summary generation."""
        runner = EvalRunner()

        from src.eval.models import EvalResult, EvalRun
        from datetime import datetime

        eval_run = EvalRun(
            run_id="test_run",
            timestamp=datetime.now(),
            aggregate_metrics={
                "tool_selection_accuracy": 92.0,
                "dimension_extraction_accuracy": 87.0,
                "end_to_end_accuracy": 85.0,
            },
            total_tests=100,
            passed_tests=85,
        )

        summary = runner.get_summary(eval_run)

        assert "test_run" in summary
        assert "92.0" in summary
        assert "✓" in summary  # Targets met

    def test_save_results(self, tmp_path, monkeypatch):
        """Test saving results to file."""
        # Set results dir to temp
        config = EvalRunnerConfig(results_dir=str(tmp_path))
        runner = EvalRunner(config)

        from src.eval.models import EvalResult, EvalRun
        from datetime import datetime

        eval_run = EvalRun(
            run_id="test_run",
            timestamp=datetime.now(),
            aggregate_metrics={"tool_selection_accuracy": 90.0},
            total_tests=10,
            passed_tests=9,
        )

        runner.save_results(eval_run)

        # Check file exists
        result_file = tmp_path / "test_run.json"
        assert result_file.exists()