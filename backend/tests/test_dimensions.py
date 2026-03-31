"""Tests for FR-3: Dimension Extraction Pipeline Pydantic Models.

This module tests the dimension extraction models:
- Generation and IncomeBand enum-like models
- DimensionExtractionInput and Result
- DimensionValidationResult and ExtractedDimensions
- DimensionConflict and DisambiguationOption
- DimensionExtractionOutput

FR Requirements:
- FR-3.1: Dimension Categories (brand, merchant_category, geography, etc.)
- FR-3.5: Dimension Validation (DimensionValidationResult, ExtractedDimensions)
- FR-3.6: Conflict Resolution (DimensionConflict, DisambiguationOption)
- FR-3.7: Extraction Output Schema (DimensionExtractionOutput)
"""

import pytest
from typing import Dict, Any, List


class TestGenerationModel:
    """FR-3.1: Generation dimension model."""

    def test_generation_model_validates_valid_ids(self) -> None:
        """Generation model accepts valid literal IDs."""
        from src.api.models.dimensions import Generation

        valid_ids = ["gen_z", "millennial", "gen_x", "boomer", "silent"]
        for gen_id in valid_ids:
            gen = Generation(id=gen_id, label="Test", birth_years="1997-2024")
            assert gen.id == gen_id

    def test_generation_model_rejects_invalid_ids(self) -> None:
        """Generation model rejects IDs not in the literal union."""
        from src.api.models.dimensions import Generation
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Generation(id="invalid_gen", label="Test", birth_years="1997-2024")

    def test_generation_model_with_aliases(self) -> None:
        """Generation model supports aliases list."""
        from src.api.models.dimensions import Generation

        gen = Generation(
            id="millennial",
            label="Millennial",
            birth_years="1981-1996",
            aliases=["gen_y", "echo_boomers"]
        )
        assert gen.aliases == ["gen_y", "echo_boomers"]


class TestIncomeBandModel:
    """FR-3.1: Income band dimension model."""

    def test_income_band_model_validates_valid_ids(self) -> None:
        """IncomeBand model accepts valid literal IDs."""
        from src.api.models.dimensions import IncomeBand

        valid_ids = ["band_1", "band_2", "band_3", "band_4", "band_5", "band_6"]
        for band_id in valid_ids:
            band = IncomeBand(id=band_id, label="Test", range_usd="<$25,000")
            assert band.id == band_id

    def test_income_band_model_rejects_invalid_ids(self) -> None:
        """IncomeBand model rejects IDs not in the literal union."""
        from src.api.models.dimensions import IncomeBand
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            IncomeBand(id="band_99", label="Test", range_usd="<$25,000")

    def test_income_band_model_with_aliases(self) -> None:
        """IncomeBand model supports aliases list."""
        from src.api.models.dimensions import IncomeBand

        band = IncomeBand(
            id="band_3",
            label="Middle Income",
            range_usd="$50,000-$74,999",
            aliases=["middle_class", "middle_income"]
        )
        assert band.aliases == ["middle_class", "middle_income"]


class TestDimensionExtractionInput:
    """FR-3.2: Dimension Extraction Input model."""

    def test_dimension_extraction_input_required_fields(self) -> None:
        """DimensionExtractionInput requires query and dimension_type."""
        from src.api.models.dimensions import DimensionExtractionInput

        inp = DimensionExtractionInput(
            query="Show me Gen Z spending on restaurants",
            dimension_type="generation"
        )
        assert inp.query == "Show me Gen Z spending on restaurants"
        assert inp.dimension_type == "generation"

    def test_dimension_extraction_input_optional_fields(self) -> None:
        """DimensionExtractionInput has optional conversation_history and max_tokens."""
        from src.api.models.dimensions import DimensionExtractionInput

        inp = DimensionExtractionInput(
            query="Show me spending",
            dimension_type="brand",
            conversation_history=[{"role": "user", "content": "Hello"}],
            max_tokens=1000
        )
        assert len(inp.conversation_history) == 1
        assert inp.max_tokens == 1000

    def test_dimension_extraction_input_defaults(self) -> None:
        """DimensionExtractionInput has sensible defaults."""
        from src.api.models.dimensions import DimensionExtractionInput

        inp = DimensionExtractionInput(
            query="Test query",
            dimension_type="brand"
        )
        assert inp.conversation_history == []
        assert inp.max_tokens == 2000


