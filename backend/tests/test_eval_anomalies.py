"""Test suite for AnomalyTestCase definitions (FR-7.5)."""

import pytest
from src.eval.anomalies import (
    ANOMALY_TEST_CASES,
    AnomalyType,
    AnomalyTestCase,
    get_anomaly_by_name,
    get_anomalies_by_category,
)


class TestAnomalyCategories:
    """Tests for anomaly categories (FR-7.5)."""

    def test_anomaly_count(self):
        """Test that at least 5 anomaly test cases are defined."""
        assert len(ANOMALY_TEST_CASES) >= 5

    def test_seasonal_anomalies_exist(self):
        """Test seasonal pattern anomalies exist."""
        seasonal = get_anomalies_by_category("seasonal")
        assert len(seasonal) >= 2

    def test_event_anomalies_exist(self):
        """Test COVID-style event anomalies exist."""
        events = get_anomalies_by_category("event")
        assert len(events) >= 2

    def test_trend_anomalies_exist(self):
        """Test secular trend anomalies exist."""
        trends = get_anomalies_by_category("trend")
        assert len(trends) >= 2


class TestAnomalyTypes:
    """Tests for AnomalyType definitions."""

    def test_all_anomaly_types_defined(self):
        """Test all anomaly types are available."""
        assert hasattr(AnomalyType, "SEASONAL")
        assert hasattr(AnomalyType, "CHANNEL_SHIFT")
        assert hasattr(AnomalyType, "SECULAR_TREND")
        assert hasattr(AnomalyType, "COVID_STYLE")


class TestAnomalyTestCaseStructure:
    """Tests for AnomalyTestCase structure."""

    def test_holiday_spike_has_magnitude(self):
        """Test holiday spike has magnitude factor."""
        anomaly = get_anomaly_by_name("holiday_spike_q4_retail")
        assert "magnitude" in anomaly.injected_anomaly
        assert anomaly.injected_anomaly["magnitude"] > 1.0

    def test_covid_has_year(self):
        """Test COVID-style anomaly has year."""
        anomaly = get_anomaly_by_name("covid_channel_shift_2020")
        assert "year" in anomaly.injected_anomaly
        assert anomaly.injected_anomaly["year"] == 2020

    def test_secular_trend_has_cagr(self):
        """Test secular trend has CAGR."""
        anomaly = get_anomaly_by_name("online_channel_growth_2019_2024")
        assert "online_cagr" in anomaly.injected_anomaly
        assert "in_store_cagr" in anomaly.injected_anomaly


class TestAnomalyRetrieval:
    """Tests for anomaly retrieval functions."""

    def test_get_anomaly_by_name_returns_correct(self):
        """Test retrieving specific anomaly."""
        anomaly = get_anomaly_by_name("holiday_spike_q4_retail")
        assert anomaly.name == "holiday_spike_q4_retail"

    def test_get_anomaly_raises_on_not_found(self):
        """Test error on non-existent anomaly."""
        with pytest.raises(ValueError):
            get_anomaly_by_name("nonexistent")

    def test_filter_by_category_returns_correct_count(self):
        """Test category filtering."""
        seasonal = get_anomalies_by_category("seasonal")
        assert all(a.category == "seasonal" for a in seasonal)

    def test_filter_by_category_empty_for_unknown(self):
        """Test unknown category returns empty."""
        empty = get_anomalies_by_category("nonexistent")
        assert len(empty) == 0