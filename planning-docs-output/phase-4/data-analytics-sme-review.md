# Data Analytics SME Review — Requirements Draft

**Review Date:** 2026-03-27
**Domain:** Data modeling, statistical analysis, visualization design, time-series data
**Focus Areas:** FR-5, FR-6, NFR-3

---

## Gaps Found

### G1: KPI Card Comparison Methodology Missing (FR-5.3)

**Location:** FR-5.3 KPI Card Display

**Issue:** The requirement specifies that KPI cards display "comparison to prior period" and "comparison to category average" but provides no methodology for calculating these comparisons.

**Missing Details:**
- Prior period is ambiguous — for a query like "Q3 2024 Target sales," does prior period mean Q2 2024 or Q3 2023 (YoY)?
- Category average comparison — is this across all brands in the category, or a specific competitor benchmark?
- No definition of how comparison percentages are calculated (absolute vs. relative difference)

**Recommended Change:**
```
- KPI comparison to prior period SHALL be calculated as: ((current - prior) / prior) * 100
- Prior period selection logic: if query specifies a quarter, use same quarter prior year (YoY); if query specifies a month, use prior month (MoM)
- Category average comparison SHALL use unweighted average of all brands in the queried category
```

---

### G2: Aggregation Auto-Selection Logic Incomplete (FR-5.1 / FR-4.4)

**Location:** FR-5.1 (auto chart-type) and FR-4.4 (API aggregation)

**Issue:** The auto-aggregation rules in FR-4.4 conflict with the visualization rules in FR-5.1. FR-4.4 specifies:
- 1-7 days → daily
- 8-90 days → daily
- 91-365 days → weekly
- 1+ years → monthly

But FR-5.1 says "over time", "trend", "history" → Line Chart. No guidance exists on what aggregation level triggers Line Chart vs. other chart types, or how aggregation level affects visualization decisions.

**Recommended Change:**
```
- Line Chart SHALL be used when: aggregation level is daily OR weekly AND time range spans 14+ days
- When aggregation is monthly or quarterly and time range is 1+ year, Line Chart shows quarterly/annual trend points
- Bar Chart SHALL be used for: categorical comparisons with monthly or quarterly aggregation
```

---

### G3: Panel Weights Specification Missing (FR-6.9)

**Location:** FR-6.9 Panel Data Structure

**Issue:** Panelists have a `panel_weight` field but no methodology is specified for how these weights are calculated or intended to be used in aggregations.

**Impact:** Without proper weighting methodology, derived metrics (e.g., total spending, market share) may not be representative of actual consumer behavior.

**Recommended Change:**
```
- Panel weights SHALL be calibrated to make the panel representative of US consumer demographics (generation x income_band x geography distribution)
- Panel weights SHALL sum to estimated total US consumer population (or scaling factor agreed upon with stakeholders)
- Market share calculations using panel data SHALL apply panel weights
```

---

### G4: Continuous Aggregate Schema Not Specified (FR-6.8)

**Location:** FR-6.8 Continuous Aggregates

**Issue:** The requirement lists the types of continuous aggregates to pre-compute but does not specify their schema design.

**Missing Details:**
- No specification of the primary key or index structure for aggregates
- No definition of how aggregates handle dimensions that are not applicable (e.g., generation for category-level aggregates)
- Chunk interval strategy for aggregates (daily chunks vs. monthly) not specified

**Recommended Change:**
```
- Daily rollup aggregate SHALL be structured as: (timestamp, brand_id, category_id, geo_state_id, generation_id, income_band_id, transaction_count, total_spend, unique_panelists)
- Aggregates SHALL use composite indexes on (timestamp, brand_id, category_id) for efficient filtering
- Aggregate tables SHALL be configured with daily chunks, compressed after 7 days with gzip
```

---

### G5: Synthetic Data Seed/Reproducibility Not Addressed (NFR-3)

**Location:** NFR-3 (entire section)

**Issue:** For reproducible analytics and debugging, the synthetic data generation process should be deterministic given a seed. No reproducibility requirements exist.

**Recommended Change:**
```
- Synthetic data generation SHALL accept a configurable seed parameter for reproducibility
- The default seed value SHALL be documented and fixed for eval suite consistency
- Regression tests for statistical properties SHALL verify distributions remain within tolerance across data regenerations
```

---

## Conflicts Identified

### C1: Q4 Holiday Spike Magnitude Conflict

