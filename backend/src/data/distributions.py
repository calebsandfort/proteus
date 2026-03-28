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
INCOME_MULTIPLIERS: Dict[int, float] = {
    1: 0.6,   # <$25K
    2: 0.8,
    3: 1.0,
    4: 1.2,
    5: 1.4,
    6: 1.7,   # $150K+
}


def generate_transaction_amount(category_tier: str, income_band: int) -> float:
    """Generate log-normal transaction amount with income multiplier.

    Args:
        category_tier: The category tier for the transaction.
            Must be one of: 'essential', 'value', 'walmart', 'mid_tier', 'premium', 'luxury', 'dining', 'fast_food'.
        income_band: The income band (1-6) of the consumer.
            1 = <$25K, 2 = $25K-$50K, 3 = $50K-$75K, 4 = $75K-$100K,
            5 = $100K-$150K, 6 = $150K+

    Returns:
        The transaction amount as a positive float.

    Raises:
        ValueError: If category_tier is not recognized or income_band is not 1-6.
    """
    if category_tier not in CATEGORY_PARAMS:
        raise ValueError(
            f"Unknown category tier: {category_tier}. "
            f"Must be one of: {list(CATEGORY_PARAMS.keys())}"
        )

    if income_band not in INCOME_MULTIPLIERS:
        raise ValueError(
            f"Invalid income band: {income_band}. Must be 1-6."
        )

    mu, sigma = CATEGORY_PARAMS[category_tier]

    # Generate log-normal sample: exp(N(mu, sigma))
    base_amount = np.random.lognormal(mean=mu, sigma=sigma)

    # Apply income multiplier
    multiplier = INCOME_MULTIPLIERS[income_band]
    final_amount = base_amount * multiplier

    return float(final_amount)


def sample_income_band(probabilities: List[float]) -> int:
    """Sample income band from given probabilities.

    Args:
        probabilities: A list of 6 probabilities corresponding to income bands 1-6.
            The probabilities should sum to 1.0 (will be normalized if not).

    Returns:
        The sampled income band (1-6) as an integer.

    Raises:
        ValueError: If the length of probabilities is not 6.
        ValueError: If any probability is negative.
    """
    if len(probabilities) != 6:
        raise ValueError(
            f"Expected 6 probabilities, got {len(probabilities)}"
        )

    for p in probabilities:
        if p < 0:
            raise ValueError(
                f"Probabilities cannot be negative, got {p}"
            )

    # Normalize probabilities
    probs = np.array(probabilities)
    probs = probs / probs.sum()

    # Sample from multinomial distribution
    # np.random.choice with replace=True gives us discrete sampling
    bands = np.arange(1, 7)  # [1, 2, 3, 4, 5, 6]
    sampled_idx = np.random.choice(a=6, p=probs)

    return int(bands[sampled_idx])


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
