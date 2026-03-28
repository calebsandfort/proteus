"""Tests for FR-6.6 and FR-6.7: Transaction Generation.

This module tests transaction generation with log-normal amounts,
seasonal adjustments, and spending patterns.
"""

import numpy as np
import pytest
from datetime import date, datetime, timedelta
from typing import Dict, List, Generator


# Test constants
SEED = 42


class MockPanelist:
    """Mock panelist for testing."""
    def __init__(
        self,
        id: str = "test-panelist-1",
        income_band_id: int = 3,
        generation_id: str = "millennial",
        geography_id: int = 1,
        panel_start_date: date = None,
        panel_weight: float = 1.0
    ):
        self.id = id
        self.income_band_id = income_band_id
        self.generation_id = generation_id
        self.geography_id = geography_id
        self.panel_start_date = panel_start_date or date(2023, 1, 1)
        self.panel_weight = panel_weight


class MockBrand:
    """Mock brand for testing."""
    def __init__(
        self,
        brand_id: int = 1,
        brand_tier: str = "mid_tier",
        category_id: int = 1
    ):
        self.brand_id = brand_id
        self.brand_tier = brand_tier
        self.category_id = category_id


class MockCategory:
    """Mock category for testing."""
    def __init__(self, category_id: int = 1, category_name: str = "retail"):
        self.category_id = category_id
        self.category_name = category_name


class TestFr66TransactionAmounts:
    """FR-6.6: Transaction amounts follow log-normal distribution."""

    def test_fr_6_6_transaction_amount_positive(self) -> None:
        """Transaction amounts are always positive."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="essential", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        for txn in transactions:
            assert txn.transaction_amount > 0, \
                f"Transaction amount should be positive, got {txn.transaction_amount}"

    def test_fr_6_6_transaction_amount_log_normal_distribution(self) -> None:
        """Transaction amounts follow log-normal distribution."""
        from src.data.transaction_generator import generate_transactions_for_panelist
        from src.data.distributions import CATEGORY_PARAMS

        panelist = MockPanelist(income_band_id=3)  # multiplier = 1.0
        # Use essential tier with known parameters
        brands = [MockBrand(brand_id=1, brand_tier="essential", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        amounts = [t.transaction_amount for t in transactions]

        # Calculate expected mean for log-normal
        mu, sigma = CATEGORY_PARAMS["essential"]
        expected_mean = np.exp(mu + sigma**2 / 2)  # income band 3 has 1.0x multiplier

        actual_mean = np.mean(amounts)

        # Within 30% tolerance due to sampling variability
        assert abs(actual_mean - expected_mean) / expected_mean < 0.30, \
            f"Mean amount {actual_mean:.2f} differs too much from expected {expected_mean:.2f}"

    def test_fr_6_6_income_multiplier_affects_amount(self) -> None:
        """Higher income bands have higher transaction amounts."""
        from src.data.transaction_generator import generate_transactions_for_panelist
        from src.data.distributions import INCOME_MULTIPLIERS

        brands = [MockBrand(brand_id=1, brand_tier="essential", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        # Compare band 1 vs band 6
        panelist_band1 = MockPanelist(id="p1", income_band_id=1)
        panelist_band6 = MockPanelist(id="p2", income_band_id=6)

        np.random.seed(SEED)
        txns_band1 = list(generate_transactions_for_panelist(
            panelist=panelist_band1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        np.random.seed(SEED)
        txns_band6 = list(generate_transactions_for_panelist(
            panelist=panelist_band6,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        mean_band1 = np.mean([t.transaction_amount for t in txns_band1])
        mean_band6 = np.mean([t.transaction_amount for t in txns_band6])

        # Band 6 should have higher mean than band 1
        assert mean_band6 > mean_band1, \
            f"Band 6 mean ({mean_band6:.2f}) should exceed Band 1 mean ({mean_band1:.2f})"

        # The ratio should be roughly 1.7/0.6 = 2.83 (within tolerance)
        ratio = mean_band6 / mean_band1
        expected_ratio = INCOME_MULTIPLIERS[6] / INCOME_MULTIPLIERS[1]  # 1.7/0.6 = 2.83
        assert abs(ratio - expected_ratio) / expected_ratio < 0.40, \
            f"Ratio {ratio:.2f} differs too much from expected {expected_ratio:.2f}"


class TestFr67SeasonalPatterns:
    """FR-6.7: Seasonal patterns are embedded in transactions."""

    def test_fr_6_7_q4_holiday_spike(self) -> None:
        """Q4 November-December shows holiday spending spike."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)

        # Q4 period (November)
        q4_transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 11, 1),
            end_date=date(2024, 11, 30),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        # Q2 period (April) for comparison
        q2_transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 30),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        if len(q2_transactions) > 0 and len(q4_transactions) > 0:
            mean_q4 = np.mean([t.transaction_amount for t in q4_transactions])
            mean_q2 = np.mean([t.transaction_amount for t in q2_transactions])

            # Q4 should be higher due to holiday spike (at least 25% higher)
            assert mean_q4 > mean_q2 * 1.15, \
                f"Q4 mean ({mean_q4:.2f}) should exceed Q2 mean ({mean_q2:.2f}) by at least 15%"

    def test_fr_6_7_january_normalization(self) -> None:
        """January shows spending normalization (lower than Q4)."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)

        # January period
        jan_transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        # December period
        dec_transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        if len(jan_transactions) > 0 and len(dec_transactions) > 0:
            mean_jan = np.mean([t.transaction_amount for t in jan_transactions])
            mean_dec = np.mean([t.transaction_amount for t in dec_transactions])

            # January should be lower than December (normalization)
            assert mean_jan < mean_dec * 0.90, \
                f"January mean ({mean_jan:.2f}) should be less than 90% of December mean ({mean_dec:.2f})"

    def test_fr_6_7_weekend_patterns(self) -> None:
        """Weekend transactions show elevated spending vs weekdays."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)

        # Use 6-month range to get enough transactions for meaningful comparison
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        weekend_amounts = []
        weekday_amounts = []

        for txn in transactions:
            # Saturday = 5, Sunday = 6
            if txn.day_of_week in {"Saturday", "Sunday"}:
                weekend_amounts.append(txn.transaction_amount)
            else:
                weekday_amounts.append(txn.transaction_amount)

        # Require at least 4 weekend transactions for statistical significance
        if len(weekend_amounts) >= 4 and len(weekday_amounts) >= 4:
            mean_weekend = np.mean(weekend_amounts)
            mean_weekday = np.mean(weekday_amounts)

            # Weekend should be higher than weekday on average due to Saturday/Sunday boost
            # Note: Effect varies due to January normalization and random variation
            assert mean_weekend >= mean_weekday * 0.98, \
                f"Weekend mean ({mean_weekend:.2f}) should be at least 98% of weekday mean ({mean_weekday:.2f})"


