"""FR-3: Dimension Extraction Pipeline Pydantic Models.

This module defines the Pydantic models for the Dimension Extraction Pipeline.

FR Requirements:
- FR-3.1: Dimension Categories (brand, merchant_category, geography, time_range,
  generation, income_band, card_type, payment_network, channel, day_of_week,
  aggregation_level)
- FR-3.5: Dimension Validation (DimensionValidationResult, ExtractedDimensions)
- FR-3.6: Conflict Resolution (DimensionConflict, DisambiguationOption)
- FR-3.7: Extraction Output Schema (DimensionExtractionOutput)

Models:
    Generation: Enum-like model for generation dimension
    IncomeBand: Enum-like model for income band dimension
    GENERATIONS: Pre-defined generation constants
    INCOME_BANDS: Pre-defined income band constants
    DimensionExtractionInput: Input for dimension extraction
    DimensionExtractionResult: Result from dimension extraction
    DimensionValidationResult: Validation result for a dimension value
    ExtractedDimensions: Container for all extracted dimension values
    DisambiguationOption: Option for resolving a dimension conflict
    DimensionConflict: Represents a conflict between dimension values
    DimensionExtractionOutput: Final output of dimension extraction pipeline
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Generation(BaseModel):
    """Generation dimension model.

    Represents demographic generations (Gen Z, Millennial, Gen X, etc.)
    with their defining characteristics and aliases.

    Attributes:
        id: Unique identifier for the generation.
        label: Human-readable label.
        birth_years: String representation of birth year range.
        aliases: List of alternative names for semantic matching.
    """

    model_config = ConfigDict(from_attributes=True)

    id: Literal["gen_z", "millennial", "gen_x", "boomer", "silent"] = Field(
        ..., description="Unique identifier for the generation"
    )
    label: str = Field(..., description="Human-readable label")
    birth_years: str = Field(..., description="String representation of birth year range")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")


class IncomeBand(BaseModel):
    """Income band dimension model.

    Represents income bands with their USD range and aliases.

    Attributes:
        id: Unique identifier for the income band.
        label: Human-readable label.
        range_usd: String representation of income range in USD.
        aliases: List of alternative names for semantic matching.
    """

    model_config = ConfigDict(from_attributes=True)

    id: Literal["band_1", "band_2", "band_3", "band_4", "band_5", "band_6"] = Field(
        ..., description="Unique identifier for the income band"
    )
    label: str = Field(..., description="Human-readable label")
    range_usd: str = Field(..., description="String representation of income range in USD")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")


# Pre-defined constants for dimension lookup
GENERATIONS: Dict[str, Generation] = {
    "gen_z": Generation(
        id="gen_z",
        label="Generation Z",
        birth_years="1997-2024",
        aliases=["gen_z", "gen z", "zoomers", "z generation", "post-millennial"]
    ),
    "millennial": Generation(
        id="millennial",
        label="Millennial",
        birth_years="1981-1996",
        aliases=["millennial", "millennials", "gen_y", "echo_boomers", "gen y"]
    ),
    "gen_x": Generation(
        id="gen_x",
        label="Generation X",
        birth_years="1965-1980",
        aliases=["gen_x", "gen x", "xers", "generation x"]
    ),
    "boomer": Generation(
        id="boomer",
        label="Baby Boomer",
        birth_years="1946-1964",
        aliases=["boomer", "boomers", "baby_boomer", "baby boomer", "gen_boomer"]
    ),
    "silent": Generation(
        id="silent",
        label="Silent Generation",
        birth_years="1928-1945",
        aliases=["silent", "silent_gen", "silent generation", "traditionalists"]
    ),
}

INCOME_BANDS: Dict[str, IncomeBand] = {
    "band_1": IncomeBand(
        id="band_1",
        label="Very Low Income",
        range_usd="<$25,000",
        aliases=["very low", "low income", "poverty", "band1", "income_1"]
    ),
    "band_2": IncomeBand(
        id="band_2",
        label="Low-Middle Income",
        range_usd="$25,000-$49,999",
        aliases=["low middle", "lower middle", "working class", "band2", "income_2"]
    ),
    "band_3": IncomeBand(
        id="band_3",
        label="Middle Income",
        range_usd="$50,000-$74,999",
        aliases=["middle", "middle class", "middle_income", "band3", "income_3"]
    ),
    "band_4": IncomeBand(
        id="band_4",
        label="Upper-Middle Income",
        range_usd="$75,000-$99,999",
        aliases=["upper middle", "upper_middle", "affluent", "band4", "income_4"]
    ),
    "band_5": IncomeBand(
        id="band_5",
        label="High Income",
        range_usd="$100,000-$149,999",
        aliases=["high income", "high_income", "wealthy", "band5", "income_5"]
    ),
    "band_6": IncomeBand(
        id="band_6",
        label="Very High Income",
        range_usd="$150,000+",
        aliases=["very high", "very high income", "affluent", "elite", "band6", "income_6"]
    ),
}


class DimensionExtractionInput(BaseModel):
    """Input for dimension extraction.

    Attributes:
        query: The user query to extract dimensions from.
        conversation_history: Optional conversation history for context.
        dimension_type: The specific dimension type to extract.
        max_tokens: Maximum tokens for LLM extraction (default 2000).
    """

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(..., description="The user query to extract dimensions from")
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Optional conversation history for context"
    )
    dimension_type: str = Field(..., description="The specific dimension type to extract")
    max_tokens: int = Field(default=2000, ge=1, description="Maximum tokens for LLM extraction")


class DimensionExtractionResult(BaseModel):
    """Result from dimension extraction.

    Attributes:
        dimension_type: The dimension type that was extracted.
        values: List of extracted dimension values.
        confidence: Confidence score (0.0 to 1.0).
        alternatives: List of alternative extraction results.
        extraction_method: Method used ("llm", "deterministic", or "lookup").
        latency_ms: Extraction latency in milliseconds.
        validation_status: Validation status ("valid", "needs_review", "invalid").
    """

    model_config = ConfigDict(from_attributes=True)

    dimension_type: str = Field(..., description="The dimension type that was extracted")
    values: List[Any] = Field(..., description="List of extracted dimension values")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    alternatives: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of alternative extraction results"
    )
    extraction_method: Literal["llm", "deterministic", "lookup"] = Field(
        ..., description="Method used for extraction"
    )
    latency_ms: int = Field(..., ge=0, description="Extraction latency in milliseconds")
    validation_status: Literal["valid", "needs_review", "invalid"] = Field(
        ..., description="Validation status"
    )


class DimensionValidationResult(BaseModel):
    """Validation result for a dimension value.

    Attributes:
        is_valid: Whether the dimension value is valid.
        dimension: The dimension type.
        value: The original value provided.
        canonical_value: The canonical/normalized value if valid.
        suggestions: List of suggested corrections if invalid.
    """

    model_config = ConfigDict(from_attributes=True)

    is_valid: bool = Field(..., description="Whether the dimension value is valid")
    dimension: str = Field(..., description="The dimension type")
    value: str = Field(..., description="The original value provided")
    canonical_value: Optional[str] = Field(
        default=None,
        description="The canonical/normalized value if valid"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="List of suggested corrections if invalid"
    )


class ExtractedDimensions(BaseModel):
    """Container for all extracted dimension values.

    FR-3.1: Supports all 11 dimension categories:
    - brand, merchant_category, geography, time_range, generation
    - income_band, card_type, payment_network, channel
    - day_of_week, aggregation_level

    Attributes:
        brand: List of brand values.
        merchant_category: List of merchant category values.
        geography: List of geography values.
        time_range: Time range as dict with start/end/granularity.
        generation: List of generation IDs.
        income_band: List of income band IDs.
        card_type: List of card type values.
        payment_network: List of payment network values.
        channel: List of channel values.
        day_of_week: List of day of week values.
        aggregation_level: Optional aggregation level.
    """

    model_config = ConfigDict(from_attributes=True)

    brand: List[str] = Field(default_factory=list, description="List of brand values")
    merchant_category: List[str] = Field(
        default_factory=list,
        description="List of merchant category values"
    )
    geography: List[str] = Field(default_factory=list, description="List of geography values")
    time_range: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Time range with start/end/granularity"
    )
    generation: List[str] = Field(default_factory=list, description="List of generation IDs")
    income_band: List[str] = Field(default_factory=list, description="List of income band IDs")
    card_type: List[str] = Field(default_factory=list, description="List of card type values")
    payment_network: List[str] = Field(
        default_factory=list,
        description="List of payment network values"
    )
    channel: List[str] = Field(default_factory=list, description="List of channel values")
    day_of_week: List[str] = Field(default_factory=list, description="List of day of week values")
    aggregation_level: Optional[str] = Field(
        default=None,
        description="Optional aggregation level"
    )


class DisambiguationOption(BaseModel):
    """Option for resolving a dimension conflict.

    Attributes:
        id: Unique identifier for this option.
        label: Human-readable label describing the option.
        resolved_dimensions: The dimensions with this option applied.
        reasoning: Explanation of why this option was generated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique identifier for this option")
    label: str = Field(..., description="Human-readable label describing the option")
    resolved_dimensions: Dict[str, Any] = Field(
        ...,
        description="The dimensions with this option applied"
    )
    reasoning: str = Field(..., description="Explanation of why this option was generated")


