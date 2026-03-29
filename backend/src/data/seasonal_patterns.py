"""Seasonal patterns for synthetic data generation.

This module implements FR-6.7: Embedded Spending Patterns including:
- Holiday Season (Q4) spike with December 15-24 peak
- January normalization
- Back-to-School (Aug-Sep) patterns
- Weekend vs. Weekday patterns
- Generational preferences
- Income-brand correlation

Functions:
    apply_seasonal_adjustment: Apply Q4 spike, January normalization, back-to-school, weekend patterns.
    get_generation_preference: Get spending multiplier for generation/category combination.
    get_income_brand_preference: Get brand preference weight for income band and brand tier.
    calculate_brand_income_correlation: Calculate Pearson correlation for brand preference vs income.
"""

from datetime import datetime
from typing import Dict, Literal

import numpy as np


# Generation IDs
GEN_Z = 'gen_z'
MILLENNIAL = 'millennial'
GEN_X = 'gen_x'
BOOMER = 'baby_boomer'

# Brand tiers
PREMIUM = 'premium'
LUXURY = 'luxury'
MID_TIER = 'mid_tier'
VALUE = 'value'
WALMART = 'walmart'

# Valid values
VALID_GENERATIONS = {GEN_Z, MILLENNIAL, GEN_X, BOOMER}
VALID_BRAND_TIERS = {PREMIUM, LUXURY, MID_TIER, VALUE, WALMART}

# Categories
RETAIL = 'retail'
GROCERY = 'grocery'
DINING = 'dining'
APPAREL = 'apparel'
HEALTHCARE = 'healthcare'
TRAVEL = 'travel'
HOME_IMPROVEMENT = 'home_improvement'
SCHOOL = 'school'

VALID_CATEGORIES = {RETAIL, GROCERY, DINING, APPAREL, HEALTHCARE, TRAVEL, HOME_IMPROVEMENT, SCHOOL}

# Valid income band IDs (ordered low to high)
INCOME_BAND_IDS = [
    'under_25k', '25k_50k', '50k_75k', '75k_100k', '100k_150k', '150k_200k', 'over_200k',
]


# =============================================================================
# Q4 Holiday Season Constants
# =============================================================================

# November-December retail volume increase: 25-40%
Q4_NOV_DEC_MIN = 1.25
Q4_NOV_DEC_MAX = 1.40

# December 15-24 peak: 60-100% increase vs prior-week baseline
Q4_PEAK_MIN = 1.60
Q4_PEAK_MAX = 2.00
Q4_PEAK_START_DAY = 15
Q4_PEAK_END_DAY = 24


# =============================================================================
# January Normalization Constants
# =============================================================================

# January: -15-25% vs Q4 average (multiplier 0.75-0.85)
JANUARY_MIN = 0.75
JANUARY_MAX = 0.85


# =============================================================================
# Back-to-School Constants (Aug-Sep)
# =============================================================================

# School categories increase 20-35% in Aug-Sep
BACK_TO_SCHOOL_MIN = 1.20
BACK_TO_SCHOOL_MAX = 1.35
BACK_TO_SCHOOL_MONTHS = {8, 9}  # August, September


# =============================================================================
# Weekend vs Weekday Constants
# =============================================================================

# Saturday vs Monday: +30-35%
WEEKEND_SAT_MIN = 1.30
WEEKEND_SAT_MAX = 1.35
# Sunday also elevated
WEEKEND_SUN_MIN = 1.20


# =============================================================================
# Generational Preference Multipliers
# =============================================================================

# Gen Z multipliers
GEN_Z_DINING = 1.22
GEN_Z_APPAREL = 1.16
GEN_Z_ONLINE = 1.65  # 65% high online preference

# Millennials multipliers
MILLENNIAL_GROCERY = 1.18
MILLENNIAL_HOME_IMPROVEMENT = 1.12

# Boomers multipliers
BOOMER_HEALTHCARE = 1.28
BOOMER_TRAVEL = 1.14
BOOMER_INSTORE = 1.75  # 75% in-store preference


# =============================================================================
# Income-Brand Correlation Constants
# =============================================================================