class TestDimensionExtractionResult:
    """FR-3.2: Dimension Extraction Result model."""

    def test_dimension_extraction_result_fields(self) -> None:
        """DimensionExtractionResult has all required fields."""
        from src.api.models.dimensions import DimensionExtractionResult

        result = DimensionExtractionResult(
            dimension_type="brand",
            values=["nike", "adidas"],
            confidence=0.95,
            alternatives=[{"brand": "puma", "confidence": 0.7}],
            extraction_method="llm",
            latency_ms=150,
            validation_status="valid"
        )
        assert result.dimension_type == "brand"
        assert result.values == ["nike", "adidas"]
        assert result.confidence == 0.95
        assert result.alternatives == [{"brand": "puma", "confidence": 0.7}]
        assert result.extraction_method == "llm"
        assert result.latency_ms == 150
        assert result.validation_status == "valid"

    def test_dimension_extraction_result_confidence_bounds(self) -> None:
        """DimensionExtractionResult confidence must be 0-1."""
        from src.api.models.dimensions import DimensionExtractionResult
        from pydantic import ValidationError

        # Valid confidence
        result = DimensionExtractionResult(
            dimension_type="brand",
            values=["test"],
            confidence=0.0,
            extraction_method="deterministic",
            latency_ms=10,
            validation_status="valid"
        )
        assert result.confidence == 0.0

        # Invalid confidence > 1
        with pytest.raises(ValidationError):
            DimensionExtractionResult(
                dimension_type="brand",
                values=["test"],
                confidence=1.5,
                extraction_method="deterministic",
                latency_ms=10,
                validation_status="valid"
            )


class TestDimensionValidationResult:
    """FR-3.5: Dimension Validation Result model."""

    def test_dimension_validation_result_valid(self) -> None:
        """DimensionValidationResult for valid dimension."""
        from src.api.models.dimensions import DimensionValidationResult

        result = DimensionValidationResult(
            is_valid=True,
            dimension="brand",
            value="nike",
            canonical_value="Nike",
            suggestions=[]
        )
        assert result.is_valid is True
        assert result.canonical_value == "Nike"

    def test_dimension_validation_result_with_suggestions(self) -> None:
        """DimensionValidationResult provides suggestions for invalid values."""
        from src.api.models.dimensions import DimensionValidationResult

        result = DimensionValidationResult(
            is_valid=False,
            dimension="brand",
            value="nkie",
            canonical_value=None,
            suggestions=["nike", "nike air", "nike.com"]
        )
        assert result.is_valid is False
        assert result.suggestions == ["nike", "nike air", "nike.com"]


class TestExtractedDimensions:
    """FR-3.5: Extracted Dimensions model."""

    def test_extracted_dimensions_defaults(self) -> None:
        """ExtractedDimensions has sensible defaults for all dimension fields."""
        from src.api.models.dimensions import ExtractedDimensions

        extracted = ExtractedDimensions()
        assert extracted.brand == []
        assert extracted.merchant_category == []
        assert extracted.geography == []
        assert extracted.time_range is None
        assert extracted.generation == []
        assert extracted.income_band == []
        assert extracted.card_type == []
        assert extracted.payment_network == []
        assert extracted.channel == []
        assert extracted.day_of_week == []
        assert extracted.aggregation_level is None

    def test_extracted_dimensions_with_values(self) -> None:
        """ExtractedDimensions can be populated with dimension values."""
        from src.api.models.dimensions import ExtractedDimensions

        extracted = ExtractedDimensions(
            brand=["nike", "adidas"],
            merchant_category=["athletic footwear", "sports apparel"],
            geography=["northeast", "southeast"],
            generation=["gen_z", "millennial"],
            income_band=["band_3", "band_4"],
            card_type=["credit", "debit"],
            payment_network=["visa", "mastercard"],
            channel=["online", "in-store"],
            day_of_week=["saturday", "sunday"],
            aggregation_level="brand"
        )
        assert len(extracted.brand) == 2
        assert len(extracted.generation) == 2
        assert extracted.aggregation_level == "brand"

    def test_extracted_dimensions_with_time_range(self) -> None:
        """ExtractedDimensions supports time_range as nested dict."""
        from src.api.models.dimensions import ExtractedDimensions

        extracted = ExtractedDimensions(
            time_range={
                "start": "2024-01-01",
                "end": "2024-12-31",
                "granularity": "monthly"
            }
        )
        assert extracted.time_range is not None
        assert extracted.time_range["granularity"] == "monthly"