class DimensionConflict(BaseModel):
    """Represents a conflict between dimension values.

    FR-3.6: Conflicts occur when extracted dimensions have overlapping
    or contradictory values that need disambiguation.

    Attributes:
        dimension: The dimension type that has a conflict.
        conflicting_values: List of values that conflict with each other.
        conflict_type: Type of conflict ("temporal_overlap" or "geographic_overlap").
        options: List of disambiguation options to resolve the conflict.
    """

    model_config = ConfigDict(from_attributes=True)

    dimension: str = Field(..., description="The dimension type that has a conflict")
    conflicting_values: List[Any] = Field(
        ...,
        description="List of values that conflict with each other"
    )
    conflict_type: Literal["temporal_overlap", "geographic_overlap"] = Field(
        ...,
        description="Type of conflict"
    )
    options: List[DisambiguationOption] = Field(
        ...,
        description="List of disambiguation options to resolve the conflict"
    )


class DimensionExtractionOutput(BaseModel):
    """Final output of dimension extraction pipeline.

    FR-3.7: This is the complete output schema for the dimension
    extraction process, including all extracted dimensions,
    any conflicts that need resolution, and validation errors.

    Attributes:
        extracted_dimensions: All extracted dimension values.
        conflicts: List of dimension conflicts needing resolution.
        validation_errors: List of validation error messages.
        retry_count: Number of retries attempted.
        schema_version: Schema version identifier.
    """

    model_config = ConfigDict(from_attributes=True)

    extracted_dimensions: ExtractedDimensions = Field(
        ...,
        description="All extracted dimension values"
    )
    conflicts: List[DimensionConflict] = Field(
        default_factory=list,
        description="List of dimension conflicts needing resolution"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation error messages"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retries attempted"
    )
    schema_version: str = Field(
        default="1.0",
        description="Schema version identifier"
    )
