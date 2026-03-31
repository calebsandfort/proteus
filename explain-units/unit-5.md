# Unit 5: Dimension Extraction Pipeline

> **Status:** Implemented
> **FR Coverage:** FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-3.5, FR-3.6, FR-3.7
> **Dependencies:** IU-3 (ASP.NET Core Data API), IU-6 (OpenRouter Integration)

## Overview

Unit 5 implements a parallel dimension extraction pipeline that parses user queries to identify and extract structured dimensional parameters. The system extracts ten dimension types (brand, merchant_category, geography, time_range, generation, income_band, card_type, payment_network, channel, day_of_week) using a combination of LLM-based extraction, deterministic parsing, and cached lookup operations. The architecture executes independent dimension extractors concurrently via `asyncio.gather()`, with a total latency budget of 600-1200ms. This unit serves as the critical bridge between natural language user queries and the structured API query construction required by Units 3 and 4.

The dimension extraction pipeline is invoked after tool selection (Unit 7) determines which tools the user intends to use. It receives the user's query and conversation history, then produces an `ExtractedDimensions` object containing validated dimension values that downstream nodes use to construct actual API calls.

## Functionality Implemented

- **Time Range Extraction** (FR-3.3) — Deterministic parser handling "last quarter", "Q3 2024", "YTD", date ranges with 10-50ms target latency
- **Brand Extraction** (FR-3.1, FR-3.4) — LLM-powered extraction with fuzzy matching and alias resolution (Walmart→walmart, Target→target)
- **Category Extraction** (FR-3.1) — LLM extraction validated against merchant category enumeration
- **Generation Extraction** (FR-3.1, FR-3.4) — Maps layman terms ("young people"→Gen Z) with confidence scoring and alternative suggestions
- **Income Band Extraction** (FR-3.1) — Maps descriptive ranges ("under $25K") to band IDs (under_25k, 25k_50k, 50k_75k, 75k_100k, 100k_150k, 150k_200k, over_200k)
- **Card Type Extraction** (FR-3.1) — Lookup-based extraction for credit/debit/prepaid distinctions
- **Payment Network Extraction** (FR-3.1) — Lookup for Visa/Mastercard/Amex/Discover networks
- **Channel Extraction** (FR-3.1) — Maps in-store/mobile/online to standardized channel IDs
- **Day of Week Extraction** (FR-3.1) — Deterministic extraction for weekday/weekend analysis
- **Geography Extraction** (FR-3.1) — State abbreviation normalization, CBSA/metro resolution, zip-to-region mapping with 50-150ms latency
- **Parallel Execution Architecture** (FR-3.2) — Independent dimensions extracted concurrently via asyncio.gather()
- **Synonym Resolution** (FR-3.4) — Fuzzy matching with Levenshtein distance and alias tables for brand layman terms
- **Dimension Validation** (FR-3.5) — Validates extracted values against IU-3 enumeration API with suggestion-based error recovery
- **Conflict Resolution** (FR-3.6) — Detects contradictory dimensions (e.g., "Target sales in TX and CA last month and last year") and surfaces structured disambiguation with 2-3 options maximum
- **Extraction Output Schema** (FR-3.7) — All LLM outputs validated against Pydantic schemas before proceeding; invalid outputs trigger retry with explicit system prompt correction

## Implementation Details

### Technology Stack

- **asyncio** — Parallel executor for independent dimension extractors
- **Pydantic** — Input/output schema validation (DimensionExtractionInput, ExtractedDimensions, DimensionValidationResult)
- **RapidFuzz** — Fuzzy string matching for brand alias resolution
- **OpenRouter Client** — LLM calls for BrandExtractor, CategoryExtractor, GenerationExtractor, IncomeBandExtractor (delegates to IU-6)
- **Cached Lookups** — In-memory dictionaries for card_type, payment_network, channel, geography normalization

### Architectural Patterns

