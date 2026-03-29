# Unit 2: Synthetic Data Generator

> **Status:** Implemented
> **FR Coverage:** FR-6.6, FR-6.7, FR-6.9, FR-6.10
> **Dependencies:** IU-1 (Database Infrastructure)

## Overview

Unit 2 is the synthetic data generation layer of Proteus, responsible for producing realistic consumer spending panel data that powers the entire analytics pipeline. It implements Python-based generators that create a statistically rigorous consumer panel of 100K–500K panelists and 10M+ transactions, with embedded seasonal patterns, demographic correlations, and income-brand relationships that mirror real-world US consumer behavior.

The generator sits between the database infrastructure (IU-1) and the data API (IU-3) in the system architecture. It produces panelist records with demographic attributes (income band, generation, geography) and transaction records with log-normal amount distributions, seasonal adjustments (Q4 holiday spikes, back-to-school, weekend effects), and generational spending preferences. All generation uses a fixed seed (default 42) for reproducibility, making it suitable for evaluation consistency.

A companion validation module measures data quality against real-world benchmarks — Gini coefficients for market share concentration, coefficient of variation for transaction volumes, and category proportion alignment with BEA consumer expenditure data — ensuring the synthetic data is statistically credible before downstream consumption.

## Functionality Implemented

### Statistical Distributions (FR-6.6)
- **Log-normal transaction amounts** — Category-specific mu/sigma parameters (essential: 3.0/0.8, mid-tier: 3.5/1.0, premium: 4.2/1.2, dining: 3.2/0.9, fast food: 2.2/0.6) plus value, walmart, and luxury tiers
- **Income multipliers** — 7 descriptive income bands (under_25k through over_200k) with multipliers ranging from 0.6x to 1.7x
- **Panel weight sampling** — Calibrated weights to make the panel representative of US consumer demographics

### Embedded Spending Patterns (FR-6.7)
- **Q4 holiday spike** — 25–40% retail volume increase Nov–Dec with December 15–24 peak at +60–100% vs. prior-week baseline
- **January normalization** — -15–25% vs. Q4 average to balance the Q4 spike
- **Back-to-school** — 20–35% increase in school-related categories during Aug–Sep
- **Weekend vs. weekday** — Saturday +30–35% vs. Monday baseline for retail
- **Generational preferences** — Gen Z dining/delivery emphasis (22%+), Millennial grocery/home focus, Boomer healthcare/travel skew
- **Income-brand correlation** — High-income panelists ($150K+) show 70–80% premium/luxury brand preference with Walmart transactions <2%

### Panel Data Structure (FR-6.9)
- **Panelist generation** — 100K–500K panelists with persistent UUID, income band, generation, geography, panel start date, and calibrated panel weight
- **Transaction density** — 50–200 transactions per panelist over 2-year period across 3–10 different brands

### Data Quality Metrics (FR-6.10)
- **Gini coefficient** — Brand market share concentration target 0.55–0.70
- **Coefficient of variation** — Daily transaction volume target 0.3–0.6
- **Category proportions** — Mean absolute deviation vs. BEA benchmarks <5%
- **Weekend-to-weekday ratio** — Within 10% of survey benchmarks
- **Transaction frequency** — Distribution validation per panelist

## Implementation Details

The unit is built as a pure Python library using NumPy for statistical computations, organized into focused single-responsibility modules. No external database connection is required for generation itself — the modules produce in-memory data structures (dataclasses) that can be consumed by downstream insertion logic.

**Key architectural patterns:**

- **Functional composition over classes**: Core generation functions (`generate_transaction_amount`, `apply_seasonal_adjustment`, `get_generation_preference`) are standalone functions rather than methods on a monolithic class. The `__init__.py` re-exports the public API for clean imports.
- **Constant-driven configuration**: Distribution parameters, income multipliers, and seasonal pattern weights are defined as module-level dictionaries and constants, making them easy to tune without changing logic.
- **Generator-based transaction production**: `generate_transactions_for_panelist` yields transactions via Python generators for memory-efficient handling of large datasets.
- **Dataclass models**: Both `Panelist` and `Transaction` are plain dataclasses — immutable data carriers with no ORM coupling.
- **Descriptive string IDs**: Dimension identifiers use human-readable underscore-delimited strings (e.g., `under_25k`, `baby_boomer`, `in_store`) aligned with the database seed data and API configuration YAML, ensuring cross-unit consistency.

