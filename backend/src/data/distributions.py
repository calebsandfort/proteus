"""Statistical distributions for synthetic data generation.

This module implements FR-6.6: Statistical Distributions for transaction amounts,
income band sampling, and panel weight calibration.

Functions:
    generate_transaction_amount: Generate log-normal transaction amount with income multiplier.
    sample_income_band: Sample income band from given probabilities.
    sample_panel_weight: Generate panel weight calibrated to US demographics.
"""

from typing import Dict, List

import numpy as np


# FR-6.6: Category-specific log-normal parameters (mu, sigma)
CATEGORY_PARAMS: Dict[str, tuple[float, float]] = {
    'essential': (3.0, 0.8),
    'value': (2.7, 0.7),    # Below essential - Walmart/value tier
    'walmart': (2.5, 0.6),  # Lowest tier
    'mid_tier': (3.5, 1.0),
    'premium': (4.2, 1.2),
    'luxury': (4.5, 1.3),  # Above premium
    'dining': (3.2, 0.9),
    'fast_food': (2.2, 0.6),
}

# FR-6.6: Income multipliers by band
INCOME_MULTIPLIERS: Dict[str, float] = {
    'under_25k': 0.6,
    '25k_50k': 0.8,
    '50k_75k': 1.0,
    '75k_100k': 1.2,
    '100k_150k': 1.4,
    '150k_200k': 1.55,
    'over_200k': 1.7,
}


def generate_transaction_amount(category_tier: str, income_band: str) -> float:
    """Generate log-normal transaction amount with income multiplier.

    Args:
        category_tier: The category tier for the transaction.
            Must be one of: 'essential', 'value', 'walmart', 'mid_tier', 'premium', 'luxury', 'dining', 'fast_food'.
        income_band: The income band ID of the consumer.
            Must be one of: 'under_25k', '25k_50k', '50k_75k', '75k_100k',
            '100k_150k', '150k_200k', 'over_200k'.

    Returns:
        The transaction amount as a positive float.

    Raises:
        ValueError: If category_tier is not recognized or income_band is not a valid ID.
    """
    if category_tier not in CATEGORY_PARAMS:
        raise ValueError(
            f"Unknown category tier: {category_tier}. "
            f"Must be one of: {list(CATEGORY_PARAMS.keys())}"
        )

    if income_band not in INCOME_MULTIPLIERS:
        raise ValueError(
            f"Invalid income band: {income_band}. Must be one of: {list(INCOME_MULTIPLIERS.keys())}"
        )

    mu, sigma = CATEGORY_PARAMS[category_tier]

    # Generate log-normal sample: exp(N(mu, sigma))
    base_amount = np.random.lognormal(mean=mu, sigma=sigma)

    # Apply income multiplier
    multiplier = INCOME_MULTIPLIERS[income_band]
    final_amount = base_amount * multiplier

    return float(final_amount)


INCOME_BAND_IDS = [
    'under_25k', '25k_50k', '50k_75k', '75k_100k', '100k_150k', '150k_200k', 'over_200k',
]


def sample_income_band(probabilities: List[float]) -> str:
    """Sample income band from given probabilities.

    Args:
        probabilities: A list of 7 probabilities corresponding to income bands
            ['under_25k', '25k_50k', '50k_75k', '75k_100k', '100k_150k', '150k_200k', 'over_200k'].
            The probabilities should sum to 1.0 (will be normalized if not).

    Returns:
        The sampled income band ID as a string.

    Raises:
        ValueError: If the length of probabilities is not 7.
        ValueError: If any probability is negative.
    """
    if len(probabilities) != 7:
        raise ValueError(
            f"Expected 7 probabilities, got {len(probabilities)}"
        )

    for p in probabilities:
        if p < 0:
            raise ValueError(
                f"Probabilities cannot be negative, got {p}"
            )

    # Normalize probabilities
    probs = np.array(probabilities)
    probs = probs / probs.sum()

    sampled_idx = np.random.choice(a=7, p=probs)

    return INCOME_BAND_IDS[sampled_idx]


def sample_panel_weight(
    geography_weights: Dict[str, float],
    generation_weights: Dict[str, float]
) -> float:
    """Generate panel weight calibrated to US demographics.

    Combines geography and generation weights to produce a panel weight
    that makes the panel representative of US consumer demographics.

    Args:
        geography_weights: Dictionary mapping geography names to their weights.
            Example: {'northeast': 0.2, 'midwest': 0.25, 'south': 0.35, 'west': 0.2}
        generation_weights: Dictionary mapping generation names to their weights.
            Example: {'gen_z': 0.15, 'millennial': 0.25, 'gen_x': 0.3, 'boomer': 0.3}

    Returns:
        The panel weight as a positive float.

    Raises:
        ValueError: If either weight dictionary is empty.
    """
    if not geography_weights:
        raise ValueError("Geography weights cannot be empty")

    if not generation_weights:
        raise ValueError("Generation weights cannot be empty")

    # Sample geography and generation
    geo_names = list(geography_weights.keys())
    geo_probs = np.array(list(geography_weights.values()))
    geo_probs = geo_probs / geo_probs.sum()

    gen_names = list(generation_weights.keys())
    gen_probs = np.array(list(generation_weights.values()))
    gen_probs = gen_probs / gen_probs.sum()

    selected_geo = np.random.choice(a=len(geo_names), p=geo_probs)
    selected_gen = np.random.choice(a=len(gen_names), p=gen_probs)

    # Combine weights: product of selected geography and generation weights
    # This ensures the panel is representative across the full cross-section
    geo_weight = geography_weights[geo_names[selected_geo]]
    gen_weight = generation_weights[gen_names[selected_gen]]

    # Use log-normal to add natural variation while maintaining calibration
    # Base weight is product of proportions, with log-normal variation
    base_weight = geo_weight * gen_weight * 100  # Scale up for reasonable values

    # Add log-normal variation (sigma=0.3 for moderate variation)
    variation = np.random.lognormal(mean=0, sigma=0.3)

    final_weight = base_weight * variation

    return float(final_weight)
