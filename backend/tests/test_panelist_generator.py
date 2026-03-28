"""Tests for FR-6.9: Panelist Generation.

This module tests panelist generation with demographic attributes
for the synthetic data generator.
"""

import numpy as np
import pytest
from datetime import date, timedelta
from typing import Dict, List


# Test constants
SEED = 42
DEFAULT_PANELIST_COUNT = 100


class TestFr69PanelistStructure:
    """FR-6.9: Panelist data structure has required fields."""

    def test_fr_6_9_panelist_has_required_fields(self) -> None:
        """Each panelist has: id, income_band_id, generation_id, geography_id, panel_start_date, panel_weight."""
        from src.data.panelist_generator import Panelist, generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=1, seed=SEED)

        assert len(panelists) == 1
        panelist = panelists[0]

        # Check all required fields exist
        assert hasattr(panelist, 'id')
        assert hasattr(panelist, 'income_band_id')
        assert hasattr(panelist, 'generation_id')
        assert hasattr(panelist, 'geography_id')
        assert hasattr(panelist, 'panel_start_date')
        assert hasattr(panelist, 'panel_weight')

    def test_fr_6_9_panelist_id_is_unique(self) -> None:
        """Each panelist has a unique persistent ID."""
        from src.data.panelist_generator import Panelist, generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=100, seed=SEED)

        ids = [p.id for p in panelists]
        assert len(ids) == len(set(ids)), "All panelist IDs should be unique"

    def test_fr_6_9_panelist_id_is_string(self) -> None:
        """Panelist ID is a string type."""
        from src.data.panelist_generator import Panelist, generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=10, seed=SEED)

        for panelist in panelists:
            assert isinstance(panelist.id, str), f"Panelist ID should be string, got {type(panelist.id)}"


class TestFr69PanelistDemographics:
    """FR-6.9: Panelist demographic attributes."""

    def test_fr_6_9_income_band_id_range(self) -> None:
        """Income band ID is in valid range 1-6."""
        from src.data.panelist_generator import generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=1000, seed=SEED)

        for panelist in panelists:
            assert 1 <= panelist.income_band_id <= 6, \
                f"Income band {panelist.income_band_id} outside valid range 1-6"

    def test_fr_6_9_generation_id_valid(self) -> None:
        """Generation ID is valid generation identifier."""
        from src.data.panelist_generator import generate_panelists
        from src.data.seasonal_patterns import VALID_GENERATIONS

        np.random.seed(SEED)
        panelists = generate_panelists(count=1000, seed=SEED)

        for panelist in panelists:
            assert panelist.generation_id in VALID_GENERATIONS, \
                f"Generation {panelist.generation_id} not in {VALID_GENERATIONS}"

    def test_fr_6_9_geography_id_valid(self) -> None:
        """Geography ID is valid integer."""
        from src.data.panelist_generator import generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=1000, seed=SEED)

        for panelist in panelists:
            assert isinstance(panelist.geography_id, int), \
                f"Geography ID should be int, got {type(panelist.geography_id)}"
            assert panelist.geography_id >= 0, \
                f"Geography ID should be non-negative, got {panelist.geography_id}"

    def test_fr_6_9_panel_weight_positive(self) -> None:
        """Panel weight is positive value."""
        from src.data.panelist_generator import generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=1000, seed=SEED)

        for panelist in panelists:
            assert panelist.panel_weight > 0, \
                f"Panel weight should be positive, got {panelist.panel_weight}"

    def test_fr_6_9_panel_weight_reasonable_range(self) -> None:
        """Panel weight is in reasonable range (0.1 to 20)."""
        from src.data.panelist_generator import generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=1000, seed=SEED)

        for panelist in panelists:
            assert 0.1 <= panelist.panel_weight <= 20, \
                f"Panel weight {panelist.panel_weight} outside reasonable range"


