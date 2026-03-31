"""FR-3.5 & FR-3.6: Tests for Dimension Validation and Conflict Resolution.

Tests for:
- LLMExtractionValidator: Validates LLM JSON output against schema
- detect_conflicts(): Detects temporal and spatial conflicts in extracted dimensions
"""

import pytest

from src.api.models.dimensions import (
    DisambiguationOption,
    DimensionConflict,
    DimensionExtractionOutput,
    ExtractedDimensions,
)
from src.agent.validation import (
    LLMExtractionValidator,
    detect_conflicts,
    _generate_temporal_options,
)


class TestLLMExtractionValidator:
    """Tests for LLMExtractionValidator class."""

    def test_llm_extraction_validator_validates_correct_json(self):
        """Test that valid JSON matching schema is accepted."""
        validator = LLMExtractionValidator()

        valid_json = """{
            "extracted_dimensions": {
                "brand": ["Nike"],
                "merchant_category": [],
                "geography": [],
                "generation": [],
                "income_band": [],
                "card_type": [],
                "payment_network": [],
                "channel": [],
                "day_of_week": [],
                "time_range": null,
                "aggregation_level": null
            },
            "conflicts": [],
            "validation_errors": [],
            "retry_count": 0,
            "schema_version": "1.0"
        }"""

        is_valid, output, error = validator.validate(valid_json)

        assert is_valid is True
        assert output is not None
        assert error is None
        assert output.schema_version == "1.0"
        assert output.extracted_dimensions.brand == ["Nike"]

    def test_llm_extraction_validator_rejects_invalid_json(self):
        """Test that invalid JSON is rejected."""
        validator = LLMExtractionValidator()

        invalid_json = "{ this is not valid json }"

        is_valid, output, error = validator.validate(invalid_json)

        assert is_valid is False
        assert output is None
        assert error is not None
        assert "Invalid JSON" in error

    def test_llm_extraction_validator_rejects_schema_mismatch(self):
        """Test that JSON not matching schema is rejected."""
        validator = LLMExtractionValidator()

        # Missing required fields
        invalid_schema_json = '{"schema_version": "1.0"}'

        is_valid, output, error = validator.validate(invalid_schema_json)

        assert is_valid is False
        assert output is None
        assert error is not None
        assert "Schema validation error" in error

    def test_llm_extraction_validator_rejects_wrong_schema_version(self):
        """Test that wrong schema version is rejected."""
        validator = LLMExtractionValidator()

        wrong_version_json = """{
            "extracted_dimensions": {
                "brand": [],
                "merchant_category": [],
                "geography": [],
                "generation": [],
                "income_band": [],
                "card_type": [],
                "payment_network": [],
                "channel": [],
                "day_of_week": [],
                "time_range": null,
                "aggregation_level": null
            },
            "conflicts": [],
            "validation_errors": [],
            "retry_count": 0,
            "schema_version": "99.9"
        }"""

        is_valid, output, error = validator.validate(wrong_version_json)

        assert is_valid is False
        assert output is None
        assert error is not None
        assert "Schema version mismatch" in error