class TestDisambiguationOption:
    """FR-3.6: Disambiguation Option model."""

    def test_disambiguation_option_structure(self) -> None:
        """DisambiguationOption has all required fields."""
        from src.api.models.dimensions import DisambiguationOption

        option = DisambiguationOption(
            id="opt_1",
            label="Use Gen Z only",
            resolved_dimensions={"generation": ["gen_z"]},
            reasoning="User specifically asked for Gen Z"
        )
        assert option.id == "opt_1"
        assert option.label == "Use Gen Z only"
        assert option.resolved_dimensions == {"generation": ["gen_z"]}
        assert "Gen Z" in option.reasoning


class TestDimensionConflict:
    """FR-3.6: Dimension Conflict model."""

    def test_dimension_conflict_structure(self) -> None:
        """DimensionConflict has all required fields."""
        from src.api.models.dimensions import DimensionConflict, DisambiguationOption

        conflict = DimensionConflict(
            dimension="time_range",
            conflicting_values=["2024-01-01 to 2024-06-30", "2024-03-01 to 2024-09-30"],
            conflict_type="temporal_overlap",
            options=[
                DisambiguationOption(
                    id="opt_1",
                    label="Use first range",
                    resolved_dimensions={"time_range": ["2024-01-01 to 2024-06-30"]},
                    reasoning="First range was specified first"
                ),
                DisambiguationOption(
                    id="opt_2",
                    label="Use combined range",
                    resolved_dimensions={"time_range": ["2024-01-01 to 2024-09-30"]},
                    reasoning="Combined range covers both"
                )
            ]
        )
        assert conflict.dimension == "time_range"
        assert conflict.conflict_type == "temporal_overlap"
        assert len(conflict.options) == 2

    def test_dimension_conflict_types(self) -> None:
        """DimensionConflict supports different conflict types."""
        from src.api.models.dimensions import DimensionConflict, DisambiguationOption

        # Geographic overlap conflict
        conflict = DimensionConflict(
            dimension="geography",
            conflicting_values=["northeast", "new england"],
            conflict_type="geographic_overlap",
            options=[
                DisambiguationOption(
                    id="geo_opt",
                    label="Use broader region",
                    resolved_dimensions={"geography": ["northeast"]},
                    reasoning="New England is part of Northeast"
                )
            ]
        )
        assert conflict.conflict_type == "geographic_overlap"