**Locations:** FR-6.7 vs. NFR-3.5

**FR-6.7 states:**
> December 15-24 peak at +60-100%

**NFR-3.5 states:**
> Holiday Q4 retail spike SHALL be +25-35% vs. Q3 average

**Conflict:** A +60-100% peak is inconsistent with a +25-35% overall Q4 spike. If December peaks at +60-100% for 10 days but the quarter is only +25-35%, this implies January and the rest of Q4 must be significantly below average to compensate. This is statistically possible but requires explicit modeling.

**Resolution Required:** Choose one interpretation:
1. "Peak" = +60-100% (10-day window); Q4 overall = +25-35% (analytically plausible with January depression)
2. "Peak" wording should be changed to align with overall Q4 expectation

**Recommended Fix:**
```
- FR-6.7 should clarify: "December 15-24 peak at +60-100% vs. prior-week baseline" (not vs. Q3 average)
- NFR-3.5 should remain as: Q4 overall +25-35% vs. Q3 average
- Add explicit January normalization: January -15-25% vs. Q4 average to balance the Q4 spike
```

---

### C2: High-Income Walmart Correlation Conflict

**Locations:** FR-6.7 vs. NFR-3.2

**FR-6.7 states:**
> High-income ($150K+) shows 70-80% premium brand transactions

**NFR-3.2 states:**
> High-income customers SHALL NOT heavily shop at Walmart — this correlation is strong and analysts will detect violations

**Conflict:** Walmart is not typically considered a "premium brand." If 70-80% of high-income transactions are premium brand, the remaining 20-30% would include mid-market and value. The statement "SHALL NOT heavily shop at Walmart" implies low correlation but doesn't quantify what "heavily" means.

**Resolution Required:** Clarify the acceptable rate of Walmart/value-tier transactions for high-income panelists.

**Recommended Fix:**
```
- High-income ($150K+) SHALL show: 70-80% premium brand, 15-25% mid-market, 0-5% value-tier
- Walmart transactions for income band 6 ($150K+) SHALL be <2% of their total transactions
- The income-band correlation (Pearson 0.65-0.75) in NFR-3.2 SHALL be verified empirically during data validation
```

---

### C3: Weekend Retail Spike Timeframe Inconsistent

**Locations:** FR-6.7 vs. NFR-3.3

**FR-6.7 states:**
> Saturday +30-35% vs. Monday baseline for retail

**NFR-3.3 states:**
> Weekend vs. weekday patterns SHALL be embedded: Saturday +30-35% for retail

**Issue:** FR-6.7 specifies "vs. Monday baseline" but NFR-3.3 omits this detail. The Monday baseline is important because retail patterns typically vary significantly across weekday categories (Monday vs. Tuesday-Thursday vs. Friday).

**Resolution:** NFR-3.3 should reference the Monday baseline explicitly for consistency.

---

## Accuracy Assessment

### Statistically Accurate