class TestValidateDimensions:
    """Tests for validate_dimensions method."""

    def test_validate_dimensions_valid_generation(self):
        """Test validation passes for valid generation values."""
        validator = LLMExtractionValidator()

        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=["gen_z", "millennial"],
            income_band=[],
            card_type=[],
            payment_network=[],
            channel=[],
            day_of_week=[],
        )

        errors = validator.validate_dimensions(dimensions)

        assert errors == []

    def test_validate_dimensions_invalid_generation(self):
        """Test validation fails for invalid generation values."""
        validator = LLMExtractionValidator()

        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=["gen_z", "invalid_gen"],
            income_band=[],
            card_type=[],
            payment_network=[],
            channel=[],
            day_of_week=[],
        )

        errors = validator.validate_dimensions(dimensions)

        assert len(errors) == 1
        assert "Invalid generation" in errors[0]

    def test_validate_dimensions_valid_income_band(self):
        """Test validation passes for valid income_band values."""
        validator = LLMExtractionValidator()

        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=[],
            income_band=["band_1", "band_5"],
            card_type=[],
            payment_network=[],
            channel=[],
            day_of_week=[],
        )

        errors = validator.validate_dimensions(dimensions)

        assert errors == []

    def test_validate_dimensions_invalid_income_band(self):
        """Test validation fails for invalid income_band values."""
        validator = LLMExtractionValidator()

        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=[],
            income_band=["band_1", "invalid_band"],
            card_type=[],
            payment_network=[],
            channel=[],
            day_of_week=[],
        )

        errors = validator.validate_dimensions(dimensions)

        assert len(errors) == 1
        assert "Invalid income_band" in errors[0]

    def test_validate_dimensions_valid_card_type(self):
        """Test validation passes for valid card_type values."""
        validator = LLMExtractionValidator()

        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=[],
            income_band=[],
            card_type=["credit", "debit"],
            payment_network=[],
            channel=[],
            day_of_week=[],
        )

        errors = validator.validate_dimensions(dimensions)

        assert errors == []

    def test_validate_dimensions_invalid_card_type(self):
        """Test validation fails for invalid card_type values."""
        validator = LLMExtractionValidator()

        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=[],
            income_band=[],
            card_type=["invalid_card"],
            payment_network=[],
            channel=[],
            day_of_week=[],
        )

        errors = validator.validate_dimensions(dimensions)

        assert len(errors) == 1
        assert "Invalid card_type" in errors[0]


class TestDetectConflicts:
    """Tests for detect_conflicts function."""

    def test_detect_conflicts_no_conflict_when_empty(self):
        """Test no conflicts detected when dimensions are empty."""
        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=[],
            income_band=[],
            card_type=[],
            payment_network=[],
            channel=[],
            day_of_week=[],
        )

        conflicts = detect_conflicts(dimensions)

        assert conflicts == []

    def test_detect_conflicts_no_conflict_single_period(self):
        """Test no conflicts detected when only one time period."""
        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=[],
            income_band=[],
            card_type=[],
            payment_network=[],
            channel=[],
            day_of_week=[],
            time_range={"periods": ["last month"]},
        )

        conflicts = detect_conflicts(dimensions)

        assert conflicts == []

    def test_detect_conflicts_detects_temporal_conflict(self):
        """Test temporal conflict detected with multiple periods."""
        dimensions = ExtractedDimensions(
            brand=[],
            merchant_category=[],
            geography=[],
            generation=[],
            income_band=[],
            card_type=[],
            payment_network=[],
            channel=[],
            day_of_week=[],
            time_range={"periods": ["last month", "last year"]},
        )

        conflicts = detect_conflicts(dimensions)

        assert len(conflicts) == 1
        assert conflicts[0].dimension == "time_range"
        assert conflicts[0].conflict_type == "temporal_overlap"
        assert "last month" in conflicts[0].conflicting_values
        assert "last year" in conflicts[0].conflicting_values
        assert len(conflicts[0].options) >= 2
        assert len(conflicts[0].options) <= 3


class TestGenerateTemporalOptions:
    """Tests for _generate_temporal_options function."""

    def test_generate_temporal_options_returns_2_to_3_options(self):
        """Test that 2-3 disambiguation options are returned."""
        periods = ["last month", "last year"]

        options = _generate_temporal_options(periods)

        assert len(options) >= 2
        assert len(options) <= 3

    def test_generate_temporal_options_empty_for_single_period(self):
        """Test no options for single period."""
        periods = ["last month"]

        options = _generate_temporal_options(periods)

        assert options == []

    def test_generate_temporal_options_includes_use_first_option(self):
        """Test first option uses first period."""
        periods = ["last month", "last year"]

        options = _generate_temporal_options(periods)

        assert any("use_first" in opt.id for opt in options)
        assert any("last month" in opt.label for opt in options)

    def test_generate_temporal_options_includes_most_recent_option(self):
        """Test includes most recent period option."""
        periods = ["last month", "last year"]

        options = _generate_temporal_options(periods)

        assert any("use_most_recent" in opt.id for opt in options)
        assert any("last year" in opt.label for opt in options)

    def test_generate_temporal_options_includes_combine_option(self):
        """Test includes combine option for two periods."""
        periods = ["last month", "last year"]

        options = _generate_temporal_options(periods)

        assert any("combine" in opt.id for opt in options)
        assert any("last month to last year" in opt.label for opt in options)