class TestDimensionExtractionOutput:
    """FR-3.7: Dimension Extraction Output model."""

    def test_dimension_extraction_output_schema(self) -> None:
        """DimensionExtractionOutput has all required fields."""
        from src.api.models.dimensions import (
            DimensionExtractionOutput,
            ExtractedDimensions,
            DimensionConflict
        )

        output = DimensionExtractionOutput(
            extracted_dimensions=ExtractedDimensions(
                brand=["nike"],
                generation=["millennial"]
            ),
            conflicts=[],
            validation_errors=[],
            retry_count=0,
            schema_version="1.0"
        )
        assert output.schema_version == "1.0"
        assert output.retry_count == 0
        assert len(output.extracted_dimensions.brand) == 1

    def test_dimension_extraction_output_with_conflicts(self) -> None:
        """DimensionExtractionOutput includes conflicts when present."""
        from src.api.models.dimensions import (
            DimensionExtractionOutput,
            ExtractedDimensions,
            DimensionConflict,
            DisambiguationOption
        )

        conflict = DimensionConflict(
            dimension="time_range",
            conflicting_values=["Q1", "Q2"],
            conflict_type="temporal_overlap",
            options=[
                DisambiguationOption(
                    id="opt_1",
                    label="Q1",
                    resolved_dimensions={"time_range": ["Q1"]},
                    reasoning="First specified"
                )
            ]
        )

        output = DimensionExtractionOutput(
            extracted_dimensions=ExtractedDimensions(),
            conflicts=[conflict],
            validation_errors=[],
            retry_count=1,
            schema_version="1.0"
        )
        assert len(output.conflicts) == 1
        assert output.retry_count == 1

    def test_dimension_extraction_output_with_validation_errors(self) -> None:
        """DimensionExtractionOutput includes validation_errors when present."""
        from src.api.models.dimensions import (
            DimensionExtractionOutput,
            ExtractedDimensions
        )

        output = DimensionExtractionOutput(
            extracted_dimensions=ExtractedDimensions(),
            conflicts=[],
            validation_errors=["Invalid brand: xyz123", "Unknown geography: foo"],
            retry_count=0,
            schema_version="1.0"
        )
        assert len(output.validation_errors) == 2

    def test_dimension_extraction_output_defaults(self) -> None:
        """DimensionExtractionOutput has sensible defaults."""
        from src.api.models.dimensions import DimensionExtractionOutput, ExtractedDimensions

        output = DimensionExtractionOutput(
            extracted_dimensions=ExtractedDimensions()
        )
        assert output.conflicts == []
        assert output.validation_errors == []
        assert output.retry_count == 0
        assert output.schema_version == "1.0"


class TestDimensionConstants:
    """FR-3.1: Pre-defined dimension constants."""

    def test_generations_constant_exists(self) -> None:
        """GENERATIONS dict is available."""
        from src.api.models.dimensions import GENERATIONS

        assert isinstance(GENERATIONS, dict)
        assert len(GENERATIONS) > 0

    def test_income_bands_constant_exists(self) -> None:
        """INCOME_BANDS dict is available."""
        from src.api.models.dimensions import INCOME_BANDS

        assert isinstance(INCOME_BANDS, dict)
        assert len(INCOME_BANDS) > 0

    def test_generations_has_all_values(self) -> None:
        """GENERATIONS contains all 5 generation IDs."""
        from src.api.models.dimensions import GENERATIONS

        expected_ids = {"gen_z", "millennial", "gen_x", "boomer", "silent"}
        actual_ids = set(GENERATIONS.keys())
        assert expected_ids == actual_ids

    def test_income_bands_has_all_values(self) -> None:
        """INCOME_BANDS contains all 6 income band IDs."""
        from src.api.models.dimensions import INCOME_BANDS

        expected_ids = {"band_1", "band_2", "band_3", "band_4", "band_5", "band_6"}
        actual_ids = set(INCOME_BANDS.keys())
        assert expected_ids == actual_ids


class TestStubsModule:
    """Tests for the IU-3 stubs module."""

    def test_stubs_module_imports(self) -> None:
        """stubs module can be imported."""
        from src.api import stubs
        assert stubs is not None

    def test_dimension_value_class_exists(self) -> None:
        """DimensionValue class exists in stubs."""
        from src.api.stubs import DimensionValue

        dv = DimensionValue(id="test_1", canonical_name="Test Value")
        assert dv.id == "test_1"
        assert dv.canonical_name == "Test Value"

    def test_dimension_value_with_aliases(self) -> None:
        """DimensionValue supports aliases."""
        from src.api.stubs import DimensionValue

        dv = DimensionValue(
            id="nike",
            canonical_name="Nike",
            aliases=["NIKE", "nike inc", "Nike Inc."]
        )
        assert len(dv.aliases) == 3

    def test_get_dimension_values_returns_list(self) -> None:
        """get_dimension_values returns a list."""
        import asyncio
        from src.api.stubs import get_dimension_values

        result = asyncio.run(get_dimension_values("brand"))
        assert isinstance(result, list)

    def test_validate_dimension_value_returns_dict(self) -> None:
        """validate_dimension_value returns a dict."""
        import asyncio
        from src.api.stubs import validate_dimension_value

        result = asyncio.run(validate_dimension_value("brand", "nike"))
        assert isinstance(result, dict)
        assert "valid" in result
        assert "canonical" in result
        assert "suggestions" in result