**Reproducibility**: All random operations use a configurable NumPy seed (default 42), enabling deterministic output for evaluation runs.

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/data/__init__.py` | Package entry point; re-exports public API (distribution functions, validation report) |
| `backend/src/data/distributions.py` | FR-6.6 implementation: log-normal amount generation, category params, income multipliers, panel weight sampling |
| `backend/src/data/seasonal_patterns.py` | FR-6.7 implementation: Q4 spike, January normalization, back-to-school, weekend patterns, generational preferences, income-brand correlation |
| `backend/src/data/panelist_generator.py` | FR-6.9 implementation: panelist generation with demographic attributes, geography/generation/income distributions |
| `backend/src/data/transaction_generator.py` | FR-6.6/6.7 integration: generates transactions per panelist combining amounts, seasonal adjustments, and preferences |
| `backend/src/data/validation.py` | FR-6.10 implementation: Gini coefficient, CV, category proportions, weekend/weekday ratio, transaction frequency validation |
| `backend/tests/test_distributions.py` | 324-line test suite for distribution functions |
| `backend/tests/test_seasonal_patterns.py` | 518-line test suite for seasonal pattern logic |
| `backend/tests/test_panelist_generator.py` | 250-line test suite for panelist generation |
| `backend/tests/test_transaction_generator.py` | 631-line test suite for transaction generation |
| `backend/tests/test_validation.py` | 462-line test suite for validation metrics |
| `backend/tests/integration/test_contract_unit2_unit3.py` | 283-line integration tests verifying dimension alignment between Unit 2 and Unit 3 |

## Integration Points

### This Unit Provides
- **`Panelist` dataclass** — Contains `id` (UUID), `income_band` (string), `generation` (string), `geography` (string), `panel_start_date` (date), `panel_weight` (float)
- **`Transaction` dataclass** — Contains `id`, `panelist_id`, `brand`, `category`, `amount`, `transaction_date`, `channel`, `card_type`
- **`generate_panelists(count, seed)`** — Produces a list of panelists with calibrated demographic distributions
- **`generate_transactions_for_panelist(panelist, ...)`** — Yields transactions with all seasonal/demographic adjustments applied
- **`generate_validation_report(transactions)`** — Produces a `ValidationReport` with pass/fail metrics
- **Dimension value constants** — Canonical string IDs for generations (`gen_z`, `millennial`, `gen_x`, `baby_boomer`), income bands (`under_25k` through `over_200k`), and channels (`in_store`, `online`, `mobile_app`)

### This Unit Depends On
- **IU-1 (Database Infrastructure)** — Schema must be available for data insertion; dimension IDs in the generated data must match the seed data in `frontend/drizzle/0011_seed_dimensions.sql`
- **PostgreSQL connection** — Via `DATABASE_URL` environment variable (for actual data insertion, not for generation itself)

## Usage Guide

### Generating panelists

```python
from src.data.panelist_generator import generate_panelists

panelists = generate_panelists(count=100_000, seed=42)
# Returns List[Panelist] with demographically calibrated attributes
```

### Generating transactions for a panelist

```python
from datetime import date
from src.data.transaction_generator import generate_transactions_for_panelist

transactions = list(generate_transactions_for_panelist(
    panelist=panelists[0],
    start_date=date(2024, 1, 1),
    end_date=date(2025, 12, 31),
    seed=42,
))
```

### Validating generated data

```python
from src.data.validation import generate_validation_report

report = generate_validation_report(transactions)
print(f"Overall pass: {report.overall_pass}")
print(f"Gini: {report.gini_result}")
print(f"CV: {report.cv_result}")
```

### Running tests

```bash
cd backend
python -m pytest tests/test_distributions.py tests/test_seasonal_patterns.py \
  tests/test_panelist_generator.py tests/test_transaction_generator.py \
  tests/test_validation.py -v
```

### Running integration contract tests

```bash
cd backend
python -m pytest tests/integration/test_contract_unit2_unit3.py -v
```

### Key configuration

- **Seed**: Default `42` for reproducibility; pass a different seed to any generator function
- **Income bands**: `under_25k`, `25k_50k`, `50k_75k`, `75k_100k`, `100k_150k`, `150k_200k`, `over_200k`
- **Generations**: `gen_z`, `millennial`, `gen_x`, `baby_boomer`
- **Channels**: `in_store`, `online`, `mobile_app`

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `3fd1cc4` | 2026-03-28 | feat: implement Unit 2 synthetic data generators |
| `fd35719` | 2026-03-28 | fix: align dimension IDs across Unit 2, Unit 3, and DB seed |
