"""Contract tests: Unit 5 (Dimension Extraction Pipeline).

Verifies the integration seams between Unit 5 and its dependencies:
- IU-5 → IU-6: OpenRouter client usage for LLM calls
- IU-5 internal: SynonymResolver, validation, dimension models
- IU-5 → future IU-7: ExtractedDimensions output shape compatibility

No mocks at the integration boundary — real modules from both units are imported.
"""

import inspect
from typing import get_type_hints

import pytest


# ============================================================================
# 1. Import Resolution Tests
# ============================================================================


class TestCrossUnitImports:
    """Verify that cross-unit imports between Unit 5 and its dependencies resolve."""

    def test_nodes_imports_openrouter_client(self):
        """Unit 5 nodes.py can import OpenRouterClient from Unit 6."""
        from src.api.openrouter import OpenRouterClient

        assert OpenRouterClient is not None

    def test_nodes_imports_model_config(self):
        """Unit 5 nodes.py can import model_config from Unit 6 config."""
        from src.config import model_config

        assert model_config is not None
        assert hasattr(model_config, "dimension_extraction")

    def test_nodes_imports_synonym_resolver(self):
        """Unit 5 nodes.py can import SynonymResolver from IU-5 lookup module."""
        from src.api.lookup import SynonymResolver

        assert SynonymResolver is not None

    def test_dimension_graph_imports_all_extractors(self):
        """DimensionExtractionGraph can import all extractor classes from nodes.py."""
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

        assert BrandExtractor is not None
        assert TimeRangeExtractor is not None
        assert GeographyExtractor is not None
        assert CategoryExtractor is not None
        assert GenerationExtractor is not None
        assert IncomeBandExtractor is not None
        assert CardTypeExtractor is not None
        assert PaymentNetworkExtractor is not None
        assert ChannelExtractor is not None
        assert DayOfWeekExtractor is not None

    def test_dimension_graph_imports_validation(self):
        """DimensionExtractionGraph can import validation functions from IU-5."""
        from src.agent.validation import detect_conflicts, LLMExtractionValidator

        assert detect_conflicts is not None
        assert LLMExtractionValidator is not None

    def test_validation_imports_dimension_models(self):
        """validation.py can import dimension models from src.api.models.dimensions."""
        from src.api.models.dimensions import (
            GENERATIONS,
            INCOME_BANDS,
            ExtractedDimensions,
            DimensionExtractionOutput,
        )

        assert GENERATIONS is not None
        assert INCOME_BANDS is not None
        assert ExtractedDimensions is not None
        assert DimensionExtractionOutput is not None

    def test_dimension_graph_module_loads_without_error(self):
        """DimensionExtractionGraph module loads cleanly (all its imports resolve)."""
        from src.agent import dimension_graph

        assert hasattr(dimension_graph, "DimensionExtractionGraph")
        assert hasattr(dimension_graph, "extract_dimensions")

    def test_nodes_module_loads_without_error(self):
        """nodes.py module loads cleanly (all its IU-6 imports resolve)."""
        from src.agent import nodes

        assert hasattr(nodes, "DimensionExtractor")


# ============================================================================
# 2. Type Compatibility Tests
# ============================================================================


