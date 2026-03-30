"""Transaction generation for synthetic data generator.

This module implements FR-6.6 and FR-6.7: Transaction generation with:
- Log-normal transaction amounts with income multipliers
- Seasonal adjustments (Q4 holiday spike, January normalization, back-to-school)
- Generational preferences
- Income-brand correlation
- Weekend/weekday patterns

Functions:
    Transaction: Dataclass representing a consumer transaction.
    generate_transactions_for_panelist: Generate transactions for a single panelist.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Generator, List
import uuid

import numpy as np

from src.data.distributions import generate_transaction_amount
from src.data.seasonal_patterns import (
    apply_seasonal_adjustment,
    get_generation_preference,
    get_income_brand_preference,
)


# Card types for transactions
CARD_TYPES = ["credit", "debit", "prepaid"]
CARD_TYPE_WEIGHTS = [0.45, 0.45, 0.10]

# Payment networks
PAYMENT_NETWORKS = ["visa", "mastercard", "amex", "discover"]
PAYMENT_NETWORK_WEIGHTS = [0.40, 0.35, 0.15, 0.10]

# Channels
CHANNELS = ["in_store", "online", "mobile_app"]
CHANNEL_WEIGHTS = [0.55, 0.35, 0.10]

# Day names for weekday()
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Star brand IDs: dominant brands per tier that get 15x selection weight to increase Gini.
# These are high-revenue, widely-recognized brands in each tier.
# IDs match brand insertion order in generate_synthetic_data.py BRAND_SEED (after re-seed).
STAR_BRAND_IDS = {
    1,   # Walmart (retail essential)
    2,   # Target (retail mid_tier)
    5,   # Costco (retail mid_tier warehouse)
    14,  # Kroger (grocery essential)
    16,  # Whole Foods (grocery premium)
    17,  # Trader Joe's (grocery mid_tier)
    24,  # Olive Garden (dining)
    34,  # McDonald's (fast_food)
    36,  # Chick-fil-A (fast_food)
    43,  # Nordstrom (apparel premium)
    45,  # Louis Vuitton (apparel luxury)
    54,  # CVS (healthcare essential)
    55,  # Walgreens (healthcare essential)
    59,  # Marriott (travel premium)
    60,  # Hilton (travel mid_tier)
    65,  # Home Depot (home_improvement mid_tier)
    66,  # Lowe's (home_improvement mid_tier)
    70,  # Staples (school mid_tier)
    71,  # Best Buy (school electronics)
}
STAR_MULTIPLIER = 15.0

# FR-6.6: Target category proportions (BEA consumer spending benchmarks).
# Used to steer category selection toward realistic spending distributions.
# Sum = 1.0. grocery=30%, dining=20%, retail=25%, apparel=10%,
# healthcare=5%, travel=5%, home_improvement=3%, school=2%.
CATEGORY_TARGET_PROPORTIONS: Dict[str, float] = {
    "grocery": 0.30,
    "dining": 0.20,
    "retail": 0.25,
    "apparel": 0.10,
    "healthcare": 0.05,
    "travel": 0.05,
    "home_improvement": 0.03,
    "school": 0.02,
}

# Transaction rate constants (per year per panelist)
TRANSACTIONS_PER_YEAR_MIN = 25
TRANSACTIONS_PER_YEAR_MAX = 100


@dataclass
class Transaction:
    """Represents a consumer transaction.

    Attributes:
        id: Unique transaction identifier.
        panelist_id: ID of the panelist who made the transaction.
        brand_id: Brand identifier.
        category_id: Category identifier.
        geography_id: Geographic region identifier.
        generation_id: Generation identifier ('gen_z', 'millennial', 'gen_x', 'boomer').
        income_band_id: Income band ID ('under_25k', '25k_50k', etc.).
        transaction_timestamp: Date and time of the transaction.
        transaction_amount: Amount in dollars.
        card_type: Type of card used ('credit', 'debit', 'prepaid').
        payment_network: Payment network ('visa', 'mastercard', 'amex', 'discover').
        channel: Purchase channel ('in_store', 'online', 'mobile_app').
        day_of_week: Day of week name.
        hour_of_day: Hour of day (0-23).
    """
    id: str
    panelist_id: str
    brand_id: int
    category_id: int
    geography_id: int
    generation_id: str
    income_band_id: str
    transaction_timestamp: datetime
    transaction_amount: float
    card_type: str
    payment_network: str
    channel: str
    day_of_week: str
    hour_of_day: int


def _sample_card_type() -> str:
    """Sample a card type based on weighted probabilities."""
    return np.random.choice(CARD_TYPES, p=CARD_TYPE_WEIGHTS)


def _sample_payment_network() -> str:
    """Sample a payment network based on weighted probabilities."""
    return np.random.choice(PAYMENT_NETWORKS, p=PAYMENT_NETWORK_WEIGHTS)


def _sample_channel() -> str:
    """Sample a purchase channel based on weighted probabilities."""
    return np.random.choice(CHANNELS, p=CHANNEL_WEIGHTS)


def _get_category_name_from_id(category_id: int, categories: List) -> str:
    """Get category name from category ID."""
    for cat in categories:
        cat_id = _get_field(cat, "category_id", _get_field(cat, "id", None))
        if cat_id == category_id:
            return _get_field(cat, "category_name", _get_field(cat, "name", "retail"))
    return "retail"


def _get_field(obj, field: str, default=None):
    """Get field from dict or object with attribute access."""
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


def _get_brand_tier(brand) -> str:
    """Get brand tier from brand dictionary or object."""
    return _get_field(brand, "brand_tier", _get_field(brand, "tier", "mid_tier"))


def generate_transactions_for_panelist(
    panelist,
    start_date: date,
    end_date: date,
    brands: List[Dict],
    categories: List[Dict],
    geography_lookup: Dict[int, str],
    seed: int = 42,
) -> Generator[Transaction, None, None]:
    """Generate transactions for a single panelist over date range.

    Generates transactions with:
    - Log-normal amounts with income multipliers
    - Seasonal adjustments (Q4 spike, January normalization, back-to-school)
    - Generational preferences
    - Income-brand correlation
    - Weekend/weekday patterns

    Args:
        panelist: Panelist object with demographic attributes.
            Must have: id, income_band_id, generation_id, geography_id, panel_weight
        start_date: Start date for transaction generation.
        end_date: End date for transaction generation.
        brands: List of brand dictionaries.
            Each dict should have: brand_id, brand_tier, category_id
        categories: List of category dictionaries.
            Each dict should have: category_id, category_name
        geography_lookup: Dictionary mapping geography_id to geography name.
        seed: Random seed for reproducibility.

    Yields:
        Transaction objects with all required fields.

    Raises:
        ValueError: If date range is invalid or panelist is missing required fields.
    """
    if end_date <= start_date:
        raise ValueError(f"End date ({end_date}) must be after start date ({start_date})")

    # Set random seed for reproducibility
    np.random.seed(seed)

    # Calculate number of days and expected transactions
    date_diff = (end_date - start_date).days
    years = date_diff / 365.0

    # Calculate expected number of transactions (50-200 over 2 years = 25-100 per year)
    expected_txns = int(years * np.random.uniform(TRANSACTIONS_PER_YEAR_MIN, TRANSACTIONS_PER_YEAR_MAX))

    # Generate transaction timestamps spread across the date range
    if expected_txns > 0:
        # Weekend weighting: Saturday and Sunday ~3.05x more likely than weekdays.
        # This targets RETAIL_WEEKEND_WEEKDAY_RATIO ≈ 1.30 (weekend amount / weekday amount).
        # With Sat=Sunday=3.05x weekday:
        #   weekday share = 5/(5 + 2*3.05) = 5/11.1, weekend share = 6.1/11.1
        # Combined with weekend amount multiplier ~1.26 (avg of Sat 1.325, Sun 1.20):
        #   weekend/weekday ratio = (6.1/5) * 1.26 = 1.54 (but actual is lower due to other effects)
        # Interpolated from test runs: w=1.9→0.92, w=3.25→1.55, target 1.30→w≈3.05
        day_weights = [1.0, 1.0, 1.0, 1.0, 1.0, 2.95, 2.95]
        day_probs = np.array(day_weights) / sum(day_weights)  # normalize

        transaction_dates = []
        for _ in range(expected_txns):
            # Pick day of week from weighted distribution
            dow = np.random.choice(7, p=day_probs)

            # Find a random date within range that falls on that day-of-week.
            # Strategy: pick a random offset, then roll forward/back to target dow.
            base_offset = np.random.randint(0, date_diff)
            candidate_date = start_date + timedelta(days=base_offset)
            current_dow = candidate_date.weekday()

            # Adjust to target dow (0=Mon ... 6=Sun)
            days_to_add = (dow - current_dow) % 7
            txn_date = candidate_date + timedelta(days=days_to_add)

            # Random hour (weighted toward afternoon/evening)
            # Hour distribution: 24 elements for hours 0-23
            # Sum must equal 1.0 for np.random.choice
            hour_weights = [
                0.02, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03,  # Night/early morning (0-6)
                0.05, 0.06, 0.06, 0.06, 0.06, 0.05,  # Morning (7-12)
                0.08, 0.08, 0.07, 0.06, 0.05, 0.04,  # Afternoon (13-18)
                0.06, 0.05, 0.03, 0.02, 0.01  # Evening (19-23)
            ]
            hour = np.random.choice(range(24), p=hour_weights)

            # Random minute
            minute = np.random.randint(0, 60)
            second = np.random.randint(0, 60)

            txn_datetime = datetime(
                txn_date.year, txn_date.month, txn_date.day,
                hour, minute, second
            )
            transaction_dates.append(txn_datetime)

        # Sort transactions by timestamp
        transaction_dates.sort()

        # Build category name <-> id lookups
        category_id_to_name: Dict[int, str] = {}
        for cat in categories:
            cat_id = _get_field(cat, "category_id", _get_field(cat, "id", None))
            cat_name = _get_field(cat, "category_name", _get_field(cat, "name", "retail"))
            if cat_id is not None:
                category_id_to_name[cat_id] = cat_name

        # Build brand choices list + category-name-to-brands mapping
        brand_choices: List[tuple] = []
        category_name_to_brands: Dict[str, List[tuple]] = {}
        for brand in brands:
            brand_id = _get_field(brand, "brand_id", _get_field(brand, "id", 1))
            tier = _get_brand_tier(brand)
            category_id = _get_field(brand, "category_id", _get_field(brand, "category", 1))
            cat_name = category_id_to_name.get(category_id, "retail")
            entry = (brand_id, tier, category_id)
            brand_choices.append(entry)
            if cat_name not in category_name_to_brands:
                category_name_to_brands[cat_name] = []
            category_name_to_brands[cat_name].append(entry)

        if not brand_choices:
            brand_choices = [(1, "mid_tier", 1)]

        # Build target category selection probabilities
        cat_names = list(CATEGORY_TARGET_PROPORTIONS.keys())
        cat_probs = [CATEGORY_TARGET_PROPORTIONS[c] for c in cat_names]

        # Generate each transaction
        for txn_datetime in transaction_dates:
            # Select category first from target proportions, then brand within category.
            # This steers category distribution toward BEA benchmarks.
            category_name = np.random.choice(cat_names, p=cat_probs)

            # Get brands in selected category, falling back to all brands
            cat_brands = category_name_to_brands.get(category_name, brand_choices)
            if not cat_brands:
                cat_brands = brand_choices

            # Select brand from within the chosen category using income preferences
            brand_id, brand_tier, category_id = _select_brand_for_income(
                panelist.income_band_id,
                cat_brands
            )

            # Generate base transaction amount using log-normal distribution
            base_amount = generate_transaction_amount(
                category_tier=brand_tier,
                income_band=panelist.income_band_id
            )

            # Apply generational preference adjustment
            gen_multiplier = get_generation_preference(
                panelist.generation_id,
                category_name
            )
            amount_after_generation = base_amount * gen_multiplier

            # Apply seasonal adjustment (Q4, January, back-to-school, weekend)
            final_amount = apply_seasonal_adjustment(
                amount_after_generation,
                txn_datetime,
                category_name
            )

            # Ensure amount is positive
            final_amount = max(0.01, final_amount)

            # Sample card type, payment network, and channel
            card_type = _sample_card_type()
            payment_network = _sample_payment_network()
            channel = _sample_channel()

            # Get day of week
            day_of_week = DAY_NAMES[txn_datetime.weekday()]
            hour_of_day = txn_datetime.hour

            yield Transaction(
                id=str(uuid.uuid4()),
                panelist_id=panelist.id,
                brand_id=brand_id,
                category_id=category_id,
                geography_id=panelist.geography_id,
                generation_id=panelist.generation_id,
                income_band_id=panelist.income_band_id,
                transaction_timestamp=txn_datetime,
                transaction_amount=round(final_amount, 2),
                card_type=card_type,
                payment_network=payment_network,
                channel=channel,
                day_of_week=day_of_week,
                hour_of_day=hour_of_day,
            )


def _select_brand_for_income(
    income_band: str,
    brand_choices: List[tuple]
) -> tuple:
    """Select a brand based on income-brand correlation.

    Uses the income_brand_preference function to weight brand selection
    based on the panelist's income band.

    Args:
        income_band: Income band ID (e.g., 'under_25k', '100k_150k').
        brand_choices: List of (brand_id, tier, category_id) tuples.

    Returns:
        Tuple of (brand_id, tier, category_id).
    """
    if not brand_choices:
        return (1, "mid_tier", 1)

    # If only one brand, return it
    if len(brand_choices) == 1:
        return brand_choices[0]

    # Get preference weights for each brand tier, with 10x boost for star brands
    weights = []
    for brand_id, tier, category_id in brand_choices:
        pref = get_income_brand_preference(income_band, tier)
        if brand_id in STAR_BRAND_IDS:
            pref *= STAR_MULTIPLIER
        weights.append(pref)

    # Normalize weights
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w / total_weight for w in weights]
    else:
        # Equal weights if all are zero
        weights = [1.0 / len(brand_choices)] * len(brand_choices)

    # Select brand based on weights
    selected_idx = np.random.choice(len(brand_choices), p=weights)
    return brand_choices[selected_idx]
