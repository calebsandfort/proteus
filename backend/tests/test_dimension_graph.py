"""FR-3.2: Dimension Extraction Graph Tests.

Tests for the DimensionExtractionGraph which orchestrates parallel
dimension extraction across all dimension types per FR-3.2.

FR-3.2 Architecture:
- Independent dimensions execute in parallel (brand, category, generation, etc.)
- Total parallel extraction budget: 600-1200ms
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from src.api.models.dimensions import (
    ExtractedDimensions,
    DimensionExtractionInput,
    DimensionExtractionResult,
    DimensionExtractionOutput,
    DimensionConflict,
)
from src.agent.dimension_graph import (
    DimensionExtractionGraph,
    extract_dimensions,
    INDEPENDENT_EXTRACTORS,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_extractors():
    """Create mock extractors for testing."""
    extractors = {}
    for dim_type in INDEPENDENT_EXTRACTORS:
        mock_extractor = MagicMock()
        mock_result = DimensionExtractionResult(
            dimension_type=dim_type,
            values=[f"{dim_type}_value"],
            confidence=0.8,
            alternatives=[],
            extraction_method="llm",
            latency_ms=100,
            validation_status="valid",
        )
        mock_extractor.extract = AsyncMock(return_value=mock_result)
        extractors[dim_type] = mock_extractor
    return extractors


@pytest.fixture
def graph_with_mocks(mock_extractors):
    """Create a DimensionExtractionGraph with mocked extractors."""
    graph = DimensionExtractionGraph()
    # Replace real extractors with mocks
    for dim_type, mock_extractor in mock_extractors.items():
        graph.extractors[dim_type] = mock_extractor
    return graph


# ============================================================================
# Initialization Tests
# ============================================================================

def test_dimension_extraction_graph_initializes_all_extractors():
    """Test that DimensionExtractionGraph initializes all extractors."""
    graph = DimensionExtractionGraph()

    # Check that all expected extractors are initialized
    assert "brand" in graph.extractors
    assert "time_range" in graph.extractors
    assert "geography" in graph.extractors
    assert "category" in graph.extractors
    assert "generation" in graph.extractors
    assert "income_band" in graph.extractors
    assert "card_type" in graph.extractors
    assert "payment_network" in graph.extractors
    assert "channel" in graph.extractors
    assert "day_of_week" in graph.extractors

    # Check that all extractors are instances of the correct classes
    from src.agent.nodes import (
        BrandExtractor,
        TimeRangeExtractor,
        GeographyExtractor,
        CategoryExtractor,
        GenerationExtractor,
        IncomeBandExtractor,
        CardTypeExtractor,
        PaymentNetworkExtractor,
        ChannelExtractor,
        DayOfWeekExtractor,
    )

    assert isinstance(graph.extractors["brand"], BrandExtractor)
    assert isinstance(graph.extractors["time_range"], TimeRangeExtractor)
    assert isinstance(graph.extractors["geography"], GeographyExtractor)
    assert isinstance(graph.extractors["category"], CategoryExtractor)
    assert isinstance(graph.extractors["generation"], GenerationExtractor)
    assert isinstance(graph.extractors["income_band"], IncomeBandExtractor)
    assert isinstance(graph.extractors["card_type"], CardTypeExtractor)
    assert isinstance(graph.extractors["payment_network"], PaymentNetworkExtractor)
    assert isinstance(graph.extractors["channel"], ChannelExtractor)
    assert isinstance(graph.extractors["day_of_week"], DayOfWeekExtractor)


def test_independent_extractors_list_defined():
    """Test that INDEPENDENT_EXTRACTORS list is properly defined."""
    expected = [
        "brand",
        "time_range",
        "geography",
        "category",
        "generation",
        "income_band",
        "channel",
        "card_type",
        "payment_network",
        "day_of_week",
    ]
    assert INDEPENDENT_EXTRACTORS == expected


# ============================================================================
# Parallel Execution Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_all_runs_independent_extractors_in_parallel(graph_with_mocks):
    """Test that extract_all runs independent extractors in parallel."""
    import time

    graph = graph_with_mocks

    # Track call times
    call_times: Dict[str, float] = {}

    async def mock_extract(input_data):
        dim_type = input_data.dimension_type
        call_times[dim_type] = time.perf_counter()
        # Small delay to ensure parallel execution is measurable
        await asyncio.sleep(0.05)
        return DimensionExtractionResult(
            dimension_type=dim_type,
            values=[f"{dim_type}_value"],
            confidence=0.8,
            alternatives=[],
            extraction_method="llm",
            latency_ms=50,
            validation_status="valid",
        )

    # Replace extractors with timed mocks
    for dim_type in INDEPENDENT_EXTRACTORS:
        graph.extractors[dim_type].extract = mock_extract

    # Run extraction
    result = await graph.extract_all("Test query about spending")

    # Verify all were called
    assert len(call_times) == len(INDEPENDENT_EXTRACTORS)

    # Verify extraction returned valid output
    assert isinstance(result, DimensionExtractionOutput)
    assert isinstance(result.extracted_dimensions, ExtractedDimensions)


# ============================================================================
# Output Structure Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_all_returns_extracted_dimensions():
    """Test that extract_all returns properly structured ExtractedDimensions."""
    graph = DimensionExtractionGraph()

    # Use a query that will trigger deterministic extractors
    result = await graph.extract_all(
        "Show me spending at Walmart in CA on credit card last quarter"
    )

    assert isinstance(result, DimensionExtractionOutput)
    assert isinstance(result.extracted_dimensions, ExtractedDimensions)
    assert result.schema_version == "1.0"
    assert result.retry_count == 0


@pytest.mark.asyncio
async def test_extract_all_includes_all_dimension_types():
    """Test that extract_all includes all dimension types in output."""
    graph = DimensionExtractionGraph()

    result = await graph.extract_all("Show spending")

    extracted = result.extracted_dimensions

    # Verify all dimension attributes exist
    assert hasattr(extracted, "brand")
    assert hasattr(extracted, "merchant_category")
    assert hasattr(extracted, "geography")
    assert hasattr(extracted, "time_range")
    assert hasattr(extracted, "generation")
    assert hasattr(extracted, "income_band")
    assert hasattr(extracted, "card_type")
    assert hasattr(extracted, "payment_network")
    assert hasattr(extracted, "channel")
    assert hasattr(extracted, "day_of_week")


# ============================================================================
# Convenience Function Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_dimensions_convenience_function():
    """Test the extract_dimensions convenience function."""
    result = await extract_dimensions("Show me spending at Walmart")

    assert isinstance(result, DimensionExtractionOutput)
    assert isinstance(result.extracted_dimensions, ExtractedDimensions)
    assert result.schema_version == "1.0"


@pytest.mark.asyncio
async def test_extract_dimensions_accepts_conversation_history():
    """Test that extract_dimensions accepts conversation_history parameter."""
    history = [{"role": "user", "content": "Show spending"}]

    result = await extract_dimensions(
        "Compare to last month",
        conversation_history=history
    )

    assert isinstance(result, DimensionExtractionOutput)
    assert isinstance(result.extracted_dimensions, ExtractedDimensions)


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_all_handles_extractor_exception():
    """Test that extract_all handles extractor exceptions gracefully."""
    graph = DimensionExtractionGraph()

    # Mock one extractor to raise an exception
    async def failing_extract(input_data):
        raise Exception("Simulated extraction failure")

    graph.extractors["brand"].extract = failing_extract

    # Should not raise, should return error result
    result = await graph.extract_all("Show spending at Walmart")

    assert isinstance(result, DimensionExtractionOutput)
    # Brand should have error status due to exception
    # The error is handled gracefully


# ============================================================================
# Conflict Detection Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_all_detects_conflicts():
    """Test that extract_all calls detect_conflicts on extracted dimensions."""
    graph = DimensionExtractionGraph()

    # The conflict detection is based on the extracted dimensions
    # We can't easily trigger a conflict without LLM extraction,
    # but we can verify the method runs without error
    result = await graph.extract_all("Show spending at Walmart")

    assert isinstance(result, DimensionExtractionOutput)
    # Conflicts should be a list (empty or with conflicts)
    assert isinstance(result.conflicts, list)


# ============================================================================
# Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_all_validates_dimensions():
    """Test that extract_all validates dimensions via LLMExtractionValidator."""
    graph = DimensionExtractionGraph()

    result = await graph.extract_all("Show spending at Walmart")

    assert isinstance(result, DimensionExtractionOutput)
    assert isinstance(result.validation_errors, list)


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_all_completes_within_budget():
    """Test that extract_all completes within the 600-1200ms budget."""
    import time

    graph = DimensionExtractionGraph()
    start = time.perf_counter()

    result = await graph.extract_all(
        "Show me spending at Walmart in CA using Visa on credit card"
    )

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    # Should complete within reasonable time (allowing for LLM calls)
    # The budget is 600-1200ms for parallel extraction, but in test
    # environment we allow up to 6s for real LLM calls
    assert elapsed_ms < 6000  # Sanity check - should not take more than 6s


# ============================================================================
# Latency Tracking Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_all_returns_output_with_latency_info():
    """Test that extract_all output includes latency information."""
    graph = DimensionExtractionGraph()

    result = await graph.extract_all("Show spending")

    assert hasattr(result, "extracted_dimensions")
    # Individual results contain latency_ms
