"""Data module for synthetic data generation."""

from src.data.distributions import (
    CATEGORY_PARAMS,
    INCOME_MULTIPLIERS,
    generate_transaction_amount,
    sample_income_band,
    sample_panel_weight,
)
from src.data.validation import (
    ValidationReport,
    validate_transaction_amounts,
    validate_market_share,
    validate_category_proportions,
    validate_weekend_weekday_ratio,
    validate_transaction_frequency,
    generate_validation_report,
)

__all__ = [
    "CATEGORY_PARAMS",
    "INCOME_MULTIPLIERS",
    "generate_transaction_amount",
    "sample_income_band",
    "sample_panel_weight",
    "ValidationReport",
    "validate_transaction_amounts",
    "validate_market_share",
    "validate_category_proportions",
    "validate_weekend_weekday_ratio",
    "validate_transaction_frequency",
    "generate_validation_report",
]
