"""FR-7.5: Anomaly Test Cases for Eval.

This module defines anomaly test cases for testing the system's ability
to detect and handle unusual patterns in consumer transaction data.

FR Requirements:
- FR-7.5: Anomaly Injection for Eval
  - Seasonal patterns (holiday spikes, back-to-school)
  - One-time events (COVID-style channel shift)
  - Secular trends (online channel growth 2019-2024)

Models:
    AnomalyTestCase: Definition of an anomaly test case
    AnomalyType: Types of anomalies that can be injected
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AnomalyType(str):
    """Types of anomalies for eval testing."""

    SEASONAL = "seasonal"
    CHANNEL_SHIFT = "channel_shift"
    SECULAR_TREND = "secular_trend"
    COVID_STYLE = "covid_style"
    PROMOTION = "promotion"
    WEATHER = "weather"


class AnomalyTestCase(BaseModel):
    """Definition of an anomaly test case.

    FR-7.5: Anomaly test cases for detection testing.
    These test cases inject known anomalies to verify the system
    correctly identifies and handles unusual patterns.

    Attributes:
        name: Unique identifier for this anomaly test case.
        description: Human-readable description of the anomaly.
        query: The query to test against this anomaly.
        expected_impact: Description of expected impact on results.
        injected_anomaly: Dict describing the anomaly parameters.
        category: Category for grouping (seasonal, event, trend).
    """

    name: str = Field(..., description="Unique identifier for this anomaly test case")
    description: str = Field(..., description="Human-readable description of the anomaly")
    query: str = Field(..., description="The query to test against this anomaly")
    expected_impact: str = Field(
        ...,
        description="Description of expected impact on results",
    )
    injected_anomaly: Dict[str, Any] = Field(
        ...,
        description="Dict describing the anomaly parameters",
    )
    category: str = Field(..., description="Category for grouping (seasonal, event, trend)")


# ============================================================================
# FR-7.5: Pre-defined Anomaly Test Cases
# ============================================================================

ANOMALY_TEST_CASES: List[AnomalyTestCase] = [
    # Seasonal Patterns - Holiday Spikes
    AnomalyTestCase(
        name="holiday_spike_q4_retail",
        description="Q4 holiday spike for retail categories",
        query="Show retail market share trends Q4 2024",
        expected_impact="Visible spike in December for retail categories",
        injected_anomaly={
            "type": AnomalyType.SEASONAL,
            "months": [11, 12],
            "magnitude": 1.35,
            "categories": ["retail", "general merchandise"],
        },
        category="seasonal",
    ),
    AnomalyTestCase(
        name="holiday_spike_grocery",
        description="Holiday spike in grocery spending",
        query="What are grocery spending trends in November-December?",
        expected_impact="Increased grocery spend during holiday weeks",
        injected_anomaly={
            "type": AnomalyType.SEASONAL,
            "months": [11, 12],
            "magnitude": 1.25,
            "categories": ["grocery"],
        },
        category="seasonal",
    ),
    # Seasonal Patterns - Back to School
    AnomalyTestCase(
        name="back_to_school_august",
        description="Back-to-school spending spike in August",
        query="Show category trends for August 2024",
        expected_impact="Visible spike in back-to-school categories",
        injected_anomaly={
            "type": AnomalyType.SEASONAL,
            "months": [7, 8],
            "magnitude": 1.20,
            "categories": ["apparel", "electronics"],
        },
        category="seasonal",
    ),
    AnomalyTestCase(
        name="back_to_school_september",
        description="Back-to-school spending continues in September",
        query="Compare school category spending September vs June",
        expected_impact="Higher spending in September for school-related categories",
        injected_anomaly={
            "type": AnomalyType.SEASONAL,
            "months": [8, 9],
            "magnitude": 1.15,
            "categories": ["apparel", "office supplies"],
        },
        category="seasonal",
    ),
    # One-time Events - COVID-style
    AnomalyTestCase(
        name="covid_channel_shift_2020",
        description="COVID-19 induced channel shift in 2020",
        query="Compare online vs in-store spending 2020 vs 2019",
        expected_impact="Dramatic online increase in 2020 vs 2019",
        injected_anomaly={
            "type": AnomalyType.COVID_STYLE,
            "year": 2020,
            "online_multiplier": 2.5,
            "in_store_multiplier": 0.6,
        },
        category="event",
    ),
    AnomalyTestCase(
        name="covid_channel_recovery_2022",
        description="COVID recovery phase in 2022",
        query="Show channel trends 2022 vs 2020",
        expected_impact="Partial recovery of in-store spending by 2022",
        injected_anomaly={
            "type": AnomalyType.COVID_STYLE,
            "year": 2022,
            "online_multiplier": 1.8,
            "in_store_multiplier": 0.85,
        },
        category="event",
    ),
    # Secular Trends - Online Growth
    AnomalyTestCase(
        name="online_channel_growth_2019_2024",
        description="Secular trend of online channel growth",
        query="Show online vs in-store spending trend 2019-2024",
        expected_impact="Consistent online channel growth over 5 years",
        injected_anomaly={
            "type": AnomalyType.SECULAR_TREND,
            "start_year": 2019,
            "end_year": 2024,
            "online_cagr": 0.15,  # 15% CAGR
            "in_store_cagr": -0.05,  # -5% CAGR
        },
        category="trend",
    ),
    AnomalyTestCase(
        name="digital_payment_adoption",
        description="Long-term digital payment adoption trend",
        query="Show digital wallet usage trends by generation",
        expected_impact="Younger generations show higher digital payment adoption",
        injected_anomaly={
            "type": AnomalyType.SECULAR_TREND,
            "start_year": 2020,
            "end_year": 2024,
            "digital_wallet_cagr": 0.25,
            "card_decline_rate": 0.10,
        },
        category="trend",
    ),
    # Promotions
    AnomalyTestCase(
        name="prime_day_july",
        description="Amazon Prime Day promotional spike",
        query="Show e-commerce spending during Prime Day period",
        expected_impact="Significant spike in July e-commerce",
        injected_anomaly={
            "type": AnomalyType.PROMOTION,
            "event": "prime_day",
            "month": 7,
            "magnitude": 1.5,
        },
        category="promotion",
    ),
    AnomalyTestCase(
        name="black_friday",
        description="Black Friday promotional spike",
        query="Show retail spending Black Friday week",
        expected_impact="Major spike in November retail spending",
        injected_anomaly={
            "type": AnomalyType.PROMOTION,
            "event": "black_friday",
            "month": 11,
            "magnitude": 1.6,
        },
        category="promotion",
    ),
    # Weather anomalies
    AnomalyTestCase(
        name="hurricane_impact",
        description="Hurricane impact on spending patterns",
        query="Show spending patterns in hurricane-affected areas",
        expected_impact="Disruption followed by recovery in affected regions",
        injected_anomaly={
            "type": AnomalyType.WEATHER,
            "event": "hurricane",
            "affected_states": ["TX", "FL", "LA"],
            "disruption_magnitude": 0.7,
            "recovery_weeks": 8,
        },
        category="weather",
    ),
    AnomalyTestCase(
        name="winter_storm",
        description="Winter storm impact on spending",
        query="Show spending impact of winter storms",
        expected_impact="Short-term disruption in affected areas",
        injected_anomaly={
            "type": AnomalyType.WEATHER,
            "event": "winter_storm",
            "months": [12, 1, 2],
            "affected_regions": ["northeast", "midwest"],
            "disruption_magnitude": 0.8,
        },
        category="weather",
    ),
]


def get_anomaly_by_name(name: str) -> AnomalyTestCase:
    """Get an anomaly test case by name.

    Args:
        name: Name of the anomaly test case.

    Returns:
        The AnomalyTestCase with the matching name.

    Raises:
        ValueError: If no matching anomaly test case is found.
    """
    for anomaly in ANOMALY_TEST_CASES:
        if anomaly.name == name:
            return anomaly
    raise ValueError(f"Anomaly test case not found: {name}")


def get_anomalies_by_category(category: str) -> List[AnomalyTestCase]:
    """Get all anomaly test cases in a category.

    Args:
        category: Category to filter by (seasonal, event, trend, promotion, weather).

    Returns:
        List of AnomalyTestCases in the category.
    """
    return [a for a in ANOMALY_TEST_CASES if a.category == category]