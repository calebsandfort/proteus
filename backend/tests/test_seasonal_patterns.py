"""Tests for FR-6.7: Embedded Spending Patterns.

This module tests seasonal adjustments, generational preferences,
and income-brand correlation for synthetic data generation.
"""

import numpy as np
import pytest
from datetime import datetime


# Test constants matching FR-6.7
SEED = 42

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

# Income bands (descriptive string IDs)
INCOME_BAND_HIGH = 'over_200k'  # $200K+

# Categories
RETAIL = 'retail'
GROCERY = 'grocery'
DINING = 'dining'
APPAREL = 'apparel'
HEALTHCARE = 'healthcare'
TRAVEL = 'travel'
HOME_IMPROVEMENT = 'home_improvement'
SCHOOL = 'school'


class TestFr67Q4HolidaySpike:
    """FR-6.7: Holiday Season Q4 spike patterns."""

    def test_fr_6_7_q4_spike_november(self) -> None:
        """November: 25-40% retail volume increase vs. prior-week baseline."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        # November 15 (mid-November)
        november_date = datetime(2024, 11, 15)
        adjusted = apply_seasonal_adjustment(base_amount, november_date, RETAIL)

        # Should be 25-40% higher than baseline
        multiplier = adjusted / base_amount
        assert 1.25 <= multiplier <= 1.40, \
            f"November retail multiplier {multiplier:.2f} not in 1.25-1.40 range"

    def test_fr_6_7_q4_spike_december(self) -> None:
        """December: 25-40% retail volume increase vs. prior-week baseline."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        # December 10 (not peak period)
        december_date = datetime(2024, 12, 10)
        adjusted = apply_seasonal_adjustment(base_amount, december_date, RETAIL)

        # Should be 25-40% higher than baseline
        multiplier = adjusted / base_amount
        assert 1.25 <= multiplier <= 1.40, \
            f"December retail multiplier {multiplier:.2f} not in 1.25-1.40 range"

    def test_fr_6_7_q4_spike_december_peak(self) -> None:
        """December 15-24 peak: +60-100% vs. prior-week baseline."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0

        # Test multiple days in peak period
        for day in range(15, 25):
            np.random.seed(SEED)
            peak_date = datetime(2024, 12, day)
            adjusted = apply_seasonal_adjustment(base_amount, peak_date, RETAIL)

            multiplier = adjusted / base_amount
            assert 1.60 <= multiplier <= 2.00, \
                f"Dec {day} peak multiplier {multiplier:.2f} not in 1.60-2.00 range"

    def test_fr_6_7_q4_spike_non_holiday_month(self) -> None:
        """Non-Q4 months should have no holiday spike (multiplier ~1.0)."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        # July (middle of year, no holiday effect)
        july_date = datetime(2024, 7, 15)
        adjusted = apply_seasonal_adjustment(base_amount, july_date, RETAIL)

        multiplier = adjusted / base_amount
        assert 0.98 <= multiplier <= 1.02, \
            f"July retail multiplier {multiplier:.2f} should be ~1.0"


class TestFr67JanuaryNormalization:
    """FR-6.7: January normalization after Q4 spike."""

    def test_fr_6_7_january_decrease(self) -> None:
        """January: -15-25% vs. Q4 average to balance the spike."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        # January 10 (after New Year's, normal January)
        january_date = datetime(2024, 1, 10)
        adjusted = apply_seasonal_adjustment(base_amount, january_date, RETAIL)

        multiplier = adjusted / base_amount
        assert 0.75 <= multiplier <= 0.85, \
            f"January retail multiplier {multiplier:.2f} not in 0.75-0.85 range"

    def test_fr_6_7_january_vs_q4(self) -> None:
        """January should be significantly lower than Q4."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        january_adjusted = apply_seasonal_adjustment(base_amount, datetime(2024, 1, 15), RETAIL)

        np.random.seed(SEED)
        december_adjusted = apply_seasonal_adjustment(base_amount, datetime(2024, 12, 15), RETAIL)

        # January should be at least 40% lower than December
        assert january_adjusted < december_adjusted * 0.6, \
            f"January ({january_adjusted:.2f}) should be < 60% of December ({december_adjusted:.2f})"


