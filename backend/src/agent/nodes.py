from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.state import AgentState


async def chat_node(state: AgentState) -> AgentState:
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = await model.ainvoke(messages)
    return {"messages": [response]}


"""FR-3.2: Dimension Extraction Nodes.

This module provides dimension extraction nodes for the Dimension Extraction Pipeline.
Each extractor handles a specific dimension category and implements the
DimensionExtractor abstract base class.

FR-3.2 Latency Targets:
- TimeRangeExtractor: 10-50ms (deterministic parsing)
- GeographyExtractor: 50-150ms (cached lookups)
- BrandExtractor: 400-800ms (LLM + fuzzy matching)
- CategoryExtractor: 400-800ms (LLM + enum lookup)
- GenerationExtractor: 400-800ms (LLM with validation)
- IncomeBandExtractor: 400-800ms (LLM with validation)
- CardTypeExtractor: 200-400ms (deterministic + lookup)
- PaymentNetworkExtractor: 200-400ms (deterministic + lookup)
- ChannelExtractor: 200-400ms (deterministic + lookup)
- DayOfWeekExtractor: 100-200ms (deterministic)
"""

import asyncio
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.api.lookup import SynonymResolver
from src.api.models.dimensions import (
    GENERATIONS,
    INCOME_BANDS,
    DimensionExtractionInput,
    DimensionExtractionResult,
)
from src.api.openrouter import OpenRouterClient
from src.config import model_config


# ============================================================================
# Abstract Base Class
# ============================================================================

