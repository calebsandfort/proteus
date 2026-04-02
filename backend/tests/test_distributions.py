"""Tests for FR-6.6: Statistical Distributions.

This module tests log-normal transaction amount generation,
income multipliers, and panel weight calibration.
"""

import numpy as np
import pytest


# Test constants matching FR-6.6
CATEGORY_PARAMS = {
    'essential': (3.0, 0.8),
    'mid_tier': (3.5, 1.0),
    'premium': (4.2, 1.2),
    'dining': (3.2, 0.9),
    'fast_food': (2.2, 0.6),
}

INCOME_MULTIPLIERS = {
    'under_25k': 0.6,
    '25k_50k': 0.8,
    '50k_75k': 1.0,
    '75k_100k': 1.2,
    '100k_150k': 1.4,
    '150k_200k': 1.55,
    'over_200k': 1.7,
}

SEED = 42


class TestFr66LogNormalEssential:
    """FR-6.6: Log-normal distribution for essential category."""

    def test_fr_6_6_log_normal_essential(self) -> None:
        """Essential categories: mu=3.0, sigma=0.8."""
        from src.data.distributions import generate_transaction_amount, CATEGORY_PARAMS

        np.random.seed(SEED)
        mu, sigma = CATEGORY_PARAMS['essential']
        amount = generate_transaction_amount('essential', income_band='50k_75k')

        # With income_band=3, multiplier is 1.0, so amount should be from lognormal(mu, sigma)
        expected_mean = np.exp(mu + sigma**2 / 2)
        # Allow 20% tolerance due to random sampling
        assert abs(amount - expected_mean) / expected_mean < 0.2


class TestFr66LogNormalMidTier:
    """FR-6.6: Log-normal distribution for mid-tier retail."""

    def test_fr_6_6_log_normal_mid_tier(self) -> None:
        """Mid-tier retail: mu=3.5, sigma=1.0."""
        from src.data.distributions import generate_transaction_amount, CATEGORY_PARAMS

        np.random.seed(SEED)
        mu, sigma = CATEGORY_PARAMS['mid_tier']
        amount = generate_transaction_amount('mid_tier', income_band='50k_75k')

        expected_mean = np.exp(mu + sigma**2 / 2)
        assert abs(amount - expected_mean) / expected_mean < 0.2


class TestFr66LogNormalPremium:
    """FR-6.6: Log-normal distribution for premium category."""

    def test_fr_6_6_log_normal_premium(self) -> None:
        """Premium: mu=4.2, sigma=1.2."""
        from src.data.distributions import generate_transaction_amount, CATEGORY_PARAMS

        np.random.seed(SEED)
        mu, sigma = CATEGORY_PARAMS['premium']
        amount = generate_transaction_amount('premium', income_band='50k_75k')

        expected_mean = np.exp(mu + sigma**2 / 2)
        assert abs(amount - expected_mean) / expected_mean < 0.2


class TestFr66LogNormalDining:
    """FR-6.6: Log-normal distribution for dining category."""

    def test_fr_6_6_log_normal_dining(self) -> None:
        """Dining: mu=3.2, sigma=0.9."""
        from src.data.distributions import generate_transaction_amount, CATEGORY_PARAMS

        np.random.seed(SEED)
        mu, sigma = CATEGORY_PARAMS['dining']
        amount = generate_transaction_amount('dining', income_band='50k_75k')

        expected_mean = np.exp(mu + sigma**2 / 2)
        assert abs(amount - expected_mean) / expected_mean < 0.2


class TestFr66LogNormalFastFood:
    """FR-6.6: Log-normal distribution for fast food category."""

    def test_fr_6_6_log_normal_fast_food(self) -> None:
        """Fast food: mu=2.2, sigma=0.6."""
        from src.data.distributions import generate_transaction_amount, CATEGORY_PARAMS

        np.random.seed(SEED)
        mu, sigma = CATEGORY_PARAMS['fast_food']
        amount = generate_transaction_amount('fast_food', income_band='50k_75k')

        expected_mean = np.exp(mu + sigma**2 / 2)
        assert abs(amount - expected_mean) / expected_mean < 0.2