class TestFr67BackToSchool:
    """FR-6.7: Back-to-School seasonal patterns (Aug-Sep)."""

    def test_fr_6_7_back_to_school_august(self) -> None:
        """August: 20-35% increase in school-related categories."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        august_date = datetime(2024, 8, 15)
        adjusted = apply_seasonal_adjustment(base_amount, august_date, SCHOOL)

        multiplier = adjusted / base_amount
        assert 1.20 <= multiplier <= 1.35, \
            f"August school multiplier {multiplier:.2f} not in 1.20-1.35 range"

    def test_fr_6_7_back_to_school_september(self) -> None:
        """September: 20-35% increase in school-related categories."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        september_date = datetime(2024, 9, 10)
        adjusted = apply_seasonal_adjustment(base_amount, september_date, SCHOOL)

        multiplier = adjusted / base_amount
        assert 1.20 <= multiplier <= 1.35, \
            f"September school multiplier {multiplier:.2f} not in 1.20-1.35 range"

    def test_fr_6_7_back_to_school_non_school_category(self) -> None:
        """Back-to-school should NOT apply to non-school categories."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        # August should not significantly affect healthcare
        august_date = datetime(2024, 8, 15)
        adjusted = apply_seasonal_adjustment(base_amount, august_date, HEALTHCARE)

        multiplier = adjusted / base_amount
        assert 0.98 <= multiplier <= 1.02, \
            f"August healthcare multiplier {multiplier:.2f} should be ~1.0 for non-school categories"


class TestFr67WeekendVsWeekday:
    """FR-6.7: Weekend vs. Weekday patterns."""

    def test_fr_6_7_saturday_retail_increase(self) -> None:
        """Saturday: +30-35% vs. Monday baseline for retail."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0

        # Monday baseline
        np.random.seed(SEED)
        monday_date = datetime(2024, 9, 2)  # Monday
        monday_adjusted = apply_seasonal_adjustment(base_amount, monday_date, RETAIL)

        # Saturday
        np.random.seed(SEED)
        saturday_date = datetime(2024, 9, 7)  # Saturday
        saturday_adjusted = apply_seasonal_adjustment(base_amount, saturday_date, RETAIL)

        multiplier = saturday_adjusted / monday_adjusted
        assert 1.30 <= multiplier <= 1.35, \
            f"Saturday/Monday ratio {multiplier:.2f} not in 1.30-1.35 range"

    def test_fr_6_7_sunday_retail_increase(self) -> None:
        """Sunday: Elevated vs Monday for retail."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0

        # Monday baseline
        np.random.seed(SEED)
        monday_date = datetime(2024, 9, 2)  # Monday
        monday_adjusted = apply_seasonal_adjustment(base_amount, monday_date, RETAIL)

        # Sunday
        np.random.seed(SEED)
        sunday_date = datetime(2024, 9, 8)  # Sunday
        sunday_adjusted = apply_seasonal_adjustment(base_amount, sunday_date, RETAIL)

        # Sunday should be higher than Monday baseline
        assert sunday_adjusted > monday_adjusted, \
            f"Sunday ({sunday_adjusted:.2f}) should be elevated vs Monday ({monday_adjusted:.2f})"


class TestFr67GenerationalPreferences:
    """FR-6.7: Generational spending preferences."""

    def test_fr_6_7_gen_z_dining_preference(self) -> None:
        """Gen Z: 22%+ dining/delivery preference (averaged over samples)."""
        from src.data.seasonal_patterns import get_generation_preference

        # Use average over 1000 samples to reduce noise
        np.random.seed(SEED)
        multipliers = [get_generation_preference(GEN_Z, DINING) for _ in range(1000)]
        avg_multiplier = sum(multipliers) / len(multipliers)

        assert avg_multiplier >= 1.20, \
            f"Gen Z dining multiplier {avg_multiplier:.2f} should be >= 1.20 (averaged over 1000 samples)"

    def test_fr_6_7_gen_z_apparel_preference(self) -> None:
        """Gen Z: 16%+ apparel/fast fashion preference (averaged over samples)."""
        from src.data.seasonal_patterns import get_generation_preference

        # Use average over 1000 samples to reduce noise
        np.random.seed(SEED)
        multipliers = [get_generation_preference(GEN_Z, APPAREL) for _ in range(1000)]
        avg_multiplier = sum(multipliers) / len(multipliers)

        assert avg_multiplier >= 1.14, \
            f"Gen Z apparel multiplier {avg_multiplier:.2f} should be >= 1.14 (averaged over 1000 samples)"

    def test_fr_6_7_millennial_grocery_preference(self) -> None:
        """Millennials: 18%+ grocery (family) preference (averaged over samples)."""
        from src.data.seasonal_patterns import get_generation_preference

        # Use average over 1000 samples to reduce noise
        np.random.seed(SEED)
        multipliers = [get_generation_preference(MILLENNIAL, GROCERY) for _ in range(1000)]
        avg_multiplier = sum(multipliers) / len(multipliers)

        assert avg_multiplier >= 1.16, \
            f"Millennial grocery multiplier {avg_multiplier:.2f} should be >= 1.16 (averaged over 1000 samples)"

    def test_fr_6_7_millennial_home_improvement_preference(self) -> None:
        """Millennials: 12%+ home improvement preference (averaged over samples)."""
        from src.data.seasonal_patterns import get_generation_preference

        # Use average over 1000 samples to reduce noise
        np.random.seed(SEED)
        multipliers = [get_generation_preference(MILLENNIAL, HOME_IMPROVEMENT) for _ in range(1000)]
        avg_multiplier = sum(multipliers) / len(multipliers)

        assert avg_multiplier >= 1.10, \
            f"Millennial home improvement multiplier {avg_multiplier:.2f} should be >= 1.10 (averaged over 1000 samples)"

    def test_fr_6_7_boomer_healthcare_preference(self) -> None:
        """Boomers: 28%+ healthcare preference (averaged over samples)."""
        from src.data.seasonal_patterns import get_generation_preference

        # Use average over 1000 samples to reduce noise
        np.random.seed(SEED)
        multipliers = [get_generation_preference(BOOMER, HEALTHCARE) for _ in range(1000)]
        avg_multiplier = sum(multipliers) / len(multipliers)

        assert avg_multiplier >= 1.26, \
            f"Boomer healthcare multiplier {avg_multiplier:.2f} should be >= 1.26 (averaged over 1000 samples)"

    def test_fr_6_7_boomer_travel_preference(self) -> None:
        """Boomers: 14%+ travel preference (averaged over samples)."""
        from src.data.seasonal_patterns import get_generation_preference

        # Use average over 1000 samples to reduce noise
        np.random.seed(SEED)
        multipliers = [get_generation_preference(BOOMER, TRAVEL) for _ in range(1000)]
        avg_multiplier = sum(multipliers) / len(multipliers)

        assert avg_multiplier >= 1.12, \
            f"Boomer travel multiplier {avg_multiplier:.2f} should be >= 1.12 (averaged over 1000 samples)"


class TestFr67IncomeBrandCorrelation:
    """FR-6.7: Income-brand preference correlation."""

    def test_fr_6_7_high_income_premium_preference(self) -> None:
        """High-income ($150K+): 70-80% premium/luxury brand preference."""
        from src.data.seasonal_patterns import get_income_brand_preference

        np.random.seed(SEED)
        premium_pref = get_income_brand_preference(INCOME_BAND_HIGH, PREMIUM)

        # Premium preference should be 70-80% (represented as 0.70-0.80)
        assert 0.70 <= premium_pref <= 0.80, \
            f"High income premium preference {premium_pref:.2f} not in 0.70-0.80 range"

    def test_fr_6_7_high_income_luxury_preference(self) -> None:
        """High-income ($150K+): 55-70% luxury brand preference."""
        from src.data.seasonal_patterns import get_income_brand_preference

        np.random.seed(SEED)
        luxury_pref = get_income_brand_preference(INCOME_BAND_HIGH, LUXURY)

        # Luxury preference for high income should be strong (0.55-0.70)
        assert 0.55 <= luxury_pref <= 0.70, \
            f"High income luxury preference {luxury_pref:.2f} not in 0.55-0.70 range"

    def test_fr_6_7_high_income_mid_tier_preference(self) -> None:
        """High-income ($150K+): 15-25% mid-market preference."""
        from src.data.seasonal_patterns import get_income_brand_preference

        np.random.seed(SEED)
        mid_tier_pref = get_income_brand_preference(INCOME_BAND_HIGH, MID_TIER)

        # Mid-tier preference should be 15-25%
        assert 0.15 <= mid_tier_pref <= 0.25, \
            f"High income mid-tier preference {mid_tier_pref:.2f} not in 0.15-0.25 range"

    def test_fr_6_7_high_income_value_preference(self) -> None:
        """High-income ($150K+): 0-5% value-tier preference."""
        from src.data.seasonal_patterns import get_income_brand_preference

        np.random.seed(SEED)
        value_pref = get_income_brand_preference(INCOME_BAND_HIGH, VALUE)

        # Value preference should be very low (0-5%)
        assert 0.00 <= value_pref <= 0.05, \
            f"High income value preference {value_pref:.2f} not in 0.00-0.05 range"

    def test_fr_6_7_high_income_walmart_preference(self) -> None:
        """Walmart transactions for income band 6 ($150K+) <2% of total."""
        from src.data.seasonal_patterns import get_income_brand_preference

        np.random.seed(SEED)
        walmart_pref = get_income_brand_preference(INCOME_BAND_HIGH, WALMART)

        # Walmart preference for high income should be <2%
        assert walmart_pref < 0.02, \
            f"High income Walmart preference {walmart_pref:.4f} should be < 0.02"


class TestFr67IncomeBrandPearsonCorrelation:
    """FR-6.7: Income-brand Pearson correlation coefficients."""

    def test_fr_6_7_premium_pearson_correlation(self) -> None:
        """Premium brands: Pearson coefficient should be positive with income."""
        from src.data.seasonal_patterns import calculate_brand_income_correlation

        np.random.seed(SEED)

        # Simulate premium brand purchases across income bands
        premium_coeff = calculate_brand_income_correlation(PREMIUM)

        # Correlation should be positive (higher income -> higher premium preference)
        assert premium_coeff > 0, \
            f"Premium Pearson coefficient {premium_coeff:.2f} should be positive"

    def test_fr_6_7_luxury_pearson_correlation(self) -> None:
        """Luxury brands: Pearson coefficient should be positive with income."""
        from src.data.seasonal_patterns import calculate_brand_income_correlation

        np.random.seed(SEED)

        luxury_coeff = calculate_brand_income_correlation(LUXURY)

        # Correlation should be positive (higher income -> higher luxury preference)
        assert luxury_coeff > 0, \
            f"Luxury Pearson coefficient {luxury_coeff:.2f} should be positive"


class TestFr67Integration:
    """FR-6.7: Integration tests combining multiple factors."""

    def test_fr_6_7_combined_seasonal_and_generation(self) -> None:
        """Gen Z shopping on Black Friday should combine both effects."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment, get_generation_preference

        base_amount = 100.0

        # Black Friday (peak Q4)
        np.random.seed(SEED)
        black_friday = datetime(2024, 11, 29)
        seasonal_adj = apply_seasonal_adjustment(base_amount, black_friday, RETAIL)

        np.random.seed(SEED)
        gen_z_adj = get_generation_preference(GEN_Z, RETAIL)

        # Both should be > 1.0 (combined effect is multiplicative)
        assert seasonal_adj > base_amount
        assert gen_z_adj >= 1.0

    def test_fr_6_7_low_income_walmart_preference(self) -> None:
        """Lower income should have higher Walmart preference."""
        from src.data.seasonal_patterns import get_income_brand_preference

        np.random.seed(SEED)
        low_income_walmart = get_income_brand_preference('under_25k', WALMART)  # Lowest income band
        high_income_walmart = get_income_brand_preference(INCOME_BAND_HIGH, WALMART)

        assert low_income_walmart > high_income_walmart, \
            f"Low income Walmart ({low_income_walmart:.4f}) should be > high income ({high_income_walmart:.4f})"

    def test_fr_6_7_consistency_across_calls(self) -> None:
        """Same inputs should produce same outputs (deterministic)."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment, get_generation_preference

        base_amount = 100.0
        test_date = datetime(2024, 12, 15)
        test_category = RETAIL
        test_generation = GEN_Z

        # Multiple calls with same seed should give same result
        np.random.seed(SEED)
        result1 = apply_seasonal_adjustment(base_amount, test_date, test_category)

        np.random.seed(SEED)
        result2 = apply_seasonal_adjustment(base_amount, test_date, test_category)

        assert result1 == result2, "Same inputs should produce same outputs"

        # Same for generation preference
        np.random.seed(SEED)
        gen_result1 = get_generation_preference(test_generation, test_category)

        np.random.seed(SEED)
        gen_result2 = get_generation_preference(test_generation, test_category)

        assert gen_result1 == gen_result2, "Same generation inputs should produce same outputs"


class TestFr67EdgeCases:
    """FR-6.7: Edge cases and boundary conditions."""

    def test_fr_6_7_leap_year_february(self) -> None:
        """February 29 in leap year should not cause errors."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0
        np.random.seed(SEED)

        leap_day = datetime(2024, 2, 29)  # 2024 is a leap year
        adjusted = apply_seasonal_adjustment(base_amount, leap_day, RETAIL)

        assert adjusted > 0

    def test_fr_6_7_year_boundary_dec_jan(self) -> None:
        """Year boundary between December and January should be smooth."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        base_amount = 100.0

        np.random.seed(SEED)
        late_december = apply_seasonal_adjustment(base_amount, datetime(2024, 12, 30), RETAIL)

        np.random.seed(SEED)
        early_january = apply_seasonal_adjustment(base_amount, datetime(2025, 1, 2), RETAIL)

        # December should be higher than January (Q4 spike vs normalization)
        assert late_december > early_january

    def test_fr_6_7_unknown_generation(self) -> None:
        """Unknown generation should raise ValueError."""
        from src.data.seasonal_patterns import get_generation_preference

        with pytest.raises(ValueError):
            get_generation_preference('unknown_gen', DINING)

    def test_fr_6_7_unknown_category(self) -> None:
        """Unknown category in generational preference should raise ValueError."""
        from src.data.seasonal_patterns import get_generation_preference

        with pytest.raises(ValueError):
            get_generation_preference(GEN_Z, 'unknown_category')

    def test_fr_6_7_unknown_brand_tier(self) -> None:
        """Unknown brand tier should raise ValueError."""
        from src.data.seasonal_patterns import get_income_brand_preference

        with pytest.raises(ValueError):
            get_income_brand_preference(INCOME_BAND_HIGH, 'unknown_tier')

    def test_fr_6_7_invalid_income_band(self) -> None:
        """Invalid income band should raise ValueError."""
        from src.data.seasonal_patterns import get_income_brand_preference

        with pytest.raises(ValueError):
            get_income_brand_preference(0, PREMIUM)  # Band 0 doesn't exist

        with pytest.raises(ValueError):
            get_income_brand_preference(7, PREMIUM)  # Band 7 doesn't exist