**Parallel Extraction with Sequential Dependencies**: Independent dimensions (brand, category, generation, income_band, card_type, payment_network, channel, day_of_week) run in parallel via `asyncio.gather()`. Time range extraction runs deterministically without LLM dependency. Geography extraction uses cached lookups but must resolve state abbreviations before CBSA lookup, so it runs sequentially after parallel phase.

**Hybrid Extraction Strategies**: Each dimension type uses an appropriate extraction strategy:
- **LLM-based**: Brand, Category, Generation, IncomeBand (complex semantic understanding required)
- **Deterministic**: TimeRange, DayOfWeek (rule-based parsing sufficient)
- **Lookup-based**: CardType, PaymentNetwork, Channel (enum validation only)

**Conflict Detection**: The `LLMExtractionValidator.conflicts_detected()` method identifies contradictory dimension values across time ranges, geographies, and brands. Conflicts are returned as structured `DimensionConflict` objects rather than attempting resolution.

### Key Design Decisions

**Token Budget per Extractor**: Each dimension extraction prompt includes only conversation turns relevant to that dimension, capped at 2,000 tokens. This prevents LLM context pollution and controls costs.

**Validation Before Proceeding**: All extracted dimensions are validated against IU-3's dimension enumeration API before the `ExtractedDimensions` object is considered complete. This catches invalid values early rather than letting them propagate to API query construction.

**No Silent Fallback for Conflicts**: When dimension conflicts are detected, the system surfaces a `HITLClarification` with 2-3 disambiguation options rather than generating multiple API calls or making best-effort interpretations.

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/api/models/dimensions.py` | Pydantic models: ExtractedDimensions, DimensionValidationResult, DimensionConflict, Generation, IncomeBand, CardType, Channel, PaymentNetwork |
| `backend/src/agent/nodes.py` | DimensionExtractor abstract class, BrandExtractor, TimeRangeExtractor, GeographyExtractor, CategoryExtractor, GenerationExtractor, IncomeBandExtractor, CardTypeExtractor, PaymentNetworkExtractor, ChannelExtractor, DayOfWeekExtractor |
| `backend/src/agent/dimension_graph.py` | DimensionExtractionGraph orchestrating parallel/sequential execution with latency budget tracking |
| `backend/src/api/lookup.py` | SynonymResolver with fuzzy matching, brand alias lookup, geography normalization |
| `backend/src/agent/validation.py` | LLMExtractionValidator with conflict detection, validate_dimensions() method |
| `backend/src/api/stubs.py` | IU-3 API stub for dimension enumeration during development/testing |
| `backend/tests/test_dimension_graph.py` | Graph execution tests with parallel/sequential latency verification |
| `backend/tests/test_dimension_nodes.py` | Individual extractor tests for each dimension type |
| `backend/tests/test_dimensions.py` | Pydantic model validation tests |
| `backend/tests/test_lookup.py` | SynonymResolver and geography normalization tests |
| `backend/tests/test_validation.py` | Validator tests for conflict detection and dimension validation |

## Integration Points

### This Unit Provides

**To Unit 7 (LangGraph Agent Graph):**
- `DimensionExtractionGraph` class accepting `DimensionExtractionInput` and returning `ExtractedDimensions`
- Parallel execution with configurable latency budget
- Structured conflict objects for HITL clarification

**To Unit 3 (ASP.NET Core Data API):**
- `ExtractedDimensions` output schema consumed during query construction
- Dimension enumeration validation before API calls execute

**To Unit 4 (Tool Registry):**
- Validated dimension values from the extraction pipeline

### This Unit Depends On

**From IU-3 (ASP.NET Core Data API):**
- Dimension enumeration cached data for validation (brands, categories, geographies, etc.)
- Stub implementation in `backend/src/api/stubs.py` for development without live API

**From IU-6 (OpenRouter Integration):**
- `OpenRouterClient.call_with_retry()` for LLM-based extractors
- Model configuration: `moonshot/kimi-k2` for dimension extraction

## Usage Guide

### Running Dimension Extraction

```python
from backend.src.agent.dimension_graph import DimensionExtractionGraph
from backend.src.api.models.dimensions import DimensionExtractionInput