class DimensionExtractor(ABC):
    """Abstract base class for all dimension extractors.

    FR-3.2: Each dimension extraction prompt SHALL include only the relevant
    conversation turns and SHALL NOT exceed 2,000 tokens.

    Attributes:
        dimension_type: The dimension type this extractor handles.
        target_latency_ms: Target latency in milliseconds.
    """

    def __init__(self, dimension_type: str, target_latency_ms: int):
        self.dimension_type = dimension_type
        self.target_latency_ms = target_latency_ms

    @abstractmethod
    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract dimension values from input.

        Args:
            input: DimensionExtractionInput with query and context.

        Returns:
            DimensionExtractionResult with extracted values and metadata.
        """
        pass

    async def _llm_extract(
        self,
        input: DimensionExtractionInput,
        prompt_template: str,
        validation_fn: Optional[callable] = None,
    ) -> DimensionExtractionResult:
        """Generic LLM-based extraction with retry.

        Args:
            input: Extraction input.
            prompt_template: Prompt template with {query} placeholder.
            validation_fn: Optional function to validate extracted values.

        Returns:
            DimensionExtractionResult.
        """
        start_time = time.perf_counter()
        client = OpenRouterClient()

        messages = [
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": f"Query: {input.query}"},
        ]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.call_with_retry(
                    model=model_config.dimension_extraction,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=input.max_tokens,
                )

                # Parse response
                if isinstance(response, dict) and "content" in response:
                    content = response["content"]
                elif isinstance(response, str):
                    content = response
                else:
                    content = str(response)

                # Extract values from content (simple parsing)
                values = self._parse_llm_response(content, validation_fn)

                latency_ms = int((time.perf_counter() - start_time) * 1000)

                return DimensionExtractionResult(
                    dimension_type=self.dimension_type,
                    values=values,
                    confidence=0.8 if values else 0.0,
                    alternatives=[],
                    extraction_method="llm",
                    latency_ms=latency_ms,
                    validation_status="valid" if values else "invalid",
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    return DimensionExtractionResult(
                        dimension_type=self.dimension_type,
                        values=[],
                        confidence=0.0,
                        alternatives=[],
                        extraction_method="llm",
                        latency_ms=latency_ms,
                        validation_status="invalid",
                    )
                await asyncio.sleep(0.1 * (attempt + 1))

        # Should not reach here
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return DimensionExtractionResult(
            dimension_type=self.dimension_type,
            values=[],
            confidence=0.0,
            alternatives=[],
            extraction_method="llm",
            latency_ms=latency_ms,
            validation_status="invalid",
        )

    def _parse_llm_response(
        self, content: str, validation_fn: Optional[callable] = None
    ) -> List[str]:
        """Parse LLM response to extract values.

        Override in subclasses for custom parsing.

        Args:
            content: Raw LLM response.
            validation_fn: Optional validation function.

        Returns:
            List of extracted values.
        """
        # Simple JSON array parsing
        values = []
        try:
            import json
            # Try to find JSON array in response
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, list):
                    values = [str(v) for v in parsed if validation_fn is None or validation_fn(v)]
        except Exception:
            # Fall back to line-by-line parsing
            for line in content.split('\n'):
                line = line.strip().strip('"*-,')
                if line and (validation_fn is None or validation_fn(line)):
                    values.append(line)
        return values


# ============================================================================
# Time Range Extractor (Deterministic)
# ============================================================================

class TimeRangeExtractor(DimensionExtractor):
    """Deterministic time range extraction.

    FR-3.3: Parses "last quarter", "Q3 2024", "YTD" etc.
    Target latency: 10-50ms.

    Aggregation auto-selection rules:
    - 1-14 days -> daily
    - 15-90 days -> weekly
    - 91-365 days -> monthly
    - 366-730 days -> quarterly
    - 731+ days -> annual
    """

    QUERY_PATTERNS = [
        (r"last\s+quarter", "last_quarter", "rolling"),
        (r"Q([1-4])\s*(\d{4})", "Q{0} {1}", "calendar"),
        (r"YTD|year[\s-]to[\s-]date", "ytd", "calendar"),
        (r"last\s+year", "last_year", "rolling"),
        (r"last\s+(\d+)\s+days", "last_{0}_days", "rolling"),
        (r"last\s+(\d+)\s+months", "last_{0}_months", "rolling"),
        (r"this\s+quarter", "this_quarter", "calendar"),
        (r"this\s+month", "this_month", "calendar"),
        (r"this\s+year", "this_year", "calendar"),
    ]

    AGGREGATION_RULES = [
        ((1, 14), "daily"),
        ((15, 90), "weekly"),
        ((91, 365), "monthly"),
        ((366, 730), "quarterly"),
        ((731, 99999), "annual"),
    ]

    def __init__(self):
        super().__init__("time_range", 30)

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract time range from query using deterministic parsing."""
        start_time = time.perf_counter()

        query_lower = input.query.lower()
        parsed = None
        period_type = "calendar"

        for pattern, template, p_type in self.QUERY_PATTERNS:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                if "{" in template:
                    parsed = template.format(*match.groups())
                else:
                    parsed = template
                period_type = p_type
                break

        if not parsed:
            # Check for date ranges
            date_range = self._extract_date_range(query_lower)
            if date_range:
                parsed = date_range["description"]
                period_type = date_range["period_type"]

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if parsed:
            days = self._estimate_days(parsed)
            aggregation = self._infer_aggregation(days)

            return DimensionExtractionResult(
                dimension_type="time_range",
                values=[parsed],
                confidence=0.95,
                alternatives=[],
                extraction_method="deterministic",
                latency_ms=latency_ms,
                validation_status="valid",
            )

        return DimensionExtractionResult(
            dimension_type="time_range",
            values=[],
            confidence=0.0,
            alternatives=[],
            extraction_method="deterministic",
            latency_ms=latency_ms,
            validation_status="invalid",
        )

    def _extract_date_range(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract explicit date range from query."""
        # Look for "between X and Y" or date patterns
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        matches = re.findall(date_pattern, query)
        if len(matches) >= 2:
            return {
                "description": f"{matches[0]} to {matches[1]}",
                "period_type": "calendar",
            }
        return None

    def _estimate_days(self, time_desc: str) -> int:
        """Estimate number of days for a time description."""
        desc = time_desc.lower()
        if "last_quarter" in desc:
            return 90
        if "last_year" in desc:
            return 365
        if "ytd" in desc:
            return (datetime.now() - datetime(datetime.now().year, 1, 1)).days
        if match := re.search(r"last_(\d+)_days", desc):
            return int(match.group(1))
        if match := re.search(r"last_(\d+)_months", desc):
            return int(match.group(1)) * 30
        if "Q1" in desc:
            return 90
        if "Q2" in desc:
            return 91
        if "Q3" in desc:
            return 92
        if "Q4" in desc:
            return 92
        return 30  # Default to monthly

    def _infer_aggregation(self, days: int) -> str:
        """Infer aggregation level based on day count."""
        for (min_days, max_days), level in self.AGGREGATION_RULES:
            if min_days <= days <= max_days:
                return level
        return "monthly"


# ============================================================================
# Generation Extractor (LLM)
# ============================================================================

class GenerationExtractor(DimensionExtractor):
    """LLM-based generation extraction with validation.

    Target latency: 400-800ms.
    """

    PROMPT_TEMPLATE = """You are a data analyst extracting generation demographics from user queries.

Extract generation values from the query. Valid generations are:
- gen_z: Born 1997-2024 (also known as Zoomers, Gen Z)
- millennial: Born 1981-1996 (also known as Millennials, Gen Y)
- gen_x: Born 1965-1980 (also known as Gen X)
- boomer: Born 1946-1964 (also known as Baby Boomers)
- silent: Born before 1946 (also known as Silent Generation)

Return a JSON array of generation IDs found in the query.
Example: ["gen_z", "millennial"]

Query: {query}"""

    def __init__(self):
        super().__init__("generation", 600)
        self.synonym_resolver = SynonymResolver()

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract generation values using LLM with validation."""

        def validate_gen(value: str) -> bool:
            return value in GENERATIONS

        return await self._llm_extract(input, self.PROMPT_TEMPLATE, validate_gen)


# ============================================================================
# Income Band Extractor (LLM)
# ============================================================================

class IncomeBandExtractor(DimensionExtractor):
    """LLM-based income band extraction with validation.

    Target latency: 400-800ms.
    """

    PROMPT_TEMPLATE = """You are a data analyst extracting income band demographics from user queries.

Extract income band values from the query. Valid income bands are:
- band_1: <$25,000
- band_2: $25,000-$49,999
- band_3: $50,000-$74,999
- band_4: $75,000-$99,999
- band_5: $100,000-$149,999
- band_6: $150,000+

Return a JSON array of income band IDs found in the query.
Example: ["band_5", "band_6"]

Query: {query}"""

    def __init__(self):
        super().__init__("income_band", 600)
        self.synonym_resolver = SynonymResolver()

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract income band values using LLM with validation."""

        def validate_band(value: str) -> bool:
            return value in INCOME_BANDS

        return await self._llm_extract(input, self.PROMPT_TEMPLATE, validate_band)


# ============================================================================
# Card Type Extractor (Deterministic + Lookup)
# ============================================================================

class CardTypeExtractor(DimensionExtractor):
    """Card type extraction using synonym resolution.

    Target latency: 200-400ms.
    """

    VALID_TYPES = {"credit", "debit", "prepaid", "corporate"}

    def __init__(self):
        super().__init__("card_type", 300)
        self.synonym_resolver = SynonymResolver()

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract card type using deterministic matching."""
        start_time = time.perf_counter()

        query_lower = input.query.lower()
        values = []

        # Check for card type mentions
        for phrase in ["credit card", "debit card", "prepaid card", "corporate card"]:
            if phrase in query_lower:
                card_type = phrase.replace(" card", "").replace(" ", "_")
                if card_type in self.VALID_TYPES:
                    values.append(card_type)

        # Use synonym resolver for other mentions
        if not values:
            resolved = self.synonym_resolver.resolve("card_type", query_lower)
            values = [v for v, _ in resolved if v in self.VALID_TYPES]

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return DimensionExtractionResult(
            dimension_type="card_type",
            values=list(set(values)),
            confidence=0.9 if values else 0.0,
            alternatives=[],
            extraction_method="lookup",
            latency_ms=latency_ms,
            validation_status="valid" if values else "invalid",
        )


# ============================================================================
# Payment Network Extractor (Deterministic + Lookup)
# ============================================================================

class PaymentNetworkExtractor(DimensionExtractor):
    """Payment network extraction using synonym resolution.

    Target latency: 200-400ms.
    """

    VALID_NETWORKS = {"visa", "mastercard", "amex", "discover"}

    def __init__(self):
        super().__init__("payment_network", 300)
        self.synonym_resolver = SynonymResolver()

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract payment network using deterministic matching."""
        start_time = time.perf_counter()

        query_lower = input.query.lower()
        values = []

        # Check for network mentions
        for network in ["visa", "mastercard", "amex", "american express", "discover"]:
            if network in query_lower:
                if network == "american express":
                    values.append("amex")
                else:
                    values.append(network)

        # Deduplicate
        values = list(set(values))
        values = [v for v in values if v in self.VALID_NETWORKS]

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return DimensionExtractionResult(
            dimension_type="payment_network",
            values=values,
            confidence=0.9 if values else 0.0,
            alternatives=[],
            extraction_method="lookup",
            latency_ms=latency_ms,
            validation_status="valid" if values else "invalid",
        )


# ============================================================================
# Channel Extractor (Deterministic + Lookup)
# ============================================================================

class ChannelExtractor(DimensionExtractor):
    """Channel extraction using synonym resolution.

    Target latency: 200-400ms.
    """

    VALID_CHANNELS = {"online", "in_store", "mobile"}

    def __init__(self):
        super().__init__("channel", 300)
        self.synonym_resolver = SynonymResolver()

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract channel using deterministic matching."""
        start_time = time.perf_counter()

        query_lower = input.query.lower()
        values = []

        # Check for channel mentions
        for channel in ["online", "in-store", "in store", "mobile", "in-person", "in person"]:
            if channel in query_lower:
                if channel in ["in-store", "in store", "in-person", "in person"]:
                    values.append("in_store")
                else:
                    values.append(channel)

        # Deduplicate and validate
        values = list(set(values))
        values = [v for v in values if v in self.VALID_CHANNELS]

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return DimensionExtractionResult(
            dimension_type="channel",
            values=values,
            confidence=0.9 if values else 0.0,
            alternatives=[],
            extraction_method="lookup",
            latency_ms=latency_ms,
            validation_status="valid" if values else "invalid",
        )


# ============================================================================
# Day of Week Extractor (Deterministic)
# ============================================================================

class DayOfWeekExtractor(DimensionExtractor):
    """Day of week extraction using deterministic parsing.

    Target latency: 100-200ms.
    """

    DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    def __init__(self):
        super().__init__("day_of_week", 150)

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract day of week using deterministic matching."""
        start_time = time.perf_counter()

        query_lower = input.query.lower()
        values = []

        for day in self.DAYS:
            if day in query_lower:
                values.append(day)

        # Check for "weekend" shorthand
        if "weekend" in query_lower:
            values.extend(["saturday", "sunday"])

        # Check for "weekday" shorthand
        if "weekday" in query_lower:
            values.extend(["monday", "tuesday", "wednesday", "thursday", "friday"])

        # Deduplicate
        values = list(set(values))

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return DimensionExtractionResult(
            dimension_type="day_of_week",
            values=values,
            confidence=0.9 if values else 0.0,
            alternatives=[],
            extraction_method="deterministic",
            latency_ms=latency_ms,
            validation_status="valid" if values else "invalid",
        )


# ============================================================================
# Brand Extractor (LLM + Fuzzy)
# ============================================================================

class BrandExtractor(DimensionExtractor):
    """Brand extraction using LLM and fuzzy matching.

    Target latency: 400-800ms.
    """

    PROMPT_TEMPLATE = """You are a data analyst extracting brand names from user queries.

Extract brand names from the query. Look for:
- Retailers: Walmart, Target, Costco, Amazon, Kroger, etc.
- Restaurants: Chipotle, McDonald's, Starbucks, etc.
- Brands: Nike, Apple, Samsung, etc.

Return a JSON array of brand names found in the query.
Example: ["Walmart", "Target"]

Query: {query}"""

    # Common brand aliases for fuzzy matching
    BRAND_ALIASES = {
        "walmart": "Walmart",
        "target": "Target",
        "tgt": "Target",
        "costco": "Costco",
        "amazon": "Amazon",
        "amzn": "Amazon",
        "kroger": "Kroger",
        "chipotle": "Chipotle",
        "mcdonalds": "McDonald's",
        "mcdonald's": "McDonald's",
        "starbucks": "Starbucks",
        "sbux": "Starbucks",
        "nike": "Nike",
        "apple": "Apple",
        "samsung": "Samsung",
    }

    def __init__(self):
        super().__init__("brand", 600)
        self.synonym_resolver = SynonymResolver()

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract brand values using LLM with fuzzy matching."""
        start_time = time.perf_counter()

        # First try deterministic brand alias lookup
        query_lower = input.query.lower()
        deterministic_brands = []

        for alias, brand in self.BRAND_ALIASES.items():
            if alias in query_lower:
                deterministic_brands.append(brand)

        if deterministic_brands:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return DimensionExtractionResult(
                dimension_type="brand",
                values=list(set(deterministic_brands)),
                confidence=0.95,
                alternatives=[],
                extraction_method="lookup",
                latency_ms=latency_ms,
                validation_status="valid",
            )

        # Fall back to LLM extraction
        return await self._llm_extract(input, self.PROMPT_TEMPLATE)


# ============================================================================
# Geography Extractor (LLM + Cached Lookups)
# ============================================================================

class GeographyExtractor(DimensionExtractor):
    """Geography extraction using LLM with cached lookups.

    Target latency: 50-150ms with cached lookups.
    """

    # State abbreviation to canonical name mapping
    STATE_ABBREV = {
        "al": "Alabama", "ak": "Alaska", "az": "Arizona", "ar": "Arkansas",
        "ca": "California", "co": "Colorado", "ct": "Connecticut", "de": "Delaware",
        "fl": "Florida", "ga": "Georgia", "hi": "Hawaii", "id": "Idaho",
        "il": "Illinois", "in": "Indiana", "ia": "Iowa", "ks": "Kansas",
        "ky": "Kentucky", "la": "Louisiana", "me": "Maine", "md": "Maryland",
        "ma": "Massachusetts", "mi": "Michigan", "mn": "Minnesota", "ms": "Mississippi",
        "mo": "Missouri", "mt": "Montana", "ne": "Nebraska", "nv": "Nevada",
        "nh": "New Hampshire", "nj": "New Jersey", "nm": "New Mexico", "ny": "New York",
        "nc": "North Carolina", "nd": "North Dakota", "oh": "Ohio", "ok": "Oklahoma",
        "or": "Oregon", "pa": "Pennsylvania", "ri": "Rhode Island", "sc": "South Carolina",
        "sd": "South Dakota", "tn": "Tennessee", "tx": "Texas", "ut": "Utah",
        "vt": "Vermont", "va": "Virginia", "wa": "Washington", "wv": "West Virginia",
        "wi": "Wisconsin", "wy": "Wyoming", "dc": "District of Columbia",
    }

    # State name to abbreviation
    STATE_NAME_TO_ABBREV = {v.lower(): k for k, v in STATE_ABBREV.items()}

    PROMPT_TEMPLATE = """You are a data analyst extracting geographic locations from user queries.

Extract geographic locations from the query. Look for:
- US States: California, Texas, New York, Florida, etc.
- State abbreviations: CA, TX, NY, FL, etc.
- Metro areas: New York City, Los Angeles, Chicago, etc.
- CBSA codes: if present

Return a JSON array of geographic identifiers.
Example: ["CA", "TX", "NY"]

Query: {query}"""

    def __init__(self):
        super().__init__("geography", 100)
        self._cache: Dict[str, List[str]] = {}

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract geography using deterministic + LLM approach."""
        start_time = time.perf_counter()

        query_lower = input.query.lower()
        values = []

        # Check cache first
        cache_key = query_lower[:50]  # Simple cache key
        if cache_key in self._cache:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return DimensionExtractionResult(
                dimension_type="geography",
                values=self._cache[cache_key],
                confidence=0.9,
                alternatives=[],
                extraction_method="lookup",
                latency_ms=latency_ms,
                validation_status="valid",
            )

        # Deterministic state abbreviation extraction
        for abbrev, name in self.STATE_ABBREV.items():
            if abbrev in query_lower or name.lower() in query_lower:
                values.append(abbrev.upper())

        # Check for metro areas
        metro_areas = {
            "new york": "NY", "los angeles": "CA", "chicago": "IL",
            "houston": "TX", "phoenix": "AZ", "philadelphia": "PA",
            "san antonio": "TX", "san diego": "CA", "dallas": "TX",
            "austin": "TX", "jacksonville": "FL", "fort worth": "TX",
            "columbus": "OH", "charlotte": "NC", "san francisco": "CA",
            "indianapolis": "IN", "seattle": "WA", "denver": "CO",
            "boston": "MA", "el paso": "TX", "detroit": "MI",
            "nashville": "TN", "portland": "OR", "memphis": "TN",
            "oklahoma city": "OK", "las vegas": "NV", "louisville": "KY",
            "baltimore": "MD", "milwaukee": "WI", "albuquerque": "NM",
            "tucson": "AZ", "fresno": "CA", "mesa": "AZ", "sacramento": "CA",
            "atlanta": "GA", "kansas city": "MO", "colorado springs": "CO",
            "miami": "FL", "raleigh": "NC", "omaha": "NE", "long beach": "CA",
            "virginia beach": "VA", "oakland": "CA", "minneapolis": "MN",
            "tampa": "FL", "arlington": "TX", "new orleans": "LA",
        }

        for area, state in metro_areas.items():
            if area in query_lower and state not in values:
                values.append(state)

        # Cache results
        if values:
            self._cache[cache_key] = values
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return DimensionExtractionResult(
                dimension_type="geography",
                values=values,
                confidence=0.9,
                alternatives=[],
                extraction_method="lookup",
                latency_ms=latency_ms,
                validation_status="valid",
            )

        # Fall back to LLM
        return await self._llm_extract(input, self.PROMPT_TEMPLATE)


# ============================================================================
# Category Extractor (LLM + Enum)
# ============================================================================

class CategoryExtractor(DimensionExtractor):
    """Category extraction using LLM with enum lookup.

    Target latency: 400-800ms.
    """

    PROMPT_TEMPLATE = """You are a data analyst extracting merchant categories from user queries.

Extract merchant categories from the query. Common categories include:
- Retail: general merchandise, grocery, electronics, apparel, home goods
- Dining: fast food, casual dining, coffee shops, QSR
- Travel: airlines, hotels, car rental
- Entertainment: streaming, gaming, movies
- Financial: banking, insurance, investments
- Healthcare: pharmacy, medical, dental
- Services: salons, auto repair, cleaning

Return a JSON array of category values found in the query.
Example: ["retail", "grocery"]

Query: {query}"""

    VALID_CATEGORIES = {
        "retail", "grocery", "electronics", "apparel", "home_goods",
        "fast_food", "casual_dining", "coffee_shops", "qsr",
        "airlines", "hotels", "car_rental",
        "streaming", "gaming", "movies",
        "banking", "insurance", "investments",
        "pharmacy", "medical", "dental",
        "salons", "auto_repair", "cleaning",
    }

    def __init__(self):
        super().__init__("merchant_category", 600)
        self.synonym_resolver = SynonymResolver()

    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        """Extract category using LLM."""

        def validate_cat(value: str) -> bool:
            return value in self.VALID_CATEGORIES

        return await self._llm_extract(input, self.PROMPT_TEMPLATE, validate_cat)