# High-income ($150K+, band 6) brand preferences
HIGH_INCOME_PREMIUM = (0.70, 0.80)
HIGH_INCOME_LUXURY = (0.55, 0.70)
HIGH_INCOME_MID_TIER = (0.15, 0.25)
HIGH_INCOME_VALUE = (0.00, 0.05)
HIGH_INCOME_WALMART = 0.02  # <2%

# Pearson correlation coefficients for premium/luxury brands
PREMIUM_PEARSON_MIN = 0.45
PREMIUM_PEARSON_MAX = 0.60
LUXURY_PEARSON_MIN = 0.55
LUXURY_PEARSON_MAX = 0.70


# =============================================================================
# Generation-Category Preference Tables
# =============================================================================

GENERATION_CATEGORY_PREFERENCES: Dict[str, Dict[str, float]] = {
    GEN_Z: {
        DINING: GEN_Z_DINING,
        APPAREL: GEN_Z_APPAREL,
        RETAIL: 1.10,  # General retail preference
        GROCERY: 0.95,  # Less grocery shopping
        HEALTHCARE: 0.90,
        TRAVEL: 1.05,
        HOME_IMPROVEMENT: 0.85,
        SCHOOL: 1.15,
    },
    MILLENNIAL: {
        GROCERY: MILLENNIAL_GROCERY,
        HOME_IMPROVEMENT: MILLENNIAL_HOME_IMPROVEMENT,
        DINING: 1.08,
        RETAIL: 1.05,
        APPAREL: 1.02,
        HEALTHCARE: 0.95,
        TRAVEL: 1.10,
        SCHOOL: 1.08,
    },
    GEN_X: {
        GROCERY: 1.05,
        HEALTHCARE: 1.08,
        HOME_IMPROVEMENT: 1.10,
        DINING: 1.00,
        RETAIL: 1.00,
        APPAREL: 1.00,
        TRAVEL: 1.05,
        SCHOOL: 1.00,
    },
    BOOMER: {
        HEALTHCARE: BOOMER_HEALTHCARE,
        TRAVEL: BOOMER_TRAVEL,
        GROCERY: 1.10,
        DINING: 0.95,
        RETAIL: 0.90,
        APPAREL: 0.85,
        HOME_IMPROVEMENT: 1.05,
        SCHOOL: 0.80,
    },
}


# =============================================================================
# Income-Brand Preference Tables
# =============================================================================

# Brand preference weights by income band
# Format: income_band_id -> brand_tier -> (min_pref, max_pref)
INCOME_BRAND_PREFERENCES: Dict[str, Dict[str, tuple[float, float]]] = {
    'under_25k': {
        PREMIUM: (0.05, 0.10),
        LUXURY: (0.01, 0.03),
        MID_TIER: (0.25, 0.35),
        VALUE: (0.55, 0.65),
        WALMART: (0.40, 0.50),
    },
    '25k_50k': {
        PREMIUM: (0.10, 0.15),
        LUXURY: (0.03, 0.06),
        MID_TIER: (0.30, 0.40),
        VALUE: (0.45, 0.55),
        WALMART: (0.30, 0.40),
    },
    '50k_75k': {
        PREMIUM: (0.20, 0.30),
        LUXURY: (0.08, 0.15),
        MID_TIER: (0.35, 0.45),
        VALUE: (0.25, 0.35),
        WALMART: (0.15, 0.25),
    },
    '75k_100k': {
        PREMIUM: (0.35, 0.45),
        LUXURY: (0.15, 0.25),
        MID_TIER: (0.30, 0.40),
        VALUE: (0.10, 0.20),
        WALMART: (0.08, 0.12),
    },
    '100k_150k': {
        PREMIUM: (0.50, 0.60),
        LUXURY: (0.25, 0.35),
        MID_TIER: (0.20, 0.30),
        VALUE: (0.03, 0.08),
        WALMART: (0.03, 0.06),
    },
    '150k_200k': {
        PREMIUM: (0.65, 0.75),
        LUXURY: (0.45, 0.60),
        MID_TIER: (0.15, 0.25),
        VALUE: HIGH_INCOME_VALUE,
        WALMART: (0.005, HIGH_INCOME_WALMART),
    },
    'over_200k': {
        PREMIUM: HIGH_INCOME_PREMIUM,
        LUXURY: HIGH_INCOME_LUXURY,
        MID_TIER: HIGH_INCOME_MID_TIER,
        VALUE: HIGH_INCOME_VALUE,
        WALMART: (0.005, HIGH_INCOME_WALMART),
    },
}