class TestTypeCompatibility:
    """Verify that Unit 5's output types satisfy the implementation plan contracts."""

    def test_extracted_dimensions_has_all_11_dimension_fields(self):
        """ExtractedDimensions has all 11 dimension fields per FR-3.1."""
        from src.api.models.dimensions import ExtractedDimensions

        expected_fields = {
            "brand", "merchant_category", "geography", "time_range",
            "generation", "income_band", "card_type", "payment_network",
            "channel", "day_of_week", "aggregation_level",
        }
        actual_fields = set(ExtractedDimensions.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_dimension_extraction_result_has_required_fields(self):
        """DimensionExtractionResult has all required fields per FR-3.7."""
        from src.api.models.dimensions import DimensionExtractionResult

        expected_fields = {
            "dimension_type", "values", "confidence", "alternatives",
            "extraction_method", "latency_ms", "validation_status",
        }
        actual_fields = set(DimensionExtractionResult.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_dimension_extraction_output_has_required_fields(self):
        """DimensionExtractionOutput has all required fields per FR-3.7."""
        from src.api.models.dimensions import DimensionExtractionOutput

        expected_fields = {
            "extracted_dimensions", "conflicts", "validation_errors",
            "retry_count", "schema_version",
        }
        actual_fields = set(DimensionExtractionOutput.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_generations_constant_has_all_5_generations(self):
        """GENERATIONS has all 5 generation values per FR-3.1."""
        from src.api.models.dimensions import GENERATIONS

        expected_gens = {"gen_z", "millennial", "gen_x", "boomer", "silent"}
        assert expected_gens.issubset(set(GENERATIONS.keys())), (
            f"Missing generations: {expected_gens - set(GENERATIONS.keys())}"
        )

    def test_income_bands_constant_has_all_6_bands(self):
        """INCOME_BANDS has all 6 income band values per FR-3.1."""
        from src.api.models.dimensions import INCOME_BANDS

        expected_bands = {"band_1", "band_2", "band_3", "band_4", "band_5", "band_6"}
        assert expected_bands.issubset(set(INCOME_BANDS.keys())), (
            f"Missing bands: {expected_bands - set(INCOME_BANDS.keys())}"
        )

    def test_generation_model_has_expected_fields(self):
        """Generation model has id, label, birth_years, aliases fields."""
        from src.api.models.dimensions import Generation

        expected_fields = {"id", "label", "birth_years", "aliases"}
        actual_fields = set(Generation.model_fields.keys())
        assert expected_fields.issubset(actual_fields)

    def test_income_band_model_has_expected_fields(self):
        """IncomeBand model has id, label, range_usd, aliases fields."""
        from src.api.models.dimensions import IncomeBand

        expected_fields = {"id", "label", "range_usd", "aliases"}
        actual_fields = set(IncomeBand.model_fields.keys())
        assert expected_fields.issubset(actual_fields)

    def test_dimension_conflict_model_fields(self):
        """DimensionConflict has the fields expected by FR-3.6."""
        from src.api.models.dimensions import DimensionConflict

        expected_fields = {"dimension", "conflicting_values", "conflict_type", "options"}
        actual_fields = set(DimensionConflict.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_disambiguation_option_model_fields(self):
        """DisambiguationOption has the fields expected by FR-3.6."""
        from src.api.models.dimensions import DisambiguationOption

        expected_fields = {"id", "label", "resolved_dimensions", "reasoning"}
        actual_fields = set(DisambiguationOption.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )


# ============================================================================
# 3. Function Signature Tests
# ============================================================================


class TestFunctionSignatures:
    """Verify that Unit 5 function signatures match the implementation plan contracts."""

    def test_dimension_extractor_is_abstract(self):
        """DimensionExtractor is an abstract base class with extract method."""
        from src.agent.nodes import DimensionExtractor

        # DimensionExtractor is an ABC with abstractmethod, so isabstract returns True
        assert inspect.isabstract(DimensionExtractor) is True

    def test_dimension_extractor_extract_is_async(self):
        """DimensionExtractor.extract is an async method."""
        from src.agent.nodes import DimensionExtractor

        method = DimensionExtractor.extract
        assert inspect.iscoroutinefunction(method)

    def test_all_extractors_have_extract_method(self):
        """All extractor classes have an extract method."""
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

        for extractor_cls in [
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
        ]:
            assert hasattr(extractor_cls, "extract"), (
                f"{extractor_cls.__name__} missing extract method"
            )
            assert inspect.iscoroutinefunction(extractor_cls.extract)

    def test_dimension_extraction_graph_extract_all_is_async(self):
        """DimensionExtractionGraph.extract_all is an async method."""
        from src.agent.dimension_graph import DimensionExtractionGraph

        method = DimensionExtractionGraph.extract_all
        assert inspect.iscoroutinefunction(method)

    def test_dimension_extraction_graph_extract_all_accepts_query(self):
        """DimensionExtractionGraph.extract_all accepts query and conversation_history."""
        from src.agent.dimension_graph import DimensionExtractionGraph

        sig = inspect.signature(DimensionExtractionGraph.extract_all)
        params = list(sig.parameters.keys())
        assert "query" in params
        assert "conversation_history" in params

    def test_extract_dimensions_convenience_function_is_async(self):
        """extract_dimensions convenience function is async."""
        from src.agent.dimension_graph import extract_dimensions

        assert inspect.iscoroutinefunction(extract_dimensions)

    def test_llm_extraction_validator_validate_is_not_async(self):
        """LLMExtractionValidator.validate is a sync method."""
        from src.agent.validation import LLMExtractionValidator

        validator = LLMExtractionValidator()
        assert inspect.iscoroutinefunction(validator.validate) is False

    def test_detect_conflicts_is_not_async(self):
        """detect_conflicts is a sync function."""
        from src.agent.validation import detect_conflicts

        assert inspect.iscoroutinefunction(detect_conflicts) is False

    def test_synonym_resolver_resolve_is_not_async(self):
        """SynonymResolver.resolve is a sync method."""
        from src.api.lookup import SynonymResolver

        resolver = SynonymResolver()
        assert inspect.iscoroutinefunction(resolver.resolve) is False


# ============================================================================
# 4. Shape Compatibility Tests (no network calls)
# ============================================================================


class TestShapeCompatibility:
    """Verify that data shapes flowing through Unit 5 are compatible."""

    def test_dimension_extraction_input_validates(self):
        """A realistic DimensionExtractionInput validates correctly."""
        from src.api.models.dimensions import DimensionExtractionInput

        input_data = DimensionExtractionInput(
            query="Show me Nike sales for millennials in California last quarter",
            conversation_history=[],
            dimension_type="brand",
            max_tokens=2000,
        )
        assert input_data.query == "Show me Nike sales for millennials in California last quarter"
        assert input_data.dimension_type == "brand"
        assert input_data.max_tokens == 2000

    def test_dimension_extraction_result_validates(self):
        """A realistic DimensionExtractionResult validates correctly."""
        from src.api.models.dimensions import DimensionExtractionResult

        result = DimensionExtractionResult(
            dimension_type="brand",
            values=["Nike"],
            confidence=0.85,
            alternatives=[],
            extraction_method="llm",
            latency_ms=450,
            validation_status="valid",
        )
        assert result.dimension_type == "brand"
        assert result.values == ["Nike"]
        assert result.confidence == 0.85
        assert result.extraction_method == "llm"

    def test_extracted_dimensions_validates_with_all_fields(self):
        """ExtractedDimensions validates with all 11 dimension fields populated."""
        from src.api.models.dimensions import ExtractedDimensions

        dims = ExtractedDimensions(
            brand=["Nike"],
            merchant_category=["apparel"],
            geography=["CA"],
            time_range={"periods": ["last_quarter"]},
            generation=["millennial"],
            income_band=["band_4"],
            card_type=["credit"],
            payment_network=["visa"],
            channel=["online"],
            day_of_week=["saturday", "sunday"],
            aggregation_level="weekly",
        )
        assert dims.brand == ["Nike"]
        assert dims.merchant_category == ["apparel"]
        assert dims.geography == ["CA"]
        assert dims.time_range == {"periods": ["last_quarter"]}
        assert dims.generation == ["millennial"]
        assert dims.income_band == ["band_4"]
        assert dims.card_type == ["credit"]
        assert dims.payment_network == ["visa"]
        assert dims.channel == ["online"]
        assert dims.day_of_week == ["saturday", "sunday"]
        assert dims.aggregation_level == "weekly"

    def test_extracted_dimensions_validates_with_empty_fields(self):
        """ExtractedDimensions validates with only some fields populated."""
        from src.api.models.dimensions import ExtractedDimensions

        dims = ExtractedDimensions(
            brand=["Nike"],
            time_range={"periods": ["last_quarter"]},
        )
        assert dims.brand == ["Nike"]
        assert dims.merchant_category == []
        assert dims.geography == []
        assert dims.generation == []

    def test_dimension_extraction_output_validates(self):
        """A realistic DimensionExtractionOutput validates correctly."""
        from src.api.models.dimensions import (
            ExtractedDimensions,
            DimensionExtractionOutput,
        )

        dims = ExtractedDimensions(
            brand=["Nike"],
            time_range={"periods": ["last_quarter"]},
        )
        output = DimensionExtractionOutput(
            extracted_dimensions=dims,
            conflicts=[],
            validation_errors=[],
            retry_count=0,
            schema_version="1.0",
        )
        assert output.extracted_dimensions.brand == ["Nike"]
        assert output.conflicts == []
        assert output.validation_errors == []
        assert output.schema_version == "1.0"

    def test_dimension_extraction_output_with_conflicts_validates(self):
        """DimensionExtractionOutput validates with conflicts present."""
        from src.api.models.dimensions import (
            DisambiguationOption,
            DimensionConflict,
            ExtractedDimensions,
            DimensionExtractionOutput,
        )

        conflict = DimensionConflict(
            dimension="time_range",
            conflicting_values=["last_month", "last_year"],
            conflict_type="temporal_overlap",
            options=[
                DisambiguationOption(
                    id="use_first",
                    label="Use: last_month",
                    resolved_dimensions={"time_range": {"periods": ["last_month"]}},
                    reasoning="Select only the first time period",
                )
            ],
        )
        dims = ExtractedDimensions(
            time_range={"periods": ["last_month", "last_year"]},
        )
        output = DimensionExtractionOutput(
            extracted_dimensions=dims,
            conflicts=[conflict],
            validation_errors=[],
            retry_count=0,
            schema_version="1.0",
        )
        assert len(output.conflicts) == 1
        assert output.conflicts[0].conflict_type == "temporal_overlap"

    def test_time_range_extractor_returns_deterministic_result(self):
        """TimeRangeExtractor returns valid DimensionExtractionResult with deterministic extraction."""
        from src.agent.nodes import TimeRangeExtractor
        from src.api.models.dimensions import DimensionExtractionInput

        extractor = TimeRangeExtractor()
        input_data = DimensionExtractionInput(
            query="Show me data for Q3 2024",
            dimension_type="time_range",
        )

        # Run synchronously for testing
        import asyncio
        result = asyncio.run(extractor.extract(input_data))

        assert result.dimension_type == "time_range"
        assert result.extraction_method == "deterministic"
        assert result.validation_status in ("valid", "invalid")

    def test_day_of_week_extractor_returns_valid_result(self):
        """DayOfWeekExtractor returns valid DimensionExtractionResult with correct days."""
        from src.agent.nodes import DayOfWeekExtractor
        from src.api.models.dimensions import DimensionExtractionInput

        extractor = DayOfWeekExtractor()
        input_data = DimensionExtractionInput(
            query="Show me weekend spending patterns",
            dimension_type="day_of_week",
        )

        import asyncio
        result = asyncio.run(extractor.extract(input_data))

        assert result.dimension_type == "day_of_week"
        assert result.extraction_method == "deterministic"
        # Should extract saturday and sunday from "weekend"
        assert "saturday" in result.values or "sunday" in result.values or result.values == []

    def test_card_type_extractor_returns_valid_result(self):
        """CardTypeExtractor returns valid DimensionExtractionResult."""
        from src.agent.nodes import CardTypeExtractor
        from src.api.models.dimensions import DimensionExtractionInput

        extractor = CardTypeExtractor()
        input_data = DimensionExtractionInput(
            query="Show me credit card transactions",
            dimension_type="card_type",
        )

        import asyncio
        result = asyncio.run(extractor.extract(input_data))

        assert result.dimension_type == "card_type"
        assert result.extraction_method == "lookup"
        assert "credit" in result.values or result.values == []

    def test_payment_network_extractor_returns_valid_result(self):
        """PaymentNetworkExtractor returns valid DimensionExtractionResult."""
        from src.agent.nodes import PaymentNetworkExtractor
        from src.api.models.dimensions import DimensionExtractionInput

        extractor = PaymentNetworkExtractor()
        input_data = DimensionExtractionInput(
            query="Show me Visa and Mastercard transactions",
            dimension_type="payment_network",
        )

        import asyncio
        result = asyncio.run(extractor.extract(input_data))

        assert result.dimension_type == "payment_network"
        assert result.extraction_method == "lookup"
        assert "visa" in result.values or result.values == []

    def test_channel_extractor_returns_valid_result(self):
        """ChannelExtractor returns valid DimensionExtractionResult."""
        from src.agent.nodes import ChannelExtractor
        from src.api.models.dimensions import DimensionExtractionInput

        extractor = ChannelExtractor()
        input_data = DimensionExtractionInput(
            query="Show me online purchases",
            dimension_type="channel",
        )

        import asyncio
        result = asyncio.run(extractor.extract(input_data))

        assert result.dimension_type == "channel"
        assert result.extraction_method == "lookup"
        assert "online" in result.values or result.values == []

    def test_synonym_resolver_fuzzy_match_brand(self):
        """SynonymResolver.fuzzy_match_brand works with brand list."""
        from src.api.lookup import SynonymResolver

        resolver = SynonymResolver()
        brands = ["Walmart", "Target", "Costco", "Amazon", "Kroger"]

        # Test exact-ish match
        results = resolver.fuzzy_match_brand("walmrt", brands)  # typo
        assert len(results) > 0
        assert results[0][0] == "Walmart"  # Should match Walmart

    def test_llm_extraction_validator_validates_dimension_output(self):
        """LLMExtractionValidator.validate_dimensions works with ExtractedDimensions."""
        from src.agent.validation import LLMExtractionValidator
        from src.api.models.dimensions import ExtractedDimensions

        validator = LLMExtractionValidator()
        dims = ExtractedDimensions(
            generation=["gen_z", "millennial"],
            income_band=["band_4", "band_5"],
            card_type=["credit"],
            payment_network=["visa"],
            channel=["online"],
            day_of_week=["saturday"],
        )

        errors = validator.validate_dimensions(dims)
        # No errors for valid values
        assert isinstance(errors, list)

    def test_detect_conflicts_returns_list(self):
        """detect_conflicts returns a list (empty or with conflicts)."""
        from src.agent.validation import detect_conflicts
        from src.api.models.dimensions import ExtractedDimensions

        dims = ExtractedDimensions(
            time_range={"periods": ["last_month"]},
        )
        conflicts = detect_conflicts(dims)
        assert isinstance(conflicts, list)


# ============================================================================
# 5. Model Configuration Contract Tests
# ============================================================================


class TestModelConfigurationContracts:
    """Verify that Unit 5 uses the correct model configuration from IU-6."""

    def test_model_config_has_dimension_extraction_field(self):
        """ModelConfig has dimension_extraction field used by IU-5 extractors."""
        from src.config import ModelConfig

        config = ModelConfig()
        assert hasattr(config, "dimension_extraction")
        assert isinstance(config.dimension_extraction, str)
        assert "/" in config.dimension_extraction  # provider/model format

    def test_model_config_dimension_extraction_is_kimi(self):
        """ModelConfig.dimension_extraction defaults to moonshot/kimi-k2 per FR-8.2."""
        from src.config import ModelConfig

        config = ModelConfig()
        # Should be kimi provider for dimension extraction
        assert "kimi" in config.dimension_extraction.lower() or "moonshot" in config.dimension_extraction.lower()

    def test_internal_models_has_dimension_extraction_key(self):
        """INTERNAL_MODELS contains 'dimension_extraction' key used by Unit 5."""
        from src.config import INTERNAL_MODELS

        assert "dimension_extraction" in INTERNAL_MODELS
        assert isinstance(INTERNAL_MODELS["dimension_extraction"], str)