graph = DimensionExtractionGraph()

input_data = DimensionExtractionInput(
    query="Show me Target sales in Texas and California for Q3 2024",
    conversation_history=[],
    dimension_type="all",
    max_tokens=2000
)

result = await graph.extract(input_data)
# result is an ExtractedDimensions object
```

### Individual Extractor Usage

```python
from backend.src.agent.nodes import BrandExtractor, TimeRangeExtractor

brand_extractor = BrandExtractor()
time_extractor = TimeRangeExtractor()

# LLM-based extraction
brand_result = await brand_extractor.extract(
    query="What brands do you shop at?",
    conversation_history=[]
)

# Deterministic parsing
time_result = await time_extractor.extract(
    query="last quarter",
    conversation_history=[]
)
```

### Validation

```python
from backend.src.agent.validation import LLMExtractionValidator

validator = LLMExtractionValidator()
validation_result = await validator.validate_dimensions(
    extracted=result,
    tool_id="sales_by_brand"
)

if not validation_result.is_valid:
    # Handle missing required dimensions
    missing = validation_result.missing_dimensions
```

### Conflict Detection

```python
conflicts = validator.conflicts_detected(result)
if conflicts:
    for conflict in conflicts:
        print(f"{conflict.dimension}: {conflict.values} - {conflict.reason}")
        # Returns 2-3 disambiguation options per conflict
```

### Configuration

Environment variables and configuration:
- `OPENAI_API_KEY` — Required for LLM-based extractors (inherited from IU-6)
- `OPENROUTER_API_KEY` — Primary LLM API key for dimension extraction
- Dimension enumeration cache initialized from IU-3 API stubs

Latency budgets per extractor type:
- TimeRangeExtractor: 10-50ms (deterministic)
- BrandExtractor: 400-800ms (LLM)
- GeographyExtractor: 50-150ms (cached lookup)
- Others: 200-400ms (lookup or LLM)

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `0ebc866` | 2026-03-30 | feat: implement Unit 5 Dimension Extraction Pipeline (FR-3.1-3.7) |
| `fd35719` | 2026-03-28 | fix: align dimension IDs across Unit 2, Unit 3, and DB seed |

### Commit 0ebc866 — Unit 5 Implementation

Implements parallel dimension extraction for 10 dimension types:
- TimeRangeExtractor (deterministic, 10-50ms)
- BrandExtractor (LLM + fuzzy, 400-800ms)
- CategoryExtractor (LLM + enum)
- GenerationExtractor (LLM)
- IncomeBandExtractor (LLM)
- CardTypeExtractor (lookup, 200-400ms)
- PaymentNetworkExtractor (lookup, 200-400ms)
- ChannelExtractor (lookup, 200-400ms)
- DayOfWeekExtractor (deterministic, 100-200ms)
- GeographyExtractor (lookup, 50-150ms)

Features: Parallel execution via asyncio.gather() with 600-1200ms budget, SynonymResolver with fuzzy matching (FR-3.4), LLMExtractionValidator with conflict detection (FR-3.5, 3.6), IU-3 API stub for dimension enumeration, 99 tests passing.

**Files changed**: 12 files, +3,671 lines, -418 lines

### Commit fd35719 — Dimension ID Alignment

Aligns dimension IDs across Unit 2, Unit 3, and database seed:
- Renames generation IDs to match DB seed: boomer→baby_boomer, fixes millennial/silent plurals, removes gen_alpha from Unit 3 YAML
- Replaces integer income band IDs with 7 descriptive string IDs (under_25k…over_200k)
- Renames channel values to use underscores: in-store→in_store, mobile→mobile_app
- Updates DB seed SQL to use descriptive income band IDs
- Adds MCP Postgres server config (.mcp.json)
- Adds contract tests verifying Unit 2/Unit 3 dimension alignment
