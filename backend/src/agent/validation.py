"""FR-3.5 & FR-3.6: Dimension Validation and Conflict Resolution.

This module provides:
- LLMExtractionValidator: Validates LLM JSON output against schema
- detect_conflicts(): Detects temporal and spatial conflicts in extracted dimensions
- Conflict resolution with disambiguation options

FR-3.5: The system SHALL validate extracted dimensions against the API's
dimension enumeration endpoint before constructing queries.

FR-3.6: When dimension conflicts are detected, the system SHALL surface
structured disambiguation. The system SHALL NOT silently generate multiple
API calls or make best-effort interpretations.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from src.api.models.dimensions import (
    DisambiguationOption,
    DimensionConflict,
    DimensionExtractionOutput,
    ExtractedDimensions,
    GENERATIONS,
    INCOME_BANDS,
)


class LLMExtractionValidator:
    """Validates LLM JSON output against the dimension extraction schema.

    FR-3.7: The system SHALL validate LLM outputs against the schema
    before proceeding. Invalid outputs SHALL trigger retry with explicit
    system prompt correction.

    Attributes:
        schema_version: Current schema version for validation.
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self) -> None:
        self.schema_version = self.SCHEMA_VERSION

    def validate(
        self, raw_output: str
    ) -> Tuple[bool, Optional[DimensionExtractionOutput], Optional[str]]:
        """Validate raw LLM output against DimensionExtractionOutput schema.

        Args:
            raw_output: Raw JSON string from LLM output.

        Returns:
            Tuple of (is_valid, parsed_output, error_message).
            If valid, parsed_output contains the DimensionExtractionOutput.
            If invalid, error_message contains the validation error.
        """
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON: {str(e)}"

        try:
            output = DimensionExtractionOutput(**parsed)
        except Exception as e:
            return False, None, f"Schema validation error: {str(e)}"

        # Validate schema version
        if output.schema_version != self.schema_version:
            return False, None, f"Schema version mismatch: expected {self.schema_version}, got {output.schema_version}"

        return True, output, None

    def validate_dimensions(
        self, dimensions: ExtractedDimensions
    ) -> List[str]:
        """Validate extracted dimensions against known enumerations.

        FR-3.5: Validate extracted dimensions against known enumerations.

        Args:
            dimensions: Extracted dimensions to validate.

        Returns:
            List of validation error messages. Empty list if all valid.
        """
        errors: List[str] = []

        # Validate generation values
        for gen in dimensions.generation:
            if gen not in GENERATIONS:
                errors.append(f"Invalid generation: {gen}")

        # Validate income_band values
        for band in dimensions.income_band:
            if band not in INCOME_BANDS:
                errors.append(f"Invalid income_band: {band}")

        # Validate card_type values
        valid_card_types = {"credit", "debit", "prepaid", "corporate"}
        for card_type in dimensions.card_type:
            if card_type not in valid_card_types:
                errors.append(f"Invalid card_type: {card_type}")

        # Validate payment_network values
        valid_networks = {"visa", "mastercard", "amex", "discover"}
        for network in dimensions.payment_network:
            if network not in valid_networks:
                errors.append(f"Invalid payment_network: {network}")

        # Validate channel values
        valid_channels = {"online", "in_store", "mobile"}
        for channel in dimensions.channel:
            if channel not in valid_channels:
                errors.append(f"Invalid channel: {channel}")

        # Validate day_of_week values
        valid_days = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
        for day in dimensions.day_of_week:
            if day not in valid_days:
                errors.append(f"Invalid day_of_week: {day}")

        # Validate aggregation_level values
        valid_aggregation = {"hourly", "daily", "weekly", "monthly", "quarterly", "annual", "auto"}
        if dimensions.aggregation_level and dimensions.aggregation_level not in valid_aggregation:
            errors.append(f"Invalid aggregation_level: {dimensions.aggregation_level}")

        return errors


def detect_conflicts(dimensions: ExtractedDimensions) -> List[DimensionConflict]:
    """Detect conflicts in extracted dimensions.

    FR-3.6: When dimension conflicts are detected, the system SHALL
    surface structured disambiguation. The system SHALL NOT silently
    generate multiple API calls or make best-effort interpretations.

    Conflict Types:
    - temporal_overlap: Multiple time periods specified (e.g., "last month and last year")
    - geographic_overlap: Multiple geographic regions that may conflict

    Args:
        dimensions: Extracted dimensions to check for conflicts.

    Returns:
        List of DimensionConflict objects. Empty list if no conflicts.
    """
    conflicts: List[DimensionConflict] = []

    # Detect temporal conflicts
    temporal_conflict = _detect_temporal_conflict(dimensions)
    if temporal_conflict:
        conflicts.append(temporal_conflict)

    # Detect geographic conflicts (same logic can apply)
    # Geographic conflicts are less clear-cut, so we return empty for now
    # as they depend on specific business rules

    return conflicts


def _detect_temporal_conflict(dimensions: ExtractedDimensions) -> Optional[DimensionConflict]:
    """Detect temporal conflicts in time ranges.

    A temporal conflict occurs when multiple distinct time periods are specified
    that overlap or contradict each other.

    Args:
        dimensions: Extracted dimensions to check.

    Returns:
        DimensionConflict if temporal conflict detected, None otherwise.
    """
    if not dimensions.time_range or not dimensions.time_range.get("periods"):
        return None

    time_range = dimensions.time_range

    # Check for multiple periods
    periods = time_range.get("periods", [])
    if len(periods) <= 1:
        return None

    # Detect conflicting periods
    # For example: "last month" and "last year" conflict
    # We generate disambiguation options

    options = _generate_temporal_options(periods)

    if options:
        return DimensionConflict(
            dimension="time_range",
            conflicting_values=periods,
            conflict_type="temporal_overlap",
            options=options,
        )

    return None


def _generate_temporal_options(periods: List[str]) -> List[DisambiguationOption]:
    """Generate disambiguation options for temporal conflicts.

    Args:
        periods: List of conflicting time period descriptions.

    Returns:
        List of 2-3 DisambiguationOption objects.
    """
    if len(periods) < 2:
        return []

    # Generate options based on the periods
    options = []

    # Option 1: Use the first period only
    options.append(DisambiguationOption(
        id="use_first",
        label=f"Use: {periods[0]}",
        resolved_dimensions={"time_range": {"periods": [periods[0]]}},
        reasoning=f"Select only the first time period ({periods[0]})",
    ))

    # Option 2: Use the most recent period
    if len(periods) >= 2:
        options.append(DisambiguationOption(
            id="use_most_recent",
            label=f"Use: {periods[-1]}",
            resolved_dimensions={"time_range": {"periods": [periods[-1]]}},
            reasoning=f"Select only the most recent time period ({periods[-1]})",
        ))

    # Option 3: Combine into a single range if possible
    if len(periods) == 2:
        options.append(DisambiguationOption(
            id="combine",
            label=f"Combine: {periods[0]} to {periods[1]}",
            resolved_dimensions={"time_range": {"periods": [f"{periods[0]} to {periods[1]}"]}},
            reasoning=f"Combine both periods into a single range from {periods[0]} to {periods[1]}",
        ))

    # Limit to 3 options maximum
    return options[:3]
