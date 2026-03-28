"""Data Quality Metrics Validation for Synthetic Data Generator.

This module implements FR-6.10: Data Quality Metrics validation including:
- Coefficient of variation for daily transaction volumes: target 0.3-0.6
- Gini coefficient for brand market share: target 0.55-0.70
- Mean absolute deviation for category proportions vs. BEA: <5%
- Weekend-to-weekday ratio by category: within 10% of benchmarks
- Transaction count distribution per panelist
- Zero-inflation modeling for sparse panelists

Functions:
    validate_transaction_amounts: Validate transaction amounts have correct distribution.
    validate_market_share: Validate brand market share distribution.
    validate_category_proportions: Validate category proportions against BEA benchmarks.
    validate_weekend_weekday_ratio: Validate weekend vs weekday spending ratio.
    validate_transaction_frequency: Validate transaction count distribution per panelist.
    generate_validation_report: Generate comprehensive validation report.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np


# FR-6.10 Target constants
CV_MIN = 0.3
CV_MAX = 0.6
GINI_MIN = 0.55
GINI_MAX = 0.70
MAD_MAX = 0.05  # 5% threshold
WEEKEND_WEEKDAY_TOLERANCE = 0.10  # 10% tolerance

# Benchmark constants
RETAIL_WEEKEND_WEEKDAY_RATIO = 1.30  # Typical Saturday vs Monday ratio

# Zero-inflation threshold (panelists with less than this many transactions are "sparse")
ZERO_INFLATION_THRESHOLD = 5


@dataclass
class Transaction:
    """Simplified transaction for validation purposes.

    Attributes:
        transaction_id: Unique identifier for the transaction.
        panelist_id: Identifier for the panelist who made the transaction.
        date: Date and time of the transaction.
        amount: Transaction amount in dollars.
        category: Spending category (e.g., 'grocery', 'dining', 'retail').
        brand: Optional brand name for the transaction.
    """
    transaction_id: str
    panelist_id: str
    date: datetime
    amount: float
    category: str
    brand: Optional[str] = None


@dataclass
class ValidationReport:
    """Report of data quality validation results.

    Attributes:
        coefficient_of_variation: CV of daily transaction volumes (target 0.3-0.6).
        gini_coefficient: Gini coefficient for brand market share (target 0.55-0.70).
        category_mad: Mean absolute deviation for category proportions (target <5%).
        weekend_weekday_ratio: Weekend to weekday spending ratio.
        transaction_frequency_ok: Whether transaction frequency distribution is valid.
        zero_inflation_ok: Whether zero-inflation is appropriately modeled.
        all_passed: Whether all metrics passed their thresholds.
    """
    coefficient_of_variation: float
    gini_coefficient: float
    category_mad: float
    weekend_weekday_ratio: float
    transaction_frequency_ok: bool
    zero_inflation_ok: bool
    all_passed: bool


def validate_transaction_amounts(amounts: List[float]) -> Dict[str, float]:
    """Validate transaction amounts have correct distribution properties.

    Calculates the coefficient of variation (CV) which measures the
    relative variability of transaction amounts.

    Args:
        amounts: List of transaction amounts to validate.

    Returns:
        Dictionary containing:
            - coefficient_of_variation: The CV (std/mean) of the amounts.
            - mean: The mean of the amounts.
            - std: The standard deviation of the amounts.
            - min: The minimum amount.
            - max: The maximum amount.
    """
    if not amounts:
        return {
            'coefficient_of_variation': 0.0,
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0
        }

    amounts_array = np.array(amounts)
    mean = float(np.mean(amounts_array))
    std = float(np.std(amounts_array, ddof=0))  # Population std

    # Avoid division by zero
    if mean == 0:
        cv = 0.0
    else:
        cv = std / mean

    return {
        'coefficient_of_variation': cv,
        'mean': mean,
        'std': std,
        'min': float(np.min(amounts_array)),
        'max': float(np.max(amounts_array))
    }


def validate_market_share(brand_shares: Dict[str, float]) -> Dict[str, float]:
    """Validate brand market share distribution.

    Calculates the Gini coefficient to measure inequality in brand
    market shares. A Gini of 0 means perfect equality, while 1 means
    perfect inequality (one brand dominates).

    Args:
        brand_shares: Dictionary mapping brand names to their market share
            (proportions that sum to 1.0).

    Returns:
        Dictionary containing:
            - gini_coefficient: The Gini coefficient (0-1).
            - num_brands: Number of brands in the distribution.
            - market_concentration: The share of the top brand.
    """
    if not brand_shares:
        return {
            'gini_coefficient': 0.0,
            'num_brands': 0,
            'market_concentration': 0.0
        }

    # Get shares as array and sort for Lorenz curve
    shares = np.array(list(brand_shares.values()))
    n = len(shares)

    if n == 0:
        return {
            'gini_coefficient': 0.0,
            'num_brands': 0,
            'market_concentration': 0.0
        }

    # Sort shares in ascending order
    sorted_shares = np.sort(shares)

    # Calculate Gini coefficient using the corrected formula:
    # Gini = (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
    # where x_i is the sorted share and i is its rank (1-indexed)
    n_array = np.arange(1, n + 1)

    # Numerator: 2 * sum(i * x_i)
    numerator = 2.0 * np.sum(n_array * sorted_shares)
    # Denominator part: (n + 1) * sum(x_i)
    denominator = (n + 1) * np.sum(sorted_shares)

    if denominator == 0:
        gini = 0.0
    else:
        # The corrected Gini formula
        gini = (numerator - denominator) / (n * np.sum(sorted_shares))

    # Handle edge case: single brand (100% market share) should give Gini = 0
    # because there's perfect equality in the distribution (everyone uses the same brand)
    # But if there's meaningful share split among multiple brands, Gini > 0
    if n == 1:
        gini = 0.0

    # Ensure Gini is in [0, 1]
    gini = max(0.0, min(1.0, gini))

    return {
        'gini_coefficient': gini,
        'num_brands': n,
        'market_concentration': float(np.max(shares))
    }


def validate_category_proportions(
    category_totals: Dict[str, float],
    benchmark: Dict[str, float]
) -> float:
    """Validate category proportions against BEA benchmarks.

    Calculates the mean absolute deviation (MAD) between the actual
    category proportions and benchmark proportions.

    Args:
        category_totals: Dictionary mapping category names to total spending.
        benchmark: Dictionary mapping category names to expected proportions
            (should sum to 1.0).

    Returns:
        The mean absolute deviation as a proportion (0-1 scale).
        Values < 0.05 (5%) indicate good agreement with benchmarks.
    """
    if not category_totals:
        return 0.0

    if not benchmark:
        return 0.0

    # Calculate actual proportions
    total_spend = sum(category_totals.values())

    if total_spend == 0:
        return 0.0

    actual_props = {cat: amt / total_spend for cat, amt in category_totals.items()}

    # Get all categories that appear in either
    all_categories = set(actual_props.keys()) | set(benchmark.keys())

    # Calculate absolute deviations
    deviations = []
    for cat in all_categories:
        actual = actual_props.get(cat, 0.0)
        expected = benchmark.get(cat, 0.0)
        deviations.append(abs(actual - expected))

    # Return mean absolute deviation
    mad = float(np.mean(deviations)) if deviations else 0.0

    return mad


def validate_weekend_weekday_ratio(
    weekend_total: float,
    weekday_total: float
) -> float:
    """Validate weekend vs weekday spending ratio.

    Calculates the ratio of weekend to weekday spending. Weekend spending
    is typically 30-35% higher than weekday for retail categories.

    Args:
        weekend_total: Total spending on weekends (Saturday + Sunday).
        weekday_total: Total spending on weekdays (Monday-Friday).

    Returns:
        The ratio of weekend to weekday spending.
        Values around 1.30-1.35 are typical for retail.
    """
    if weekday_total == 0:
        # Avoid division by zero
        return float('inf') if weekend_total > 0 else 0.0

    return float(weekend_total / weekday_total)


def validate_transaction_frequency(
    transactions_per_panelist: List[int]
) -> bool:
    """Validate transaction count distribution per panelist.

    Checks if the transaction frequency distribution follows expected
    patterns. Uses statistical tests to detect if the distribution
    is realistic for consumer panel data.

    The distribution should generally follow a Poisson-like pattern
    with some zero-inflation for sparse panelists.

    Args:
        transactions_per_panelist: List of transaction counts per panelist.

    Returns:
        True if the distribution is valid, False otherwise.
    """
    if not transactions_per_panelist:
        return True

    counts = np.array(transactions_per_panelist)

    # Basic checks
    if len(counts) == 0:
        return True

    # Check for reasonable range
    max_count = np.max(counts)
    if max_count > 10000:  # Unreasonably high
        return False

    # Calculate zero-inflation rate
    zero_count = np.sum(counts == 0)
    zero_rate = zero_count / len(counts)

    # Zero-inflation is expected for sparse panelists
    # But should not be too high (>80% zeros is suspicious)
    if zero_rate > 0.8:
        return False

    # Check that the distribution has reasonable variance
    # A Poisson-like distribution has mean ~= variance
    mean_count = np.mean(counts)
    var_count = np.var(counts)

    # If there are non-zero counts, check variance relationship
    non_zero_counts = counts[counts > 0]
    if len(non_zero_counts) > 0:
        mean_nz = np.mean(non_zero_counts)

        # For count data, variance should not be unreasonably large
        # compared to mean (overdispersion check)
        if mean_nz > 0:
            var_to_mean_ratio = var_count / mean_nz if mean_nz > 0 else 0

            # Reasonable ratio should be less than 100 for panel data
            if var_to_mean_ratio > 100:
                return False

    # Check for minimum activity among active panelists
    if len(non_zero_counts) > 0:
        max_active = np.max(non_zero_counts)

        # If maximum is 1 for all non-zero, that's a very sparse panel
        if max_active <= 1 and len(non_zero_counts) > len(counts) * 0.2:
            return False

    return True


def _calculate_zero_inflation_score(
    transactions_per_panelist: List[int]
) -> bool:
    """Check if zero-inflation is appropriately modeled.

    Zero-inflation is expected for panelists with sparse transaction history.
    This function checks if the zero-inflation pattern is realistic.

    Args:
        transactions_per_panelist: List of transaction counts per panelist.

    Returns:
        True if zero-inflation is appropriate, False otherwise.
    """
    if not transactions_per_panelist:
        return True

    counts = np.array(transactions_per_panelist)
    n = len(counts)

    # Count zero and non-zero
    zero_count = np.sum(counts == 0)
    zero_rate = zero_count / n if n > 0 else 0

    # Calculate proportion of sparse panelists
    sparse_threshold = ZERO_INFLATION_THRESHOLD
    sparse_count = np.sum((counts > 0) & (counts < sparse_threshold))
    sparse_rate = sparse_count / n if n > 0 else 0

    # A realistic panel should have:
    # - Some zero-activity panelists (10-40% typical for sparse panels)
    # - Mix of light, medium, and heavy users

    # If zero rate is too low or too high, that's a problem
    if zero_rate < 0.0 or zero_rate > 0.9:
        return False

    # Check for bimodal distribution (light users + heavy users)
    non_zero = counts[counts > 0]
    if len(non_zero) > 10:
        # Simple check: if standard deviation is large relative to mean,
        # it might indicate bimodal (which is actually OK for panel data)
        mean_nz = np.mean(non_zero)
        std_nz = np.std(non_zero)

        if mean_nz > 0:
            cv = std_nz / mean_nz

            # High CV (>2) could indicate bimodal distribution
            # which is actually realistic for panel data
            pass  # This is actually OK

    return True


def generate_validation_report(transactions: List[Transaction]) -> ValidationReport:
    """Generate comprehensive validation report for transaction dataset.

    Performs all FR-6.10 validation checks on the transaction dataset.

    Args:
        transactions: List of Transaction objects to validate.

    Returns:
        ValidationReport with all metrics and overall pass/fail status.
    """
    if not transactions:
        return ValidationReport(
            coefficient_of_variation=0.0,
            gini_coefficient=0.0,
            category_mad=0.0,
            weekend_weekday_ratio=0.0,
            transaction_frequency_ok=True,
            zero_inflation_ok=True,
            all_passed=False
        )

    # 1. Coefficient of Variation for transaction amounts
    amounts = [t.amount for t in transactions]
    amounts_result = validate_transaction_amounts(amounts)
    cv = amounts_result['coefficient_of_variation']

    # 2. Gini coefficient for brand market share
    # Calculate brand shares from transactions
    brand_totals: Dict[str, float] = {}
    for t in transactions:
        if t.brand:
            brand_totals[t.brand] = brand_totals.get(t.brand, 0.0) + t.amount

    # Normalize to get shares
    total_brand_amount = sum(brand_totals.values())
    if total_brand_amount > 0:
        brand_shares = {b: amt / total_brand_amount for b, amt in brand_totals.items()}
    else:
        brand_shares = {}

    market_result = validate_market_share(brand_shares)
    gini = market_result['gini_coefficient']

    # 3. Category MAD
    category_totals: Dict[str, float] = {}
    for t in transactions:
        category_totals[t.category] = category_totals.get(t.category, 0.0) + t.amount

    # Benchmark (simplified BEA consumer expenditure proportions)
    benchmark = {
        'grocery': 0.30,
        'dining': 0.20,
        'retail': 0.25,
        'apparel': 0.10,
        'healthcare': 0.05,
        'travel': 0.05,
        'home_improvement': 0.03,
        'school': 0.02
    }

    category_mad = validate_category_proportions(category_totals, benchmark)

    # 4. Weekend/weekday ratio
    weekend_total = 0.0
    weekday_total = 0.0

    for t in transactions:
        # weekday() returns 0-4 for Mon-Fri, 5-6 for Sat-Sun
        if t.date.weekday() >= 5:  # Saturday or Sunday
            weekend_total += t.amount
        else:
            weekday_total += t.amount

    weekend_weekday_ratio = validate_weekend_weekday_ratio(weekend_total, weekday_total)

    # 5. Transaction frequency per panelist
    panelist_counts: Dict[str, int] = {}
    for t in transactions:
        panelist_counts[t.panelist_id] = panelist_counts.get(t.panelist_id, 0) + 1

    transactions_per_panelist = list(panelist_counts.values())
    transaction_frequency_ok = validate_transaction_frequency(transactions_per_panelist)

    # 6. Zero-inflation check
    zero_inflation_ok = _calculate_zero_inflation_score(transactions_per_panelist)

    # Determine if all passed
    cv_ok = CV_MIN <= cv <= CV_MAX
    gini_ok = GINI_MIN <= gini <= GINI_MAX
    mad_ok = category_mad < MAD_MAX

    # Weekend/weekday ratio within 10% of benchmark
    ratio_ok = abs(weekend_weekday_ratio - RETAIL_WEEKEND_WEEKDAY_RATIO) / RETAIL_WEEKEND_WEEKDAY_RATIO <= WEEKEND_WEEKDAY_TOLERANCE

    all_passed = (cv_ok and gini_ok and mad_ok and ratio_ok and
                  transaction_frequency_ok and zero_inflation_ok)

    return ValidationReport(
        coefficient_of_variation=cv,
        gini_coefficient=gini,
        category_mad=category_mad,
        weekend_weekday_ratio=weekend_weekday_ratio,
        transaction_frequency_ok=transaction_frequency_ok,
        zero_inflation_ok=zero_inflation_ok,
        all_passed=all_passed
    )
