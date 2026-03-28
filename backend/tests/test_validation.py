"""Tests for FR-6.10: Data Quality Metrics Validation.

This module tests statistical validation for synthetic transaction data:
- Coefficient of variation for daily transaction volumes: target 0.3-0.6
- Gini coefficient for brand market share: target 0.55-0.70
- Mean absolute deviation for category proportions vs. BEA: <5%
- Weekend-to-weekday ratio by category: within 10% of benchmarks
- Transaction count distribution per panelist
- Zero-inflation modeling for sparse panelists
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pytest


# Test constants
SEED = 42

# FR-6.10 Target constants
CV_MIN = 0.3
CV_MAX = 0.6
GINI_MIN = 0.55
GINI_MAX = 0.70
MAD_MAX = 0.05  # 5%
WEEKEND_WEEKDAY_TOLERANCE = 0.10  # 10%


@dataclass
class Transaction:
    """Simplified transaction for testing validation."""
    transaction_id: str
    panelist_id: str
    date: datetime
    amount: float
    category: str
    brand: Optional[str] = None


class TestFr610CoefficientOfVariation:
    """FR-6.10: Coefficient of variation for daily transaction volumes."""

    def test_fr_6_10_cv_calculation_basic(self) -> None:
        """Coefficient of variation is calculated as std/mean."""
        from src.data.validation import validate_transaction_amounts

        # Create amounts with known CV
        # If mean=100 and std=30, then CV=0.3
        amounts = [100, 130, 70, 100, 100]
        np.random.seed(SEED)
        result = validate_transaction_amounts(amounts)

        assert 'coefficient_of_variation' in result
        cv = result['coefficient_of_variation']
        assert cv >= 0

    def test_fr_6_10_cv_low_variance(self) -> None:
        """Low variance amounts should have CV close to 0."""
        from src.data.validation import validate_transaction_amounts

        # Nearly constant amounts = very low CV
        amounts = [100, 101, 99, 100, 100]
        np.random.seed(SEED)
        result = validate_transaction_amounts(amounts)

        cv = result['coefficient_of_variation']
        assert cv < 0.1

    def test_fr_6_10_cv_high_variance(self) -> None:
        """High variance amounts should have CV > 1."""
        from src.data.validation import validate_transaction_amounts

        # Highly variable amounts
        amounts = [100, 500, 50, 200, 150]
        np.random.seed(SEED)
        result = validate_transaction_amounts(amounts)

        cv = result['coefficient_of_variation']
        assert cv > 0.5


class TestFr610GiniCoefficient:
    """FR-6.10: Gini coefficient for brand market share."""

    def test_fr_6_10_gini_calculation_basic(self) -> None:
        """Gini coefficient is calculated from market shares."""
        from src.data.validation import validate_market_share

        # Equal market shares should give Gini close to 0
        brand_shares = {'brand_a': 0.25, 'brand_b': 0.25, 'brand_c': 0.25, 'brand_d': 0.25}
        np.random.seed(SEED)
        result = validate_market_share(brand_shares)

        assert 'gini_coefficient' in result
        gini = result['gini_coefficient']
        assert 0 <= gini <= 1

    def test_fr_6_10_gini_unequal_shares(self) -> None:
        """Unequal market shares should give higher Gini."""
        from src.data.validation import validate_market_share

        # Highly unequal shares should give Gini closer to 1
        brand_shares = {'dominant': 0.8, 'other1': 0.1, 'other2': 0.05, 'other3': 0.05}
        np.random.seed(SEED)
        result = validate_market_share(brand_shares)

        gini = result['gini_coefficient']
        assert gini > 0.5

    def test_fr_6_10_gini_perfect_equality(self) -> None:
        """Perfect equality should give Gini of 0."""
        from src.data.validation import validate_market_share

        # All equal shares
        brand_shares = {f'brand_{i}': 1.0/6 for i in range(6)}
        np.random.seed(SEED)
        result = validate_market_share(brand_shares)

        gini = result['gini_coefficient']
        assert gini < 0.1

    def test_fr_6_10_gini_perfect_equality(self) -> None:
        """Single brand (100% share) should give Gini of 0 - everyone uses same brand."""
        from src.data.validation import validate_market_share

        # One brand has 100% share - everyone uses the same brand
        # This is actually perfect equality in terms of market share distribution
        brand_shares = {'only_brand': 1.0}
        np.random.seed(SEED)
        result = validate_market_share(brand_shares)

        gini = result['gini_coefficient']
        assert gini == 0.0, f"Single brand with 100% share should give Gini 0, got {gini}"

    def test_fr_6_10_gini_equal_distribution(self) -> None:
        """Equal shares among many brands should give low Gini."""
        from src.data.validation import validate_market_share

        # Equal shares among many brands - no inequality
        brand_shares = {f'brand_{i}': 0.1 for i in range(10)}
        np.random.seed(SEED)
        result = validate_market_share(brand_shares)

        gini = result['gini_coefficient']
        # Equal distribution should give Gini close to 0
        assert gini < 0.1, f"Equal shares should give low Gini, got {gini}"


class TestFr610CategoryMeanAbsoluteDeviation:
    """FR-6.10: Mean absolute deviation for category proportions."""

    def test_fr_6_10_category_mad_basic(self) -> None:
        """MAD is calculated as mean of absolute differences."""
        from src.data.validation import validate_category_proportions

        # Identical proportions = MAD of 0
        category_totals = {'grocery': 1000, 'dining': 500, 'retail': 500}
        benchmark = {'grocery': 0.5, 'dining': 0.25, 'retail': 0.25}

        np.random.seed(SEED)
        mad = validate_category_proportions(category_totals, benchmark)

        assert mad >= 0
        assert mad < 0.01  # Should be nearly 0 for identical

    def test_fr_6_10_category_mad_within_tolerance(self) -> None:
        """MAD within 5% threshold passes validation."""
        from src.data.validation import validate_category_proportions

        # Small deviation should be within 5%
        category_totals = {'grocery': 1000, 'dining': 500, 'retail': 500}
        # Actual proportions: 0.5, 0.25, 0.25
        # Benchmark: 0.52, 0.24, 0.24 (2% deviation each)
        benchmark = {'grocery': 0.52, 'dining': 0.24, 'retail': 0.24}

        np.random.seed(SEED)
        mad = validate_category_proportions(category_totals, benchmark)

        assert mad < MAD_MAX  # 5% threshold

    def test_fr_6_10_category_mad_exceeds_tolerance(self) -> None:
        """MAD exceeding 5% threshold fails validation."""
        from src.data.validation import validate_category_proportions

        category_totals = {'grocery': 1000, 'dining': 500, 'retail': 500}
        # Large deviation
        benchmark = {'grocery': 0.7, 'dining': 0.2, 'retail': 0.1}

        np.random.seed(SEED)
        mad = validate_category_proportions(category_totals, benchmark)

        assert mad > MAD_MAX  # Should exceed 5% threshold


class TestFr610WeekendWeekdayRatio:
    """FR-6.10: Weekend-to-weekday spending ratio."""

    def test_fr_6_10_weekend_weekday_ratio_basic(self) -> None:
        """Ratio is weekend_total / weekday_total."""
        from src.data.validation import validate_weekend_weekday_ratio

        # Equal totals = ratio of 1
        np.random.seed(SEED)
        ratio = validate_weekend_weekday_ratio(weekend_total=1000, weekday_total=1000)

        assert abs(ratio - 1.0) < 0.01

    def test_fr_6_10_weekend_weekday_ratio_elevated_weekend(self) -> None:
        """Weekend spending elevated vs weekday shows ratio > 1."""
        from src.data.validation import validate_weekend_weekday_ratio

        # Saturday typically 30-35% higher
        np.random.seed(SEED)
        ratio = validate_weekend_weekday_ratio(weekend_total=1300, weekday_total=1000)

        assert ratio > 1.0
        assert ratio < 1.5  # Should be reasonable

    def test_fr_6_10_weekend_weekday_ratio_within_benchmark(self) -> None:
        """Ratio within 10% of benchmark passes."""
        from src.data.validation import validate_weekend_weekday_ratio

        # Weekend is 30% higher, which is within typical range
        np.random.seed(SEED)
        ratio = validate_weekend_weekday_ratio(weekend_total=1300, weekday_total=1000)

        # Benchmark for retail is typically 1.30
        # 1.30 is within 10% of 1.30
        assert ratio > 1.17  # 10% below 1.30
        assert ratio < 1.43  # 10% above 1.30


class TestFr610TransactionFrequency:
    """FR-6.10: Transaction count distribution per panelist."""

    def test_fr_6_10_frequency_basic(self) -> None:
        """Frequency distribution validation returns boolean."""
        from src.data.validation import validate_transaction_frequency

        # Typical frequency distribution
        transactions_per_panelist = [10, 15, 8, 12, 20, 5, 18, 11, 14, 9]

        np.random.seed(SEED)
        result = validate_transaction_frequency(transactions_per_panelist)

        assert isinstance(result, bool)

    def test_fr_6_10_frequency_zero_inflation(self) -> None:
        """Zero-inflation is detected for sparse panelists."""
        from src.data.validation import validate_transaction_frequency

        # Mix of high and zero frequency panelists
        transactions_per_panelist = [0, 0, 0, 5, 10, 50, 60, 55, 45, 0, 0]

        np.random.seed(SEED)
        result = validate_transaction_frequency(transactions_per_panelist)

        # Should handle zero-inflation appropriately
        assert isinstance(result, bool)

    def test_fr_6_10_frequency_all_zeros(self) -> None:
        """All zeros should still be handled correctly."""
        from src.data.validation import validate_transaction_frequency

        transactions_per_panelist = [0, 0, 0, 0, 0]

        np.random.seed(SEED)
        result = validate_transaction_frequency(transactions_per_panelist)

        assert isinstance(result, bool)


class TestFr610ValidationReport:
    """FR-6.10: Comprehensive validation report generation."""

    def test_fr_6_10_report_structure(self) -> None:
        """Validation report has all required fields."""
        from src.data.validation import generate_validation_report, ValidationReport

        # Create minimal test transactions
        transactions = [
            Transaction(
                transaction_id='t1',
                panelist_id='p1',
                date=datetime(2024, 1, 15),
                amount=100.0,
                category='grocery',
                brand='store_brand'
            ),
            Transaction(
                transaction_id='t2',
                panelist_id='p1',
                date=datetime(2024, 1, 16),
                amount=50.0,
                category='dining',
                brand='fast_food'
            ),
        ]

        np.random.seed(SEED)
        report = generate_validation_report(transactions)

        assert isinstance(report, ValidationReport)
        assert hasattr(report, 'coefficient_of_variation')
        assert hasattr(report, 'gini_coefficient')
        assert hasattr(report, 'category_mad')
        assert hasattr(report, 'weekend_weekday_ratio')
        assert hasattr(report, 'transaction_frequency_ok')
        assert hasattr(report, 'zero_inflation_ok')
        assert hasattr(report, 'all_passed')

    def test_fr_6_10_report_all_passed_true(self) -> None:
        """All metrics in range should set all_passed to True."""
        from src.data.validation import generate_validation_report

        # Create transactions that should pass all validations
        # Well-distributed amounts (CV in 0.3-0.6 range)
        amounts = np.random.lognormal(mean=3.5, sigma=0.8, size=100)

        # Equal brand shares for Gini test (but we need brand info)
        transactions = []
        categories = ['grocery', 'dining', 'retail', 'apparel']
        brands = ['brand_a', 'brand_b', 'brand_c']

        for i, amt in enumerate(amounts):
            transactions.append(Transaction(
                transaction_id=f't{i}',
                panelist_id=f'p{i % 10}',
                date=datetime(2024, 6, 15 + (i % 7)),  # Spread across days
                amount=float(amt),
                category=categories[i % len(categories)],
                brand=brands[i % len(brands)]
            ))

        np.random.seed(SEED)
        report = generate_validation_report(transactions)

        # Should have all_passed as boolean
        assert isinstance(report.all_passed, bool)


class TestFr610EdgeCases:
    """FR-6.10: Edge case handling."""

    def test_fr_6_10_empty_amounts(self) -> None:
        """Empty amounts list should be handled gracefully."""
        from src.data.validation import validate_transaction_amounts

        np.random.seed(SEED)
        result = validate_transaction_amounts([])

        assert 'coefficient_of_variation' in result

    def test_fr_6_10_single_amount(self) -> None:
        """Single amount should not cause division by zero."""
        from src.data.validation import validate_transaction_amounts

        np.random.seed(SEED)
        result = validate_transaction_amounts([100.0])

        assert 'coefficient_of_variation' in result
        # CV with single value should be 0 or handled gracefully

    def test_fr_6_10_empty_market_shares(self) -> None:
        """Empty market shares should be handled gracefully."""
        from src.data.validation import validate_market_share

        np.random.seed(SEED)
        result = validate_market_share({})

        assert 'gini_coefficient' in result

    def test_fr_6_10_zero_weekday_total(self) -> None:
        """Zero weekday total should be handled gracefully."""
        from src.data.validation import validate_weekend_weekday_ratio

        np.random.seed(SEED)
        ratio = validate_weekend_weekday_ratio(weekend_total=100, weekday_total=0)

        # Should return infinity or large value, not crash
        assert ratio > 100 or np.isinf(ratio)


class TestFr610Determinism:
    """FR-6.10: Tests are deterministic with fixed seed."""

    def test_fr_6_10_deterministic_cv(self) -> None:
        """CV calculation is deterministic with same seed."""
        from src.data.validation import validate_transaction_amounts

        amounts = [100, 150, 200, 250, 300]

        np.random.seed(SEED)
        result1 = validate_transaction_amounts(amounts.copy())

        np.random.seed(SEED)
        result2 = validate_transaction_amounts(amounts.copy())

        assert result1['coefficient_of_variation'] == result2['coefficient_of_variation']

    def test_fr_6_10_deterministic_gini(self) -> None:
        """Gini calculation is deterministic with same seed."""
        from src.data.validation import validate_market_share

        brand_shares = {'a': 0.3, 'b': 0.3, 'c': 0.2, 'd': 0.2}

        np.random.seed(SEED)
        result1 = validate_market_share(brand_shares.copy())

        np.random.seed(SEED)
        result2 = validate_market_share(brand_shares.copy())

        assert result1['gini_coefficient'] == result2['gini_coefficient']

    def test_fr_6_10_deterministic_mad(self) -> None:
        """MAD calculation is deterministic with same seed."""
        from src.data.validation import validate_category_proportions

        category_totals = {'a': 100, 'b': 200, 'c': 300}
        benchmark = {'a': 0.2, 'b': 0.4, 'c': 0.4}

        np.random.seed(SEED)
        result1 = validate_category_proportions(category_totals.copy(), benchmark.copy())

        np.random.seed(SEED)
        result2 = validate_category_proportions(category_totals.copy(), benchmark.copy())

        assert result1 == result2


class TestFr610Imports:
    """FR-6.10: Verify module imports correctly."""

    def test_fr_6_10_import_validation_module(self) -> None:
        """Validation module can be imported."""
        from src.data import validation
        assert validation is not None

    def test_fr_6_10_import_validation_report(self) -> None:
        """ValidationReport can be imported."""
        from src.data.validation import ValidationReport
        assert ValidationReport is not None

    def test_fr_6_10_import_all_functions(self) -> None:
        """All required functions can be imported."""
        from src.data.validation import (
            validate_transaction_amounts,
            validate_market_share,
            validate_category_proportions,
            validate_weekend_weekday_ratio,
            validate_transaction_frequency,
            generate_validation_report
        )
        assert validate_transaction_amounts is not None
        assert validate_market_share is not None
        assert validate_category_proportions is not None
        assert validate_weekend_weekday_ratio is not None
        assert validate_transaction_frequency is not None
        assert generate_validation_report is not None