class TestFr69PanelistDistribution:
    """FR-6.9: Panelist distribution follows specifications."""

    def test_fr_6_9_generates_requested_count(self) -> None:
        """generate_panelists returns exactly the requested count."""
        from src.data.panelist_generator import generate_panelists

        np.random.seed(SEED)
        counts = [1, 10, 100, 500]
        for count in counts:
            panelists = generate_panelists(count=count, seed=SEED)
            assert len(panelists) == count, f"Expected {count} panelists, got {len(panelists)}"

    def test_fr_6_9_income_distribution_custom(self) -> None:
        """Custom income distribution is respected."""
        from src.data.panelist_generator import generate_panelists

        # All panelists in band 5
        income_distribution = [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]

        np.random.seed(SEED)
        panelists = generate_panelists(
            count=100,
            seed=SEED,
            income_distribution=income_distribution
        )

        for panelist in panelists:
            assert panelist.income_band_id == 5, \
                f"Expected income band 5, got {panelist.income_band_id}"

    def test_fr_6_9_geography_distribution_custom(self) -> None:
        """Custom geography distribution is respected."""
        from src.data.panelist_generator import generate_panelists

        # All panelists in geography 1
        geography_distribution = {"1": 1.0}

        np.random.seed(SEED)
        panelists = generate_panelists(
            count=50,
            seed=SEED,
            geography_distribution=geography_distribution
        )

        for panelist in panelists:
            assert panelist.geography_id == 1, \
                f"Expected geography 1, got {panelist.geography_id}"

    def test_fr_6_9_generation_distribution_custom(self) -> None:
        """Custom generation distribution is respected."""
        from src.data.panelist_generator import generate_panelists

        # All panelists are millennials
        generation_distribution = {"gen_z": 0.0, "millennial": 1.0, "gen_x": 0.0, "boomer": 0.0}

        np.random.seed(SEED)
        panelists = generate_panelists(
            count=50,
            seed=SEED,
            generation_distribution=generation_distribution
        )

        for panelist in panelists:
            assert panelist.generation_id == "millennial", \
                f"Expected millennial, got {panelist.generation_id}"


class TestFr69PanelistDateRange:
    """FR-6.9: Panel start date is within expected range."""

    def test_fr_6_9_panel_start_date_type(self) -> None:
        """Panel start date is a date object."""
        from src.data.panelist_generator import generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=10, seed=SEED)

        for panelist in panelists:
            assert isinstance(panelist.panel_start_date, date), \
                f"Panel start date should be date, got {type(panelist.panel_start_date)}"

    def test_fr_6_9_panel_start_date_reasonable(self) -> None:
        """Panel start date is within reasonable range (2020-2025)."""
        from src.data.panelist_generator import generate_panelists

        np.random.seed(SEED)
        panelists = generate_panelists(count=100, seed=SEED)

        min_date = date(2020, 1, 1)
        max_date = date(2025, 12, 31)

        for panelist in panelists:
            assert min_date <= panelist.panel_start_date <= max_date, \
                f"Panel start date {panelist.panel_start_date} outside range [{min_date}, {max_date}]"


class TestFr69Reproducibility:
    """FR-6.9: Panelist generation is reproducible with seed."""

    def test_fr_6_9_same_seed_same_panelists(self) -> None:
        """Same seed produces same panelist list."""
        from src.data.panelist_generator import generate_panelists

        panelists1 = generate_panelists(count=100, seed=42)
        panelists2 = generate_panelists(count=100, seed=42)

        assert len(panelists1) == len(panelists2)

        for p1, p2 in zip(panelists1, panelists2):
            assert p1.id == p2.id
            assert p1.income_band_id == p2.income_band_id
            assert p1.generation_id == p2.generation_id
            assert p1.geography_id == p2.geography_id
            assert p1.panel_start_date == p2.panel_start_date
            assert p1.panel_weight == p2.panel_weight

    def test_fr_6_9_different_seed_different_panelists(self) -> None:
        """Different seeds produce different panelist lists."""
        from src.data.panelist_generator import generate_panelists

        panelists1 = generate_panelists(count=100, seed=42)
        panelists2 = generate_panelists(count=100, seed=123)

        # IDs should be different
        ids1 = set(p.id for p in panelists1)
        ids2 = set(p.id for p in panelists2)

        assert ids1 != ids2, "Different seeds should produce different panelists"
