"""FR-3.2: Dimension Extraction Graph.

This module provides the DimensionExtractionGraph for orchestrating
parallel dimension extraction across all dimension types.

FR-3.2 Architecture:
- Independent dimensions execute in parallel (brand, category, generation, income_band, etc.)
- Total parallel extraction budget: 600-1200ms
- Each dimension extractor targets specific latency per FR-3.2

The graph produces an ExtractedDimensions object with all dimension
values extracted from the user query.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional

from src.api.models.dimensions import (
    ExtractedDimensions,
    DimensionExtractionInput,
    DimensionExtractionResult,
    DimensionExtractionOutput,
    DimensionConflict,
)
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
from src.agent.validation import detect_conflicts, LLMExtractionValidator


# Independent extractors that run in parallel (per FR-3.2)
INDEPENDENT_EXTRACTORS = [
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


class DimensionExtractionGraph:
    """Orchestrates parallel dimension extraction across all dimension types.

    FR-3.2: The system SHALL execute dimension extraction nodes in parallel
    for independent dimensions.

    Attributes:
        extractors: Dict mapping dimension type to extractor instance.
        validator: LLMExtractionValidator for output validation.
    """

    def __init__(self) -> None:
        """Initialize the dimension extraction graph."""
        self.extractors: Dict[str, Any] = {
            "brand": BrandExtractor(),
            "time_range": TimeRangeExtractor(),
            "geography": GeographyExtractor(),
            "category": CategoryExtractor(),
            "generation": GenerationExtractor(),
            "income_band": IncomeBandExtractor(),
            "card_type": CardTypeExtractor(),
            "payment_network": PaymentNetworkExtractor(),
            "channel": ChannelExtractor(),
            "day_of_week": DayOfWeekExtractor(),
        }
        self.validator = LLMExtractionValidator()

    async def extract_all(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> DimensionExtractionOutput:
        """Extract all dimension values from a query in parallel.

        FR-3.2: Execute dimension extraction nodes in parallel for
        independent dimensions. Target total latency: 600-1200ms.

        Args:
            query: The user query to extract dimensions from.
            conversation_history: Optional conversation history for context.

        Returns:
            DimensionExtractionOutput with all extracted dimensions.
        """
        start_time = time.perf_counter()
        conversation_history = conversation_history or []

        # Prepare extraction tasks for independent dimensions
        tasks = []
        for dim_type in INDEPENDENT_EXTRACTORS:
            if dim_type in self.extractors:
                extractor = self.extractors[dim_type]
                input_data = DimensionExtractionInput(
                    query=query,
                    conversation_history=conversation_history,
                    dimension_type=dim_type,
                )
                tasks.append(self._run_extractor(dim_type, extractor, input_data))

        # Execute all independent extractors in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dict
        result_dict: Dict[str, DimensionExtractionResult] = {}
        for i, dim_type in enumerate(INDEPENDENT_EXTRACTORS):
            if dim_type in self.extractors:
                result = results[i]
                if isinstance(result, Exception):
                    # Handle exception - create error result
                    result_dict[dim_type] = DimensionExtractionResult(
                        dimension_type=dim_type,
                        values=[],
                        confidence=0.0,
                        alternatives=[],
                        extraction_method="llm",
                        latency_ms=0,
                        validation_status="invalid",
                    )
                else:
                    result_dict[dim_type] = result

        # Build ExtractedDimensions from results
        extracted_dims = self._build_extracted_dimensions(result_dict)

        # Detect conflicts
        conflicts = detect_conflicts(extracted_dims)

        # Validate dimensions
        validation_errors = self.validator.validate_dimensions(extracted_dims)

        total_latency_ms = int((time.perf_counter() - start_time) * 1000)

        return DimensionExtractionOutput(
            extracted_dimensions=extracted_dims,
            conflicts=conflicts,
            validation_errors=validation_errors,
            retry_count=0,
            schema_version="1.0",
        )

    async def _run_extractor(
        self,
        dim_type: str,
        extractor: Any,
        input_data: DimensionExtractionInput,
    ) -> DimensionExtractionResult:
        """Run a single extractor and handle exceptions."""
        try:
            return await extractor.extract(input_data)
        except Exception as e:
            # Return error result
            return DimensionExtractionResult(
                dimension_type=dim_type,
                values=[],
                confidence=0.0,
                alternatives=[],
                extraction_method="llm",
                latency_ms=0,
                validation_status="invalid",
            )

    def _build_extracted_dimensions(
        self, results: Dict[str, DimensionExtractionResult]
    ) -> ExtractedDimensions:
        """Build ExtractedDimensions from extraction results."""
        def get_result(dim_type: str) -> DimensionExtractionResult:
            return results.get(dim_type, DimensionExtractionResult(
                dimension_type=dim_type, values=[], confidence=0.0,
                alternatives=[], extraction_method="lookup", latency_ms=0, validation_status="invalid"
            ))

        time_range_result = get_result("time_range")
        return ExtractedDimensions(
            brand=get_result("brand").values,
            merchant_category=get_result("category").values,
            geography=get_result("geography").values,
            time_range={"periods": time_range_result.values} if time_range_result.values else None,
            generation=get_result("generation").values,
            income_band=get_result("income_band").values,
            card_type=get_result("card_type").values,
            payment_network=get_result("payment_network").values,
            channel=get_result("channel").values,
            day_of_week=get_result("day_of_week").values,
        )


# Convenience function for easy use
async def extract_dimensions(
    query: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> DimensionExtractionOutput:
    """Extract all dimensions from a query.

    Convenience function that creates a DimensionExtractionGraph
    and extracts all dimensions in parallel.

    Args:
        query: The user query to extract dimensions from.
        conversation_history: Optional conversation history for context.

    Returns:
        DimensionExtractionOutput with all extracted dimensions.
    """
    graph = DimensionExtractionGraph()
    return await graph.extract_all(query, conversation_history)
