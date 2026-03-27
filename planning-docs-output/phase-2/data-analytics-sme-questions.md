# Cross-SME Questions for Data Analytics SME (data-analytics-sme)

## From AI/NLP SME (ai-nlp-sme)

**Context:** The AI/NLP SME is designing dimension extraction and result validation. They need statistical guidance on dimension distributions and aggregation detection.

1. **Dimension Distributions for Validation:**
   The HLRD mentions dimensions like "generation," "income band," "card type" - what statistical distributions should be embedded for these to produce analytically plausible results? Specifically: should income band show expected correlation with transaction amount and brand preferences?

2. **Aggregation Level Detection:**
   When a user asks about "spending trends," how does the system decide between daily, weekly, or monthly granularity? Is there a domain rule (e.g., "queries spanning >3 months default to monthly") or should this be inferred from query wording?

3. **Result Sanity Checks:**
   What basic sanity checks should the AI pipeline perform on API results before rendering? For example: detecting negative values where none expected, or results that are statistical outliers given the query dimensions.

---

## From Integration Engineer SME (integration-engineer-sme)

**Context:** The Integration Engineer is designing continuous aggregates and pre-computation. They need guidance on what granularities and metrics to pre-compute.

1. **Continuous Aggregate Granularities:**
   What aggregation granularities should continuous aggregates pre-compute? Daily, weekly, monthly, and quarterly are obvious candidates, but should we also consider:
   - Hourly aggregates for real-time dashboards?
   - Year-over-year comparisons (annualized)?
   - Running totals (cumulative sum)?

2. **Pre-Computed Derived Metrics:**
   What derived metrics should the API pre-compute? Beyond `SUM`, `COUNT`, `AVG` on transaction amounts:
   - Market share percentages (per brand within category)
   - Year-over-year growth rates
   - Category mix percentages (percentage of total spend within category)

---

## From Consumer Spending SME (consumer-spending-sme)

**Context:** The Consumer Spending SME is designing synthetic transaction data generation. They need statistical guidance on distributions and panel data handling.

1. **Transaction Amount Distributions:**
   For the synthetic transaction data generation, what statistical distributions should we use for transaction amounts (skewed, log-normal typical for spending)? Should we model at transaction-level or generate pre-aggregated data?

2. **Cross-Shopping Panel Data:**
   How should customer_id be handled for cross-shopping/retention analysis? If using synthetic panel data, what panel size is realistic (1M+ panelists vs. smaller sample)?

3. **Time-Series Aggregation Strategy:**
   What time-series aggregation strategies balance query performance with analytical flexibility (pre-aggregated monthly tables vs. on-the-fly daily aggregation)?

---

## From Market Analyst SME (market-analyst-sme)

**Context:** The Market Analyst is designing the eval framework and synthetic data expectations. They need statistical guidance on distributions and anomaly injection.

1. **Aggregation Level for Time-Series:**
   What aggregation level is appropriate for synthetic transactions? Daily? Weekly? Monthly? This affects what time-series analysis is meaningful.

2. **Statistical Distributions for Realistic Trends:**
   What statistical distributions should the synthetic data follow? Normal? Power law? Zipfian? This affects how realistic trend analysis will feel.

3. **Anomaly Injection for Eval Framework:**
   Should the eval framework include known anomalies that the system should detect? If so, what types (seasonal, one-time events, secular trends)?

4. **Market Share Calculation Method:**
   How should "market share" be calculated - by transaction count, by spend, by unique customers? All three give different results.
