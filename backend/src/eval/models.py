"""FR-7.1-7.6: Eval Framework Models.

This module defines the Pydantic models for the evaluation framework.

FR Requirements:
- FR-7.1: Eval Suite Size (200+ test cases across 5 complexity levels)
- FR-7.2: Eval Dimensions and Metrics (tool selection, dimension extraction, visualization)
- FR-7.4: Test Case Structure (TestFixture, EvalResult, EvalRun)

Models:
    ComplexityLevel: Enum for 5 complexity levels
    ExpectedParameter: Expected parameter values for test case
    TestFixture: Complete test case definition
    EvalResult: Result of a single test execution
    EvalRun: Complete eval run with aggregate metrics
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    """Complexity levels for test cases.

    FR-7.1: Distribution across 5 levels:
    - Level 1 (Simple): 30% (60 cases) -- single-tool, single-dimension
    - Level 2 (Moderate): 35% (70 cases) -- single-tool, 2-4 dimensions
    - Level 3 (Complex): 15% (30 cases) -- single-tool, 5+ dimensions
    - Level 4 (Multi-tool): 10% (20 cases) -- planner decomposition correctness
    - Level 5 (Ambiguous): 10% (20 cases) -- HITL appropriateness
    """

    LEVEL_1_SIMPLE = "level_1_simple"
    LEVEL_2_MODERATE = "level_2_moderate"
    LEVEL_3_COMPLEX = "level_3_complex"
    LEVEL_4_MULTI_TOOL = "level_4_multi_tool"
    LEVEL_5_AMBIGUOUS = "level_5_ambiguous"


class ExpectedParameter(BaseModel):
    """Expected parameter values for a test case.

    Attributes:
        dimension: Name of the dimension (e.g., "brand", "geography").
        values: List of expected values for this dimension.
        tolerance: Optional tolerance for numeric values (e.g., 0.05 for 5%).
    """

    dimension: str = Field(..., description="Name of the dimension")
    values: List[str] = Field(..., description="Expected values for this dimension")
    tolerance: Optional[float] = Field(
        default=None,
        description="Tolerance for numeric values (e.g., 0.05 for 5%)",
    )


class TestFixture(BaseModel):
    """Complete test case definition.

    FR-7.4: Each test case includes:
    - Natural language input
    - Expected tool(s)
    - Expected parameters
    - Expected result characteristics
    - Complexity level
    - Synonym variations for key concepts

    Attributes:
        id: Unique identifier for this test fixture.
        description: Human-readable description of the test case.
        natural_language_input: The query to test.
        expected_tools: List of expected tool IDs that should be selected.
        expected_parameters: List of expected parameters with values.
        expected_result_characteristics: Dict of expected result characteristics.
        complexity_level: Complexity level for this test case.
        synonym_variations: Alternative phrasings of the query.
        category: Category for grouping analysis (e.g., "market_share", "brand_comparison").
    """

    id: str = Field(..., description="Unique identifier for this test fixture")
    description: str = Field(..., description="Human-readable description of the test case")
    natural_language_input: str = Field(
        ..., description="The query to test"
    )
    expected_tools: List[str] = Field(
        ..., description="List of expected tool IDs that should be selected"
    )
    expected_parameters: List[ExpectedParameter] = Field(
        ..., description="List of expected parameters with values"
    )
    expected_result_characteristics: Dict[str, Any] = Field(
        ..., description="Dict of expected result characteristics"
    )
    complexity_level: ComplexityLevel = Field(
        ..., description="Complexity level for this test case"
    )
    synonym_variations: List[str] = Field(
        default_factory=list,
        description="Alternative phrasings of the query",
    )
    category: str = Field(..., description="Category for grouping analysis")


class EvalResult(BaseModel):
    """Result of a single test execution.

    FR-7.2: Eval dimensions and metrics:
    - Tool selection accuracy: % correct tool(s) selected -- target >=90%
    - Dimension extraction accuracy: % correct parameter values -- target >=85%
    - Visualization selection accuracy: % correct chart type selected -- target >=85%
    - End-to-end result correctness: Target >=80% of test cases passing
    - Clarification appropriateness: Target mean >=1.5 (human-rated 0-2 scale)

    Attributes:
        fixture_id: ID of the test fixture that was run.
        trial_number: Trial number (1-3) for this execution.
        temperature: Temperature used for this trial (default 0.0).
        actual_tools: List of tool IDs that were actually selected.
        actual_parameters: Dict of actual parameter values extracted.
        tool_selection_correct: Whether the correct tool(s) were selected.
        dimension_extraction_correct: Whether dimensions were extracted correctly.
        visualization_correct: Optional bool for visualization correctness.
        end_to_end_correct: Whether the end-to-end result was structurally correct.
        latency_ms: Latency of the query execution in milliseconds.
        error: Optional error message if execution failed.
    """

    fixture_id: str = Field(..., description="ID of the test fixture that was run")
    trial_number: int = Field(..., ge=1, le=3, description="Trial number (1-3) for this execution")
    temperature: float = Field(default=0.0, description="Temperature used for this trial")
    actual_tools: List[str] = Field(
        default_factory=list,
        description="List of tool IDs that were actually selected",
    )
    actual_parameters: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Dict of actual parameter values extracted",
    )
    tool_selection_correct: bool = Field(
        ..., description="Whether the correct tool(s) were selected"
    )
    dimension_extraction_correct: bool = Field(
        ..., description="Whether dimensions were extracted correctly"
    )
    visualization_correct: Optional[bool] = Field(
        default=None,
        description="Optional bool for visualization correctness",
    )
    end_to_end_correct: bool = Field(
        ..., description="Whether the end-to-end result was structurally correct"
    )
    latency_ms: int = Field(..., ge=0, description="Latency of the query execution in milliseconds")
    error: Optional[str] = Field(
        default=None,
        description="Optional error message if execution failed",
    )


class EvalRun(BaseModel):
    """Complete eval run with aggregate metrics.

    Attributes:
        run_id: Unique identifier for this eval run.
        timestamp: Timestamp when the eval run was executed.
        fixture_results: List of results for each test fixture execution.
        aggregate_metrics: Dict of aggregate metrics (accuracy percentages, etc.).
        total_tests: Total number of tests run.
        passed_tests: Number of tests that passed.
    """

    run_id: str = Field(..., description="Unique identifier for this eval run")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the eval run was executed",
    )
    fixture_results: List[EvalResult] = Field(
        default_factory=list,
        description="List of results for each test fixture execution",
    )
    aggregate_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Dict of aggregate metrics (accuracy percentages, etc.)",
    )
    total_tests: int = Field(default=0, description="Total number of tests run")
    passed_tests: int = Field(default=0, description="Number of tests that passed")


# Type alias for fixture collections
TestFixtureCollection = List[TestFixture]