**A1: Log-Normal Distribution for Transaction Amounts (FR-6.6)**
Correctly specified. Log-normal is appropriate for transaction amounts which are bounded at zero and positively skewed. The mu/sigma parameters (representing the underlying normal distribution's mean and standard deviation) are reasonable for the stated categories.

**A2: Zipfian/Power Law for Brand Market Shares (NFR-3.1)**
Correct. Brand market share typically follows a power law distribution where the largest brand has the highest share and share decreases rapidly for smaller brands.

**A3: Exponential Distribution for Inter-Transaction Time (NFR-3.1)**
Correct. Inter-transaction times in consumer behavior are well-modeled by exponential distributions (memoryless property).

**A4: Dirichlet Distribution for Category Proportions (NFR-3.1)**
Correct. Dirichlet is the appropriate prior/conjugate for categorical proportion data like category spend mix.

**A5: TimescaleDB Compression After 30 Days (FR-6.2)**
Accurate. 30-day compression threshold is reasonable for daily chunk intervals.

---

### Statistically Questionable

**Q1: Income-Brand Correlation Coefficient (NFR-3.2)**

The Pearson coefficient of 0.65-0.75 for premium brand selection by income is **higher than typically observed** in real consumer data. Real-world income-brand correlations are usually in the 0.35-0.55 range for discretionary categories.

If the data truly exhibits 0.65-0.75 correlation, it may appear "too clean" and raise suspicion. Consider:
- Target range: 0.45-0.60 for premium brands (more realistic)
- Luxury-only correlation: 0.55-0.70 (more defensible)

**Recommended Change:**
```
- Income-brand correlation for premium brands SHALL have Pearson coefficient 0.45-0.60
- Income-brand correlation for luxury brands SHALL have Pearson coefficient 0.55-0.70
- This provides realistic but detectable correlation patterns
```

---

### Missing Statistical Specifications

**M1: Transaction Count Distribution Not Specified**
FR-6.6 specifies amount distributions but not the distribution of transaction frequency per panelist. This is critical for panel data realism.

**M2: Zero-Inflation Not Addressed**
Some panelists may have zero transactions in certain categories. The current spec doesn't address whether/how zero-inflation is modeled.

**M3: Channel Preference Correlation Not Quantified**
NFR-3.2 mentions "generation SHALL correlate with channel preferences" but provides no target correlation strength.

---

## Recommended Changes

### RC-1: Add Statistical Validation Tests (NFR-3.6)

Add a new section specifying concrete statistical tests:

```
### NFR-3.6: Statistical Validation Tests

The following tests SHALL pass during data generation validation:

1. **Shapiro-Wilk test** on log-transformed transaction amounts: p > 0.05 (confirms log-normal)
2. **Kolmogorov-Smirnov test** on brand market share vs. theoretical Zipfian: p > 0.05
3. **Chi-squared test** on category proportions vs. Dirichlet parameters: p > 0.05
4. **Autocorrelation test** on daily transaction volumes: no significant autocorrelation at lag 7 (confirms no identical-year-patterns)
5. **Market share stability test**: brand rank correlation between 2023 and 2024 > 0.85 (implies realistic evolution, not stasis)
```

### RC-2: Clarify KPI Card Period Comparison Logic (FR-5.3)

Add explicit rules for comparison period selection:

```
- For queries with explicit period (e.g., "Q3 2024"): prior period = Q3 2023 (YoY)
- For queries with relative period (e.g., "last month"): prior period = month before (MoM)
- For queries spanning multiple months (e.g., "2024 YTD"): prior period = same period prior year
- Category average = unweighted mean of all brands in queried category for the same time period
```

### RC-3: Add Visualization Threshold Justification (FR-5.7)

The thresholds (100, 1000, 10000) are arbitrary. Add justification or make configurable:

```
- 1-100 rows: Full display (reasonable for human comprehension)
- 101-1000 rows: Virtual scrolling recommended; aggregation optional
- 1001-10000 rows: Aggregation view shown by default with "Show raw" option
- 10000+ rows: Aggregation mandatory; raw data requires explicit query parameter
```

### RC-4: Add Data Quality Metrics for Synthetic Data

Add explicit quality gates:

```
### FR-6.10: Data Quality Metrics

The following quality metrics SHALL be measured and reported:
- Coefficient of variation for daily transaction volumes: target 0.3-0.6
- Gini coefficient for brand market share: target 0.55-0.70
- Mean absolute deviation for category proportions vs. BEA consumer expenditure data: <5%
- Weekend-to-weekday ratio by category: within 10% of survey benchmarks
```

### RC-5: Clarify Time Range Default Units (FR-3.3, FR-4.4)

The aggregation level defaults in FR-3.3 and FR-4.4 have gaps:

```
- FR-4.4: 8-90 days → daily creates redundant rule (both 1-7 and 8-90 map to daily)
- Suggest: 1-14 days → daily, 15-90 days → weekly, 91-365 days → monthly, 1+ years → quarterly
```

---

## Questions for Other SMEs

**For AI/NLP SME:**
- In FR-5.1, the chart type selection logic includes patterns like "over time," "trend," "history." How does the dimension extraction handle queries that mix time-series intent with categorical comparison (e.g., "Show me Target vs. Walmart quarterly trend for 2024")? Does this require multi-tool execution or single-tool with compound aggregation?

**For Behavioral Psychology SME:**
- NFR-3.3 specifies Saturday +30-35% vs. Monday baseline for retail. Is this consistent with consumer behavior research? Should there be variation by generation (e.g., Gen Z showing different weekend patterns)?

**For Market Analyst SME:**
- The validation benchmark in NFR-3.5 specifies "E-commerce share of retail SHALL be 20-25% in 2024." Is this based on Census Bureau or other official data? Should the synthetic data track this metric across years to show the secular trend from 2019-2024?
