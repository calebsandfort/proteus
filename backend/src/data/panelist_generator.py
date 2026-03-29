"""Panelist generation for synthetic data generator.

This module implements FR-6.9: Panel Data Structure for consumer panel
generation with demographic attributes.

Each panelist has:
- Persistent ID
- Income band
- Generation
- Geography
- Panel start date
- Panel weight

Functions:
    Panelist: Dataclass representing a panelist with demographic attributes.
    generate_panelists: Generate a list of panelists with demographic attributes.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional
import uuid

import numpy as np

from src.data.distributions import sample_income_band, sample_panel_weight


# Default distributions for panelist demographics
DEFAULT_GEOGRAPHY_DISTRIBUTION: Dict[str, float] = {
    "1": 0.18,   # Northeast
    "2": 0.22,   # Midwest
    "3": 0.38,   # South
    "4": 0.22,   # West
}

DEFAULT_GENERATION_DISTRIBUTION: Dict[str, float] = {
    "gen_z": 0.12,
    "millennial": 0.26,
    "gen_x": 0.30,
    "baby_boomer": 0.32,
}

DEFAULT_INCOME_DISTRIBUTION: List[float] = [
    0.12,  # under_25k: <$25K
    0.18,  # 25k_50k: $25K-$50K
    0.22,  # 50k_75k: $50K-$75K
    0.20,  # 75k_100k: $75K-$100K
    0.18,  # 100k_150k: $100K-$150K
    0.07,  # 150k_200k: $150K-$200K
    0.03,  # over_200k: $200K+
]


@dataclass
class Panelist:
    """Represents a consumer panelist with demographic attributes.

    Attributes:
        id: Unique persistent identifier for the panelist.
        income_band_id: Income band (1-6).
            1 = <$25K, 2 = $25K-$50K, 3 = $50K-$75K,
            4 = $75K-$100K, 5 = $100K-$150K, 6 = $150K+
        generation_id: Generation identifier ('gen_z', 'millennial', 'gen_x', 'boomer').
        geography_id: Geographic region identifier (1-4).
            1 = Northeast, 2 = Midwest, 3 = South, 4 = West
        panel_start_date: Date the panelist joined the panel.
        panel_weight: Statistical weight for panel representativeness.
    """
    id: str
    income_band_id: str
    generation_id: str
    geography_id: int
    panel_start_date: date
    panel_weight: float


def generate_panelists(
    count: int,
    seed: int = 42,
    geography_distribution: Optional[Dict[str, float]] = None,
    generation_distribution: Optional[Dict[str, float]] = None,
    income_distribution: Optional[List[float]] = None,
) -> List[Panelist]:
    """Generate panelists with demographic attributes.

    Args:
        count: Number of panelists to generate.
        seed: Random seed for reproducibility.
        geography_distribution: Dictionary mapping geography IDs to probabilities.
            Defaults to US census regional distribution.
        generation_distribution: Dictionary mapping generation IDs to probabilities.
            Defaults to approximate US generational distribution.
        income_distribution: List of 6 probabilities for income bands 1-6.
            Defaults to approximate US income distribution.

    Returns:
        List of Panelist objects with demographic attributes.

    Raises:
        ValueError: If count is negative or distributions are invalid.
    """
    if count < 0:
        raise ValueError(f"Count must be non-negative, got {count}")

    # Set random seed for reproducibility
    np.random.seed(seed)

    # Use default distributions if not provided
    geo_dist = geography_distribution or DEFAULT_GEOGRAPHY_DISTRIBUTION
    gen_dist = generation_distribution or DEFAULT_GENERATION_DISTRIBUTION
    inc_dist = income_distribution or DEFAULT_INCOME_DISTRIBUTION

    # Validate income distribution
    if len(inc_dist) != 7:
        raise ValueError(f"Income distribution must have 7 elements, got {len(inc_dist)}")

    if sum(inc_dist) <= 0:
        raise ValueError("Income distribution must sum to positive value")

    panelists = []

    # Convert geography distribution to lists for numpy
    geo_ids = list(geo_dist.keys())
    geo_probs = list(geo_dist.values())
    geo_probs = np.array(geo_probs) / sum(geo_probs)

    # Convert generation distribution to lists for numpy
    gen_ids = list(gen_dist.keys())
    gen_probs = list(gen_dist.values())
    gen_probs = np.array(gen_probs) / sum(gen_probs)

    for _ in range(count):
        # Sample demographics
        income_band = sample_income_band(inc_dist)

        selected_geo_idx = np.random.choice(len(geo_ids), p=geo_probs)
        geography_id = int(geo_ids[selected_geo_idx])

        selected_gen_idx = np.random.choice(len(gen_ids), p=gen_probs)
        generation_id = gen_ids[selected_gen_idx]

        # Generate panel start date (random date in 2020-2024)
        days_offset = np.random.randint(0, 365 * 5)  # 5 years of potential start dates
        panel_start_date = date(2020, 1, 1) + date.resolution * days_offset

        # Generate panel weight
        panel_weight = sample_panel_weight(geo_dist, gen_dist)

        # Generate unique ID
        panelist_id = str(uuid.uuid4())

        panelists.append(Panelist(
            id=panelist_id,
            income_band_id=income_band,
            generation_id=generation_id,
            geography_id=geography_id,
            panel_start_date=panel_start_date,
            panel_weight=panel_weight,
        ))

    return panelists
