"""Tests for FR-3.4: Synonym and Layman Term Handling.

This module tests the SynonymResolver class for mapping layman terms,
synonyms, and fuzzy matches to canonical dimension values.
"""

import pytest
from src.api.lookup import SynonymResolver, DIMENSION_ALIASES, CANONICAL_VALUES


class TestSynonymResolver:
    """Test cases for SynonymResolver class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = SynonymResolver()

    def test_synonym_resolver_resolves_known_aliases(self):
        """Test that known aliases resolve to correct canonical values."""
        # Test "young people" -> Gen Z (confidence 0.7) with Millennial as alternative
        result = self.resolver.resolve("generation", "young people")
        assert len(result) == 2
        assert result[0][0] == "gen_z"
        assert result[0][1] == 0.7
        assert result[1][0] == "millennial"
        assert result[1][1] == 0.6

        # Test "credit card" -> credit (confidence 0.8) with debit as alternative
        result = self.resolver.resolve("card_type", "credit card")
        assert len(result) == 2
        assert result[0][0] == "credit"
        assert result[0][1] == 0.8
        assert result[1][0] == "debit"
        assert result[1][1] == 0.3

        # Test "fancy" -> premium tier (not in our aliases, but tests fallback)
        # Note: "fancy" is not in aliases, it would need fuzzy match
        # Let's test a known alias
        result = self.resolver.resolve("generation", "baby boomers")
        assert result[0][0] == "boomer"
        assert result[0][1] == 0.9

    def test_synonym_resolver_fuzzy_match_returns_empty_for_unknown_dimension(self):
        """Test that fuzzy match returns empty list for unknown dimension."""
        result = self.resolver.fuzzy_match("unknown_dimension", "some value")
        assert result == []

    def test_synonym_resolver_fuzzy_match_generation(self):
        """Test fuzzy matching for generation dimension."""
        # Test fuzzy match for "gen z" to "gen_z"
        result = self.resolver.fuzzy_match("generation", "gen z")
        assert len(result) > 0
        assert result[0][0] == "gen_z"
        assert result[0][1] >= 0.6

    def test_synonym_resolver_fuzzy_match_income_band(self):
        """Test fuzzy matching for income_band dimension."""
        # Test fuzzy match for "band 6" to "band_6"
        result = self.resolver.fuzzy_match("income_band", "band 6")
        assert len(result) > 0
        assert result[0][0] == "band_6"
        assert result[0][1] >= 0.6

    def test_synonym_resolver_fuzzy_match_card_type(self):
        """Test fuzzy matching for card_type dimension."""
        # Test fuzzy match for "credit" to "credit"
        result = self.resolver.fuzzy_match("card_type", "credit")
        assert len(result) > 0
        assert result[0][0] == "credit"
        assert result[0][1] == 1.0

    def test_synonym_resolver_fuzzy_match_channel(self):
        """Test fuzzy matching for channel dimension."""
        # Test fuzzy match for "online" to "online"
        result = self.resolver.fuzzy_match("channel", "online")
        assert len(result) > 0
        assert result[0][0] == "online"
        assert result[0][1] == 1.0

    def test_fuzzy_match_brand_exact_match(self):
        """Test fuzzy brand matching with exact match."""
        brands = ["Apple", "Samsung", "Google", "Microsoft"]
        result = self.resolver.fuzzy_match_brand("Apple", brands)
        assert result[0][0] == "Apple"
        assert result[0][1] == 1.0

    def test_fuzzy_match_brand_partial_match(self):
        """Test fuzzy brand matching with partial match."""
        brands = ["Apple", "Samsung", "Google", "Microsoft"]
        # "appl" should match "Apple"
        result = self.resolver.fuzzy_match_brand("appl", brands)
        assert len(result) > 0
        assert result[0][0] == "Apple"
        assert result[0][1] >= 0.6

    def test_fuzzy_match_brand_no_match(self):
        """Test fuzzy brand matching with no match."""
        brands = ["Apple", "Samsung", "Google", "Microsoft"]
        # "xyz123" should not match any brand above threshold
        result = self.resolver.fuzzy_match_brand("xyz123", brands)
        # Should either be empty or have no matches above 0.6
        matched_brands = [r for r in result if r[1] >= 0.6]
        assert len(matched_brands) == 0


class TestDimensionAliases:
    """Test cases for DIMENSION_ALIASES constant."""

    def test_aliases_contain_expected_dimensions(self):
        """Test that aliases contain all expected dimensions."""
        expected_dimensions = ["generation", "income_band", "card_type", "payment_network", "channel"]
        for dim in expected_dimensions:
            assert dim in DIMENSION_ALIASES

    def test_aliases_have_valid_confidence_scores(self):
        """Test that all alias confidence scores are between 0 and 1."""
        for dim_aliases in DIMENSION_ALIASES.values():
            for alias, candidates in dim_aliases.items():
                for canonical, confidence in candidates:
                    assert 0 <= confidence <= 1, f"Confidence for {alias} -> {canonical} is out of range"


class TestCanonicalValues:
    """Test cases for CANONICAL_VALUES constant."""

    def test_canonical_values_contain_expected_dimensions(self):
        """Test that canonical values contain all expected dimensions."""
        expected_dimensions = ["card_type", "payment_network", "channel", "day_of_week", "generation", "income_band", "aggregation_level"]
        for dim in expected_dimensions:
            assert dim in CANONICAL_VALUES

    def test_canonical_values_are_lists(self):
        """Test that all canonical value entries are lists."""
        for dim, values in CANONICAL_VALUES.items():
            assert isinstance(values, list), f"{dim} values should be a list"
            assert len(values) > 0, f"{dim} should have at least one canonical value"