def apply_seasonal_adjustment(
    base_amount: float,
    date: datetime,
    category: str
) -> float:
    """Apply Q4 spike, January normalization, back-to-school, weekend patterns.

    Args:
        base_amount: The base transaction amount before seasonal adjustment.
        date: The datetime of the transaction.
        category: The spending category (e.g., 'retail', 'grocery', 'school').

    Returns:
        The adjusted transaction amount after applying seasonal factors.

    Raises:
        ValueError: If category is not recognized.
    """
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Unknown category: {category}. "
            f"Must be one of: {sorted(VALID_CATEGORIES)}"
        )

    month = date.month
    day = date.day
    weekday = date.weekday()  # 0=Monday, 6=Sunday

    multiplier = 1.0

    # Q4 Holiday Season (November-December)
    if month in {11, 12}:
        # Check if in December 15-24 peak period
        if month == 12 and Q4_PEAK_START_DAY <= day <= Q4_PEAK_END_DAY:
            # Peak period: +60-100% vs prior-week baseline
            peak_range = Q4_PEAK_MAX - Q4_PEAK_MIN
            noise = np.random.uniform(0, peak_range)
            multiplier = Q4_PEAK_MIN + noise
        else:
            # Regular November-December: +25-40%
            nov_dec_range = Q4_NOV_DEC_MAX - Q4_NOV_DEC_MIN
            noise = np.random.uniform(0, nov_dec_range)
            multiplier = Q4_NOV_DEC_MIN + noise

    # January Normalization
    elif month == 1:
        january_range = JANUARY_MAX - JANUARY_MIN
        noise = np.random.uniform(0, january_range)
        multiplier = JANUARY_MIN + noise

    # Back-to-School (August-September) for school-related categories
    elif month in BACK_TO_SCHOOL_MONTHS and category == SCHOOL:
        bts_range = BACK_TO_SCHOOL_MAX - BACK_TO_SCHOOL_MIN
        noise = np.random.uniform(0, bts_range)
        multiplier = BACK_TO_SCHOOL_MIN + noise

    # Weekend vs Weekday (for retail categories)
    elif category == RETAIL:
        if weekday == 5:  # Saturday
            sat_range = WEEKEND_SAT_MAX - WEEKEND_SAT_MIN
            noise = np.random.uniform(0, sat_range)
            multiplier = WEEKEND_SAT_MIN + noise
        elif weekday == 6:  # Sunday
            # Sunday has elevated spending but less than Saturday
            # Sunday multiplier: ~1.20 +/- 5%
            noise = np.random.uniform(-0.05, 0.05)
            multiplier = WEEKEND_SUN_MIN + noise

    # For other cases (non-special periods/categories), multiplier stays 1.0
    # with small random variation for realism
    else:
        noise = np.random.uniform(-0.02, 0.02)
        multiplier = 1.0 + noise

    return base_amount * multiplier


def get_generation_preference(
    generation_id: str,
    category: str
) -> float:
    """Get spending multiplier for generation/category combination.

    Args:
        generation_id: The generation identifier.
            Must be one of: 'gen_z', 'millennial', 'gen_x', 'boomer'.
        category: The spending category.
            Must be one of: 'retail', 'grocery', 'dining', 'apparel',
            'healthcare', 'travel', 'home_improvement', 'school'.

    Returns:
        The spending multiplier for the generation/category combination.
        Values > 1.0 indicate increased spending, < 1.0 indicate decreased.

    Raises:
        ValueError: If generation_id or category is not recognized.
    """
    if generation_id not in VALID_GENERATIONS:
        raise ValueError(
            f"Unknown generation: {generation_id}. "
            f"Must be one of: {sorted(VALID_GENERATIONS)}"
        )

    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Unknown category: {category}. "
            f"Must be one of: {sorted(VALID_CATEGORIES)}"
        )

    # Get base multiplier from table
    base_multiplier = GENERATION_CATEGORY_PREFERENCES[generation_id].get(category, 1.0)

    # Add small random variation for realism (+/- 5%)
    noise = np.random.uniform(-0.05, 0.05)
    multiplier = base_multiplier * (1.0 + noise)

    return float(multiplier)