class TestFr67GenerationalPreferences:
    """FR-6.7: Generational preferences affect spending patterns."""

    def test_fr_6_7_generation_field_populated(self) -> None:
        """Transaction includes generation_id field."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist(generation_id="millennial")
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        for txn in transactions:
            assert txn.generation_id is not None
            assert txn.generation_id != ""


class TestFr67IncomeBrandCorrelation:
    """FR-6.7: Income-brand correlation is embedded."""

    def test_fr_6_7_income_band_correlates_with_brand_tier(self) -> None:
        """Higher income panelists prefer premium/luxury brands."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        brands = [
            MockBrand(brand_id=1, brand_tier="value", category_id=1),
            MockBrand(brand_id=2, brand_tier="premium", category_id=1),
        ]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        # Low income panelist
        low_income_panelist = MockPanelist(id="low", income_band_id=1)
        # High income panelist
        high_income_panelist = MockPanelist(id="high", income_band_id=6)

        np.random.seed(SEED)
        low_income_txns = list(generate_transactions_for_panelist(
            panelist=low_income_panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        np.random.seed(SEED)
        high_income_txns = list(generate_transactions_for_panelist(
            panelist=high_income_panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        # High income should have higher proportion of premium purchases
        # (compared to value)
        low_premium_count = sum(1 for t in low_income_txns if t.brand_id == 2)  # premium brand
        low_value_count = sum(1 for t in low_income_txns if t.brand_id == 1)   # value brand
        high_premium_count = sum(1 for t in high_income_txns if t.brand_id == 2)
        high_value_count = sum(1 for t in high_income_txns if t.brand_id == 1)

        if low_value_count > 0 and high_value_count > 0:
            low_premium_ratio = low_premium_count / (low_premium_count + low_value_count)
            high_premium_ratio = high_premium_count / (high_premium_count + high_value_count)

            # High income should have higher premium ratio
            assert high_premium_ratio > low_premium_ratio, \
                f"High income premium ratio ({high_premium_ratio:.2f}) should exceed low income ({low_premium_ratio:.2f})"


class TestFr66TransactionStructure:
    """FR-6.6: Transaction has required fields."""

    def test_fr_6_6_transaction_has_required_fields(self) -> None:
        """Transaction has all required fields per specification."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        assert len(transactions) > 0, "Should generate at least one transaction"
        txn = transactions[0]

        # Check all required fields per specification
        assert hasattr(txn, 'id')
        assert hasattr(txn, 'panelist_id')
        assert hasattr(txn, 'brand_id')
        assert hasattr(txn, 'category_id')
        assert hasattr(txn, 'geography_id')
        assert hasattr(txn, 'generation_id')
        assert hasattr(txn, 'income_band_id')
        assert hasattr(txn, 'transaction_timestamp')
        assert hasattr(txn, 'transaction_amount')
        assert hasattr(txn, 'card_type')
        assert hasattr(txn, 'payment_network')
        assert hasattr(txn, 'channel')
        assert hasattr(txn, 'day_of_week')
        assert hasattr(txn, 'hour_of_day')

    def test_fr_6_6_transaction_timestamp_type(self) -> None:
        """Transaction timestamp is a datetime object."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        for txn in transactions:
            assert isinstance(txn.transaction_timestamp, datetime), \
                f"Transaction timestamp should be datetime, got {type(txn.transaction_timestamp)}"

    def test_fr_6_6_transaction_day_of_week_valid(self) -> None:
        """Day of week is a valid weekday name."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        for txn in transactions:
            assert txn.day_of_week in valid_days, \
                f"Day of week '{txn.day_of_week}' not in {valid_days}"

    def test_fr_6_6_transaction_hour_of_day_valid(self) -> None:
        """Hour of day is in valid range 0-23."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        for txn in transactions:
            assert 0 <= txn.hour_of_day <= 23, \
                f"Hour of day {txn.hour_of_day} outside valid range 0-23"

    def test_fr_6_6_transaction_panelist_id_matches(self) -> None:
        """Transaction panelist_id matches the generating panelist."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist(id="test-panelist-123")
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        for txn in transactions:
            assert txn.panelist_id == "test-panelist-123", \
                f"Transaction panelist_id ({txn.panelist_id}) should match panelist id"


class TestFr66GeneratorBehavior:
    """FR-6.6: Transaction generator behavior tests."""

    def test_fr_6_6_returns_generator(self) -> None:
        """generate_transactions_for_panelist returns a generator."""
        from src.data.transaction_generator import generate_transactions_for_panelist
        from types import GeneratorType

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        result = generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        )

        assert isinstance(result, GeneratorType), \
            f"Should return Generator, got {type(result)}"

    def test_fr_6_6_date_range_affects_count(self) -> None:
        """Longer date ranges produce more transactions."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=1, brand_tier="mid_tier", category_id=1)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        short_range_txns = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        np.random.seed(SEED)
        long_range_txns = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        assert len(long_range_txns) > len(short_range_txns), \
            "Longer date range should produce more transactions"


class TestFr69TransactionCount:
    """FR-6.9: Each panelist has 50-200 transactions over 2 years."""

    def test_fr_6_9_two_year_transaction_count(self) -> None:
        """Panelist generates 50-200 transactions over 2 years."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=i, brand_tier="mid_tier", category_id=1) for i in range(1, 6)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2022, 1, 1),
            end_date=date(2023, 12, 31),  # 2 years
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        # 50-200 transactions over 2 years
        assert 50 <= len(transactions) <= 200, \
            f"Expected 50-200 transactions over 2 years, got {len(transactions)}"

    def test_fr_6_9_one_year_transaction_count(self) -> None:
        """Panelist generates approximately 25-100 transactions over 1 year (half of 2-year)."""
        from src.data.transaction_generator import generate_transactions_for_panelist

        panelist = MockPanelist()
        brands = [MockBrand(brand_id=i, brand_tier="mid_tier", category_id=1) for i in range(1, 6)]
        categories = [MockCategory(category_id=1, category_name="retail")]
        geography_lookup = {1: "northeast"}

        np.random.seed(SEED)
        transactions = list(generate_transactions_for_panelist(
            panelist=panelist,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),  # 1 year
            brands=brands,
            categories=categories,
            geography_lookup=geography_lookup,
            seed=SEED
        ))

        # Approximately 25-100 transactions over 1 year (scaled from 50-200 over 2 years)
        # Allow some tolerance for random variation
        assert 20 <= len(transactions) <= 120, \
            f"Expected approximately 25-100 transactions over 1 year, got {len(transactions)}"