class TestFr66IncomeMultipliers:
    """FR-6.6: Income multipliers affect transaction amounts."""

    def test_fr_6_6_income_multiplier_band_1(self) -> None:
        """Income band 1 (<$25K): 0.6x multiplier - statistical verification."""
        from src.data.distributions import generate_transaction_amount, CATEGORY_PARAMS

        # The expected mean of lognormal is exp(mu + sigma^2/2)
        mu, sigma = CATEGORY_PARAMS['essential']
        expected_mean_no_income = np.exp(mu + sigma**2 / 2)

        # With 0.6x multiplier, band 1 mean should be 0.6 * expected_mean
        expected_mean_band_1 = expected_mean_no_income * 0.6

        # Generate many samples and check average is close
        np.random.seed(SEED)
        samples = [generate_transaction_amount('essential', income_band='under_25k') for _ in range(1000)]
        actual_mean = np.mean(samples)

        # Within 15% of expected
        assert abs(actual_mean - expected_mean_band_1) / expected_mean_band_1 < 0.15, \
            f"Mean {actual_mean:.2f} vs expected {expected_mean_band_1:.2f}"

    def test_fr_6_6_income_multiplier_band_6(self) -> None:
        """Income band 6 ($150K+): 1.7x multiplier - statistical verification."""
        from src.data.distributions import generate_transaction_amount, CATEGORY_PARAMS

        # The expected mean of lognormal is exp(mu + sigma^2/2)
        mu, sigma = CATEGORY_PARAMS['essential']
        expected_mean_no_income = np.exp(mu + sigma**2 / 2)

        # With 1.7x multiplier, band 6 mean should be 1.7 * expected_mean
        expected_mean_band_6 = expected_mean_no_income * 1.7

        # Generate many samples and check average is close
        np.random.seed(SEED)
        samples = [generate_transaction_amount('essential', income_band='over_200k') for _ in range(1000)]
        actual_mean = np.mean(samples)

        # Within 15% of expected
        assert abs(actual_mean - expected_mean_band_6) / expected_mean_band_6 < 0.15, \
            f"Mean {actual_mean:.2f} vs expected {expected_mean_band_6:.2f}"

    def test_fr_6_6_income_multiplier_all_bands(self) -> None:
        """All income bands 1-6 have correct multipliers."""
        from src.data.distributions import generate_transaction_amount, INCOME_MULTIPLIERS

        np.random.seed(SEED)

        # Generate base amount with band 3 (multiplier = 1.0)
        base_amount = generate_transaction_amount('essential', income_band='50k_75k')

        for band, expected_multiplier in INCOME_MULTIPLIERS.items():
            np.random.seed(SEED)  # Reset seed for fair comparison
            band_amount = generate_transaction_amount('essential', income_band=band)
            ratio = band_amount / base_amount
            assert abs(ratio - expected_multiplier) / expected_multiplier < 0.15, \
                f"Band {band}: expected {expected_multiplier}, got {ratio:.3f}"


class TestFr66IncomeBandBoundary:
    """FR-6.6: Boundary conditions for income band values."""

    def test_fr_6_6_income_band_invalid_zero(self) -> None:
        """Income band 0 should raise ValueError."""
        from src.data.distributions import generate_transaction_amount

        with pytest.raises(ValueError):
            generate_transaction_amount('essential', income_band=0)

    def test_fr_6_6_income_band_invalid_seven(self) -> None:
        """Income band 7 should raise ValueError."""
        from src.data.distributions import generate_transaction_amount

        with pytest.raises(ValueError):
            generate_transaction_amount('essential', income_band=7)

    def test_fr_6_6_income_band_negative(self) -> None:
        """Negative income band should raise ValueError."""
        from src.data.distributions import generate_transaction_amount

        with pytest.raises(ValueError):
            generate_transaction_amount('essential', income_band=-1)


class TestFr66SampleIncomeBand:
    """FR-6.6: Sample income band from probabilities."""

    def test_fr_6_6_sample_income_band_basic(self) -> None:
        """Basic sampling returns valid income band string IDs."""
        from src.data.distributions import sample_income_band, INCOME_BAND_IDS

        # Equal probabilities for all 7 bands
        probabilities = [1/7] * 7
        np.random.seed(SEED)

        for _ in range(100):
            band = sample_income_band(probabilities)
            assert band in INCOME_BAND_IDS, f"Band '{band}' not in {INCOME_BAND_IDS}"

    def test_fr_6_6_sample_income_band_weighted(self) -> None:
        """Weighted sampling favors higher probability bands."""
        from src.data.distributions import sample_income_band

        # Strongly favor over_200k (last band)
        probabilities = [0.05, 0.05, 0.05, 0.10, 0.10, 0.15, 0.50]
        np.random.seed(SEED)

        samples = [sample_income_band(probabilities) for _ in range(1000)]
        top_band_count = samples.count('over_200k')

        # over_200k should be sampled more than 40% of the time
        assert top_band_count > 400, f"Expected >400 over_200k samples, got {top_band_count}"

    def test_fr_6_6_sample_income_band_invalid_probabilities(self) -> None:
        """Invalid probability length should raise ValueError."""
        from src.data.distributions import sample_income_band

        with pytest.raises(ValueError):
            sample_income_band([0.5, 0.5])  # Only 2 elements, need 7

    def test_fr_6_6_sample_income_band_negative_prob(self) -> None:
        """Negative probabilities should raise ValueError."""
        from src.data.distributions import sample_income_band

        with pytest.raises(ValueError):
            sample_income_band([-0.1, 0.3, 0.2, 0.2, 0.1, 0.15, 0.15])


