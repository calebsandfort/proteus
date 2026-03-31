"""FR-3.4: Synonym and Layman Term Handling.

This module provides the SynonymResolver for mapping layman terms,
synonyms, and fuzzy matches to canonical dimension values.

Key Features:
- Lookup table for known aliases per dimension
- Fuzzy matching fallback against enumeration values
- Confidence scoring for matches
- Brand alias resolution with fuzzy matching
"""

from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher

# Fuzzy matching threshold (per FR-3.4)
DEFAULT_FUZZY_THRESHOLD: float = 0.6

# Dimension alias maps per FR-3.4
DIMENSION_ALIASES: Dict[str, Dict[str, List[Tuple[str, float]]]] = {
    "generation": {
        "young people": [("gen_z", 0.7), ("millennial", 0.6)],
        "old": [("boomer", 0.8), ("silent", 0.5)],
        "teenagers": [("gen_z", 0.8)],
        "seniors": [("boomer", 0.7), ("silent", 0.6)],
        "baby boomers": [("boomer", 0.9)],
        "gen x": [("gen_x", 0.9)],
        "millennials": [("millennial", 0.9)],
    },
    "income_band": {
        "wealthy": [("band_6", 0.9), ("band_5", 0.6)],
        "affluent": [("band_6", 0.8), ("band_5", 0.7)],
        "low income": [("band_1", 0.8), ("band_2", 0.6)],
        "middle class": [("band_3", 0.8), ("band_4", 0.5)],
        "upper middle class": [("band_4", 0.8), ("band_5", 0.5)],
    },
    "card_type": {
        "credit card": [("credit", 0.8), ("debit", 0.3)],
        "debit card": [("debit", 0.8), ("credit", 0.2)],
        "prepaid card": [("prepaid", 0.9)],
    },
    "payment_network": {
        "amex": [("amex", 0.9)],
        "american express": [("amex", 0.9)],
    },
    "channel": {
        "online": [("online", 0.9)],
        "in-store": [("in_store", 0.9)],
        "in store": [("in_store", 0.9)],
        "mobile": [("mobile", 0.9)],
    },
}

# Canonical value normalization
CANONICAL_VALUES: Dict[str, List[str]] = {
    "card_type": ["credit", "debit", "prepaid", "corporate"],
    "payment_network": ["visa", "mastercard", "amex", "discover"],
    "channel": ["online", "in_store", "mobile"],
    "day_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    "generation": ["gen_z", "millennial", "gen_x", "boomer", "silent"],
    "income_band": ["band_1", "band_2", "band_3", "band_4", "band_5", "band_6"],
    "aggregation_level": ["hourly", "daily", "weekly", "monthly", "quarterly", "annual", "auto"],
}


class SynonymResolver:
    """Resolves synonyms and layman terms to canonical dimension values.

    FR-3.4: Uses LLM + lookup table hybrid for dimension value mapping.

    The resolver first checks its internal alias lookup table, then
    falls back to fuzzy matching against canonical enumeration values.

    Attributes:
        aliases: Dict of dimension-specific alias maps
        canonical_values: Dict of valid canonical values per dimension
    """

    def __init__(self):
        self.aliases = DIMENSION_ALIASES
        self.canonical_values = CANONICAL_VALUES

    def resolve(self, dimension: str, value: str) -> List[Tuple[str, float]]:
        """Resolve a value to canonical dimension values with confidence.

        Args:
            dimension: Dimension type (e.g., "generation", "income_band")
            value: Value to resolve (e.g., "young people", "wealthy")

        Returns:
            List of (canonical_value, confidence) tuples, sorted by confidence descending.
            Empty list if no match found.
        """
        lower_value = value.lower().strip()

        # First check lookup table
        if dimension in self.aliases:
            dim_aliases = self.aliases[dimension]
            if lower_value in dim_aliases:
                return dim_aliases[lower_value].copy()

        # Fall back to fuzzy matching against canonical values
        return self.fuzzy_match(dimension, value)

    def fuzzy_match(self, dimension: str, value: str) -> List[Tuple[str, float]]:
        """Fuzzy match a value against canonical values for a dimension.

        Uses SequenceMatcher for fuzzy matching with confidence scoring.

        Args:
            dimension: Dimension type
            value: Value to match

        Returns:
            List of (canonical_value, confidence) tuples sorted by confidence.
            Returns empty list if no matches above 0.6 threshold.
        """
        if dimension not in self.canonical_values:
            return []

        canonicals = self.canonical_values[dimension]
        results = []
        lower_value = value.lower().strip()

        for canonical in canonicals:
            # Exact match
            if lower_value == canonical.lower():
                results.append((canonical, 1.0))
                continue

            # Fuzzy match using SequenceMatcher
            ratio = SequenceMatcher(None, lower_value, canonical.lower()).ratio()
            if ratio >= DEFAULT_FUZZY_THRESHOLD:
                results.append((canonical, ratio))

        # Sort by confidence descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def fuzzy_match_brand(self, value: str, brand_list: List[str]) -> List[Tuple[str, float]]:
        """Fuzzy match a brand name against a list of known brands.

        Args:
            value: Brand name to match
            brand_list: List of known brand names

        Returns:
            List of (brand, confidence) tuples sorted by confidence.
        """
        results = []
        lower_value = value.lower().strip()

        for brand in brand_list:
            lower_brand = brand.lower()

            # Exact match
            if lower_value == lower_brand:
                results.append((brand, 1.0))
                continue

            # Substring match - high confidence
            if lower_value in lower_brand or lower_brand in lower_value:
                results.append((brand, 0.85))
                continue

            # Fuzzy match
            ratio = SequenceMatcher(None, lower_value, lower_brand).ratio()
            if ratio >= DEFAULT_FUZZY_THRESHOLD:
                results.append((brand, ratio))

        results.sort(key=lambda x: x[1], reverse=True)
        return results
