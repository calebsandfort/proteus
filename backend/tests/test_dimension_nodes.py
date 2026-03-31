"""FR-3.2: Dimension Extractor Node Tests.

Tests for the dimension extraction nodes including:
- TimeRangeExtractor (deterministic)
- BrandExtractor (LLM + fuzzy)
- CategoryExtractor (LLM + enum)
- GenerationExtractor (LLM)
- IncomeBandExtractor (LLM)
- CardTypeExtractor (deterministic + lookup)
- PaymentNetworkExtractor (deterministic + lookup)
- ChannelExtractor (deterministic + lookup)
- DayOfWeekExtractor (deterministic)
- GeographyExtractor (deterministic + cached lookups)
"""

import pytest
from datetime import datetime

from src.api.models.dimensions import DimensionExtractionInput, DimensionExtractionResult
from src.agent.nodes import (
    TimeRangeExtractor,
    BrandExtractor,
    CategoryExtractor,
    GenerationExtractor,
    IncomeBandExtractor,
    CardTypeExtractor,
    PaymentNetworkExtractor,
    ChannelExtractor,
    DayOfWeekExtractor,
    GeographyExtractor,
)


# ============================================================================
# Time Range Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_time_range_extractor_parses_last_quarter():
    """Test TimeRangeExtractor parses 'last quarter'."""
    extractor = TimeRangeExtractor()
    input_data = DimensionExtractionInput(
        query="Show me spending for last quarter",
        dimension_type="time_range",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "time_range"
    assert "last_quarter" in result.values
    assert result.extraction_method == "deterministic"
    assert result.validation_status == "valid"
    assert 0 <= result.latency_ms <= 50


@pytest.mark.asyncio
async def test_time_range_extractor_parses_q3_2024():
    """Test TimeRangeExtractor parses 'Q3 2024'."""
    extractor = TimeRangeExtractor()
    input_data = DimensionExtractionInput(
        query="Show Q3 2024 transactions",
        dimension_type="time_range",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "time_range"
    assert "Q3 2024" in result.values or "Q3" in result.values
    assert result.extraction_method == "deterministic"
    assert result.validation_status == "valid"


@pytest.mark.asyncio
async def test_time_range_extractor_parses_ytd():
    """Test TimeRangeExtractor parses 'YTD'."""
    extractor = TimeRangeExtractor()
    input_data = DimensionExtractionInput(
        query="Show year-to-date spending",
        dimension_type="time_range",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "time_range"
    assert "ytd" in result.values or "YTD" in result.values[0].lower()
    assert result.extraction_method == "deterministic"
    assert result.validation_status == "valid"


@pytest.mark.asyncio
async def test_time_range_extractor_parses_last_year():
    """Test TimeRangeExtractor parses 'last year'."""
    extractor = TimeRangeExtractor()
    input_data = DimensionExtractionInput(
        query="Compare to last year",
        dimension_type="time_range",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "time_range"
    assert "last_year" in result.values
    assert result.extraction_method == "deterministic"
    assert result.validation_status == "valid"


@pytest.mark.asyncio
async def test_time_range_extractor_parses_last_30_days():
    """Test TimeRangeExtractor parses 'last 30 days'."""
    extractor = TimeRangeExtractor()
    input_data = DimensionExtractionInput(
        query="Show last 30 days of transactions",
        dimension_type="time_range",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "time_range"
    assert "last_30_days" in result.values
    assert result.extraction_method == "deterministic"
    assert result.validation_status == "valid"


@pytest.mark.asyncio
async def test_time_range_extractor_infers_aggregation_daily():
    """Test TimeRangeExtractor infers daily aggregation for 1-14 days."""
    extractor = TimeRangeExtractor()

    # 7 days -> daily
    days = 7
    aggregation = extractor._infer_aggregation(days)
    assert aggregation == "daily"

    # 14 days -> daily
    days = 14
    aggregation = extractor._infer_aggregation(days)
    assert aggregation == "daily"


@pytest.mark.asyncio
async def test_time_range_extractor_infers_aggregation_weekly():
    """Test TimeRangeExtractor infers weekly aggregation for 15-90 days."""
    extractor = TimeRangeExtractor()

    # 30 days -> weekly
    days = 30
    aggregation = extractor._infer_aggregation(days)
    assert aggregation == "weekly"

    # 90 days -> weekly
    days = 90
    aggregation = extractor._infer_aggregation(days)
    assert aggregation == "weekly"


@pytest.mark.asyncio
async def test_time_range_extractor_infers_aggregation_monthly():
    """Test TimeRangeExtractor infers monthly aggregation for 91-365 days."""
    extractor = TimeRangeExtractor()

    # 180 days -> monthly
    days = 180
    aggregation = extractor._infer_aggregation(days)
    assert aggregation == "monthly"


@pytest.mark.asyncio
async def test_time_range_extractor_invalid_returns_empty():
    """Test TimeRangeExtractor returns empty for unparseable input."""
    extractor = TimeRangeExtractor()
    input_data = DimensionExtractionInput(
        query="Show everything",
        dimension_type="time_range",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "time_range"
    assert result.values == []
    assert result.confidence == 0.0
    assert result.validation_status == "invalid"


# ============================================================================
# Card Type Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_card_type_extractor_parses_credit_card():
    """Test CardTypeExtractor parses 'credit card'."""
    extractor = CardTypeExtractor()
    input_data = DimensionExtractionInput(
        query="Show credit card transactions",
        dimension_type="card_type",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "card_type"
    assert "credit" in result.values
    assert result.extraction_method == "lookup"
    assert result.validation_status == "valid"
    assert 0 <= result.latency_ms <= 400


@pytest.mark.asyncio
async def test_card_type_extractor_parses_debit_card():
    """Test CardTypeExtractor parses 'debit card'."""
    extractor = CardTypeExtractor()
    input_data = DimensionExtractionInput(
        query="Debit card spending",
        dimension_type="card_type",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "card_type"
    assert "debit" in result.values
    assert result.extraction_method == "lookup"
    assert result.validation_status == "valid"


# ============================================================================
# Payment Network Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_payment_network_extractor_parses_visa():
    """Test PaymentNetworkExtractor parses 'visa'."""
    extractor = PaymentNetworkExtractor()
    input_data = DimensionExtractionInput(
        query="Visa transactions only",
        dimension_type="payment_network",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "payment_network"
    assert "visa" in result.values
    assert result.extraction_method == "lookup"
    assert result.validation_status == "valid"
    assert 0 <= result.latency_ms <= 400


@pytest.mark.asyncio
async def test_payment_network_extractor_parses_amex():
    """Test PaymentNetworkExtractor parses 'american express'."""
    extractor = PaymentNetworkExtractor()
    input_data = DimensionExtractionInput(
        query="American Express spending",
        dimension_type="payment_network",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "payment_network"
    assert "amex" in result.values
    assert result.extraction_method == "lookup"
    assert result.validation_status == "valid"


# ============================================================================
# Channel Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_channel_extractor_parses_online():
    """Test ChannelExtractor parses 'online'."""
    extractor = ChannelExtractor()
    input_data = DimensionExtractionInput(
        query="Online purchases",
        dimension_type="channel",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "channel"
    assert "online" in result.values
    assert result.extraction_method == "lookup"
    assert result.validation_status == "valid"
    assert 0 <= result.latency_ms <= 400


@pytest.mark.asyncio
async def test_channel_extractor_parses_in_store():
    """Test ChannelExtractor parses 'in-store'."""
    extractor = ChannelExtractor()
    input_data = DimensionExtractionInput(
        query="In-store transactions",
        dimension_type="channel",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "channel"
    assert "in_store" in result.values
    assert result.extraction_method == "lookup"
    assert result.validation_status == "valid"


# ============================================================================
# Day of Week Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_day_of_week_extractor_parses_single_day():
    """Test DayOfWeekExtractor parses single day."""
    extractor = DayOfWeekExtractor()
    input_data = DimensionExtractionInput(
        query="Show spending on monday",
        dimension_type="day_of_week",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "day_of_week"
    assert "monday" in result.values
    assert result.extraction_method == "deterministic"
    assert result.validation_status == "valid"
    assert 0 <= result.latency_ms <= 200


@pytest.mark.asyncio
async def test_day_of_week_extractor_parses_weekend():
    """Test DayOfWeekExtractor parses 'weekend'."""
    extractor = DayOfWeekExtractor()
    input_data = DimensionExtractionInput(
        query="Weekend spending",
        dimension_type="day_of_week",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "day_of_week"
    assert "saturday" in result.values
    assert "sunday" in result.values
    assert result.extraction_method == "deterministic"
    assert result.validation_status == "valid"


@pytest.mark.asyncio
async def test_day_of_week_extractor_parses_weekday():
    """Test DayOfWeekExtractor parses 'weekday'."""
    extractor = DayOfWeekExtractor()
    input_data = DimensionExtractionInput(
        query="Weekday transactions",
        dimension_type="day_of_week",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "day_of_week"
    assert "monday" in result.values
    assert "tuesday" in result.values
    assert "wednesday" in result.values
    assert "thursday" in result.values
    assert "friday" in result.values
    assert "saturday" not in result.values
    assert "sunday" not in result.values
    assert result.extraction_method == "deterministic"
    assert result.validation_status == "valid"


# ============================================================================
# Brand Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_brand_extractor_deterministic_match():
    """Test BrandExtractor uses deterministic matching for known brands."""
    extractor = BrandExtractor()
    input_data = DimensionExtractionInput(
        query="Spending at Walmart and Target",
        dimension_type="brand",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "brand"
    assert "Walmart" in result.values
    assert "Target" in result.values
    assert result.extraction_method == "lookup"
    assert result.validation_status == "valid"
    assert 0 <= result.latency_ms <= 800


# ============================================================================
# Geography Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_geography_extractor_state_abbreviation():
    """Test GeographyExtractor parses state abbreviations."""
    extractor = GeographyExtractor()
    input_data = DimensionExtractionInput(
        query="Spending in CA and TX",
        dimension_type="geography",
    )
    result = await extractor.extract(input_data)

    assert result.dimension_type == "geography"
    assert "CA" in result.values
    assert "TX" in result.values
    assert result.extraction_method == "lookup"
    assert result.validation_status == "valid"
    assert 0 <= result.latency_ms <= 150


@pytest.mark.asyncio
async def test_geography_extractor_caches_results():
    """Test GeographyExtractor caches lookups for performance."""
    extractor = GeographyExtractor()
    input_data = DimensionExtractionInput(
        query="Spending in California",
        dimension_type="geography",
    )

    # First call
    result1 = await extractor.extract(input_data)
    assert "CA" in result1.values

    # Second call should hit cache
    result2 = await extractor.extract(input_data)
    assert result2.values == result1.values
    assert result2.extraction_method == "lookup"
    # Cache should make second call faster or equal (allow 0ms for both)
    assert result2.latency_ms <= result1.latency_ms + 1


# ============================================================================
# Generation Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_generation_extractor_has_valid_prompt():
    """Test GenerationExtractor has valid prompt template."""
    extractor = GenerationExtractor()

    assert hasattr(extractor, 'PROMPT_TEMPLATE')
    assert "gen_z" in extractor.PROMPT_TEMPLATE
    assert "millennial" in extractor.PROMPT_TEMPLATE
    assert extractor.dimension_type == "generation"


# ============================================================================
# Income Band Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_income_band_extractor_has_valid_prompt():
    """Test IncomeBandExtractor has valid prompt template."""
    extractor = IncomeBandExtractor()

    assert hasattr(extractor, 'PROMPT_TEMPLATE')
    assert "band_1" in extractor.PROMPT_TEMPLATE
    assert "band_6" in extractor.PROMPT_TEMPLATE
    assert extractor.dimension_type == "income_band"


# ============================================================================
# Category Extractor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_category_extractor_has_valid_prompt():
    """Test CategoryExtractor has valid prompt template."""
    extractor = CategoryExtractor()

    assert hasattr(extractor, 'PROMPT_TEMPLATE')
    assert extractor.dimension_type == "merchant_category"
    assert len(extractor.VALID_CATEGORIES) > 0