def get_income_brand_preference(
    income_band: str,
    brand_tier: str
) -> float:
    """Get brand preference weight for income band and brand tier.

    Args:
        income_band: The income band ID.
            Must be one of: 'under_25k', '25k_50k', '50k_75k', '75k_100k',
            '100k_150k', '150k_200k', 'over_200k'.
        brand_tier: The brand tier.
            Must be one of: 'premium', 'luxury', 'mid_tier', 'value', 'walmart'.

    Returns:
        The brand preference weight (probability) for the income band/brand tier.
        Values are between 0.0 and 1.0, representing the proportion of
        purchases in that brand tier for the given income band.

    Raises:
        ValueError: If income_band or brand_tier is not recognized.
    """
    if income_band not in INCOME_BRAND_PREFERENCES:
        raise ValueError(
            f"Invalid income band: {income_band}. Must be one of: {INCOME_BAND_IDS}"
        )

    if brand_tier not in VALID_BRAND_TIERS:
        raise ValueError(
            f"Unknown brand tier: {brand_tier}. "
            f"Must be one of: {sorted(VALID_BRAND_TIERS)}"
        )

    # Get preference range from table
    pref_range = INCOME_BRAND_PREFERENCES[income_band][brand_tier]
    min_pref, max_pref = pref_range

    # Sample from the range with slight clustering toward center
    # Using beta distribution-like approach for realistic clustering
    raw_value = np.random.beta(2, 2)  # Clusters around 0.5
    preference = min_pref + raw_value * (max_pref - min_pref)

    return float(preference)


def calculate_brand_income_correlation(
    brand_tier: Literal['premium', 'luxury']
) -> float:
    """Calculate Pearson correlation coefficient for brand preference vs income.

    Args:
        brand_tier: The brand tier to calculate correlation for.
            Must be 'premium' or 'luxury'.

    Returns:
        The Pearson correlation coefficient between income band and
        brand tier preference. This demonstrates the income-brand correlation.

    Raises:
        ValueError: If brand_tier is not 'premium' or 'luxury'.

    Note:
        Premium brands: Pearson coefficient should be 0.45-0.60
        Luxury brands: Pearson coefficient should be 0.55-0.70
    """
    if brand_tier not in {PREMIUM, LUXURY}:
        raise ValueError(
            f"brand_tier must be '{PREMIUM}' or '{LUXURY}', got '{brand_tier}'"
        )

    # Simulate brand preference data across income bands
    # Generate synthetic purchase data using ordinal positions (1-7) for correlation math
    income_band_ordinals = np.array(list(range(1, len(INCOME_BAND_IDS) + 1)))

    # Generate correlated preferences
    # Higher income -> higher preference for premium/luxury
    correlations = []

    for _ in range(100):  # Bootstrap for stability
        preferences = []
        for band_id in INCOME_BAND_IDS:
            pref = get_income_brand_preference(band_id, brand_tier)
            # Add noise and scale to create variance
            noise = np.random.normal(0, 0.05)
            scaled_pref = pref * 100 + noise
            preferences.append(scaled_pref)

        preferences = np.array(preferences)

        # Calculate Pearson correlation with income ordinals
        mean_income = np.mean(income_band_ordinals)
        mean_pref = np.mean(preferences)

        numerator = np.sum((income_band_ordinals - mean_income) * (preferences - mean_pref))
        denominator = np.sqrt(
            np.sum((income_band_ordinals - mean_income) ** 2) *
            np.sum((preferences - mean_pref) ** 2)
        )

        if denominator > 0:
            corr = numerator / denominator
            correlations.append(corr)

    # Return median correlation for stability
    median_corr = np.median(correlations)

    return float(median_corr)