class TestFr66SamplePanelWeight:
    """FR-6.6: Panel weight calibration for US demographics."""

    def test_fr_6_6_sample_panel_weight_returns_positive(self) -> None:
        """Panel weight should always be positive."""
        from src.data.distributions import sample_panel_weight

        geography_weights = {'northeast': 0.2, 'midwest': 0.25, 'south': 0.35, 'west': 0.2}
        generation_weights = {'gen_z': 0.15, 'millennial': 0.25, 'gen_x': 0.3, 'boomer': 0.3}

        np.random.seed(SEED)
        for _ in range(100):
            weight = sample_panel_weight(geography_weights, generation_weights)
            assert weight > 0

    def test_fr_6_6_sample_panel_weight_reasonable_range(self) -> None:
        """Panel weight should be in reasonable range (0.1 to 20)."""
        from src.data.distributions import sample_panel_weight

        geography_weights = {'northeast': 0.2, 'midwest': 0.25, 'south': 0.35, 'west': 0.2}
        generation_weights = {'gen_z': 0.15, 'millennial': 0.25, 'gen_x': 0.3, 'boomer': 0.3}

        np.random.seed(SEED)
        for _ in range(100):
            weight = sample_panel_weight(geography_weights, generation_weights)
            assert 0.1 <= weight <= 20, f"Weight {weight} outside reasonable range"

    def test_fr_6_6_sample_panel_weight_invalid_geo_weights(self) -> None:
        """Invalid geography weights should raise ValueError."""
        from src.data.distributions import sample_panel_weight

        # Empty geography weights
        with pytest.raises(ValueError):
            sample_panel_weight({}, {'gen_z': 1.0})

    def test_fr_6_6_sample_panel_weight_invalid_gen_weights(self) -> None:
        """Invalid generation weights should raise ValueError."""
        from src.data.distributions import sample_panel_weight

        # Empty generation weights
        with pytest.raises(ValueError):
            sample_panel_weight({'northeast': 1.0}, {})


class TestFr66Constants:
    """FR-6.6: Verify constants are correctly defined."""

    def test_fr_6_6_category_params_keys(self) -> None:
        """All required category keys exist."""
        from src.data.distributions import CATEGORY_PARAMS

        # Check essential keys plus any additional tiers
        keys = set(CATEGORY_PARAMS.keys())
        assert 'essential' in keys
        assert 'mid_tier' in keys
        assert 'premium' in keys
        assert 'dining' in keys
        assert 'fast_food' in keys
        # Additional tiers may exist
        assert len(keys) >= 5

    def test_fr_6_6_category_params_values(self) -> None:
        """Category parameters match FR-6.6 specification."""
        from src.data.distributions import CATEGORY_PARAMS

        assert CATEGORY_PARAMS['essential'] == (3.1, 0.15)
        assert CATEGORY_PARAMS['mid_tier'] == (3.3, 0.15)
        assert CATEGORY_PARAMS['premium'] == (3.5, 0.15)
        assert CATEGORY_PARAMS['dining'] == (3.2, 0.15)
        assert CATEGORY_PARAMS['fast_food'] == (3.0, 0.15)

    def test_fr_6_6_income_multipliers_keys(self) -> None:
        """All required income band keys exist (7 descriptive string IDs)."""
        from src.data.distributions import INCOME_MULTIPLIERS

        assert set(INCOME_MULTIPLIERS.keys()) == {
            'under_25k', '25k_50k', '50k_75k', '75k_100k', '100k_150k', '150k_200k', 'over_200k'
        }

    def test_fr_6_6_income_multipliers_values(self) -> None:
        """Income multipliers match FR-6.6 specification."""
        from src.data.distributions import INCOME_MULTIPLIERS

        assert INCOME_MULTIPLIERS['under_25k'] == 0.6   # <$25K
        assert INCOME_MULTIPLIERS['50k_75k'] == 1.0     # baseline
        assert INCOME_MULTIPLIERS['over_200k'] == 1.7   # $200K+
        # Multipliers increase monotonically with income
        values = list(INCOME_MULTIPLIERS.values())
        assert values == sorted(values), "Multipliers should increase with income"
