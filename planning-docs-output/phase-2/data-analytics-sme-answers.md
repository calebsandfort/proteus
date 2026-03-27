# Data Analytics SME: Cross-SME Answers

## From AI/NLP SME (ai-nlp-sme)

---

**Question 1: Dimension Distributions for Validation**

The HLRD mentions dimensions like "generation," "income band," "card type" - what statistical distributions should be embedded for these to produce analytically plausible results? Specifically: should income band show expected correlation with transaction amount and brand preferences?

---

**Answer:**

Yes, income band MUST show correlation with transaction amount and brand preferences for analytically plausible results. This is not optional -- analysts will immediately detect a dataset where high-income and low-income consumers behave identically. Here are the specific statistical distributions to embed:

**Income Band Distributions:**

| Income Band | Population Share | Avg Transaction | Brand Tier Preference |
|-------------|------------------|-----------------|----------------------|
| <$25K | 18% | $25-35 | Budget (60%), Mid (35%), Premium (5%) |
| $25K-$50K | 24% | $35-55 | Budget (40%), Mid (45%), Premium (15%) |
| $50K-$75K | 22% | $50-75 | Budget (20%), Mid (50%), Premium (30%) |
| $75K-$100K | 16% | $70-100 | Budget (10%), Mid (45%), Premium (45%) |
| $100K-$150K | 12% | $90-140 | Budget (5%), Mid (30%), Premium (65%) |
| $150K+ | 8% | $130-200 | Budget (2%), Mid (15%), Premium (83%) |

**Generation Distributions:**

| Generation | Age Range | Population Share | Primary Categories | Card Type Preference |
|------------|-----------|------------------|-------------------|---------------------|
| Gen Z | 18-27 | 18% | Fast food, streaming, fashion, gaming | Debit (55%), Credit (35%) |
| Millennial | 28-43 | 25% | Groceries, dining, home goods, childcare | Credit (60%), Debit (35%) |
| Gen X | 44-59 | 24% | Home improvement, healthcare, travel | Credit (65%), Debit (30%) |
| Boomer+ | 60-78 | 33% | Healthcare, groceries, travel, dining | Credit (55%), Debit (40%) |

**Critical Correlations to Embed:**

1. **Income x Brand Tier**: Pearson correlation coefficient should be 0.65-0.75 between income band and average transaction amount at premium brands. Lower correlation (0.30-0.40) for essential categories like groceries.

2. **Generation x Channel**: Gen Z shows 45% online, 55% in-store; Boomers show 25% online, 75% in-store.

3. **Income x Category Mix**: Lower income = 65-70% essentials (groceries, utilities); Higher income = 40-45% essentials, rest discretionary.

4. **Geography x Category**: Urban = +30% dining/entertainment; Rural = +25% auto/gas.

**Validation Check for AI Pipeline:**
When the AI receives API results, it should validate:
- High-income band query returns higher avg transaction at premium brands than low-income band (should be ~3-5x difference)
- Gen Z query shows higher % to streaming/fast food than Boomer query
- If these patterns are absent, flag data quality issue

---

**Question 2: Aggregation Level Detection**

When a user asks about "spending trends," how does the system decide between daily, weekly, or monthly granularity? Is there a domain rule (e.g., "queries spanning >3 months default to monthly") or should this be inferred from query wording?

---

**Answer:**

Use a hybrid approach: **domain rules for time range heuristics, query wording for intent inference**.

**Recommended Aggregation Detection Logic:**

```
Rule 1: Explicit wins
  IF query contains "daily" OR "per day" → daily
  IF query contains "weekly" OR "per week" → weekly
  IF query contains "monthly" OR "per month" OR "quarterly" → monthly

Rule 2: Time range size (default behavior)
  IF span ≤ 14 days → daily (shows day-level patterns)
  IF span 15-90 days → weekly (balances detail vs noise)
  IF span 91-365 days → monthly (consistent with reporting)
  IF span > 365 days → quarterly (year-over-year alignment)

Rule 3: Query intent inference
  "trend" OR "over time" → depends on span per Rule 2
  "compare" (without explicit period) → last completed period at default granularity
  "average" OR "typical" → aggregate to appropriate level for stable estimate
  "spike" OR "anomaly" → daily (granular enough to spot outliers)

Rule 4: Category-specific overrides
  Streaming subscriptions → weekly (billing cycle)
  Grocery → weekly or monthly (shopping patterns)
  Travel → monthly (booking cycles)
```

**Default When Ambiguous:**
If no time range specified AND query wording gives no hint, default to:
- Last 30 days at daily granularity for transaction volume
- Last 12 months at monthly granularity for trend analysis
- Last quarter at weekly granularity for recent trends

**Implementation Note:** The dimension extraction layer should extract BOTH the time range AND the implied aggregation level. The NLP pipeline should surface this transparently so users understand why "weekly" was selected for their 6-month query.

---

**Question 3: Result Sanity Checks**

What basic sanity checks should the AI pipeline perform on API results before rendering? For example: detecting negative values where none expected, or results that are statistical outliers given the query dimensions.

---

**Answer:**

Implement a three-tier validation pipeline:

**Tier 1: Schema/Type Validation (Fail-Fast)**

| Check | Expected Behavior | Action if Failed |
|-------|-----------------|------------------|
| NULL values in required fields | None expected | Return error, do not render |
| Negative transaction amounts | None expected (amounts can be negative for refunds) | Flag but render with visual indicator |
| Market share sum | Should equal 100% (within rounding) | Warn if <98% or >102% |
| Date range consistency | start_date ≤ end_date | Return error |
| Count non-negative | COUNT queries always ≥ 0 | Return error if negative |

**Tier 2: Statistical Outlier Detection**

```python
def detect_outliers(values: list[float], z_threshold: float = 3.0) -> list[int]:
    """Return indices of values with |z-score| > threshold."""
    mean = sum(values) / len(values)
    std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
    return [i for i, v in enumerate(values) if abs((v - mean) / std) > z_threshold]

# Also check for contextual outliers:
# - Monthly data showing 10x spike might be December holiday (valid)
# - Monthly data showing 10x spike in August (suspicious unless event-driven)
```

**Tier 3: Domain Consistency Checks**

| Query Type | Sanity Check | Expected Range |
|------------|--------------|----------------|
| Market share | All shares between 0-100% | 0 ≤ share ≤ 100 |
| YoY growth | Within plausible bounds | -50% to +200% (beyond = likely error) |
| Average transaction | Above minimum plausible | > $0.50 for any category |
| Category totals | Sum ≤ total market | Category share ≤ 100% |
| Generation breakdown | Sums to ~100% | 95-105% acceptable |
| Geographic totals | Sum = national total | 98-102% (accounting for small geog) |

**Recommended Implementation:**

The AI pipeline should receive structured API responses that include metadata for validation:
```json
{
  "data": [...],
  "metadata": {
    "row_count": 45,
    "has_nulls": false,
    "total_sum": 1250000.00,
    "outlier_indices": [12, 34],
    "warnings": ["December shows 3.2x normal - holiday effect"]
  }
}
```

If outlier_indices is non-empty, render with visual distinction (different color, tooltip explaining potential anomaly). Do NOT suppress the data unless it fails Tier 1.

---

## From Integration Engineer SME (integration-engineer-sme)

---

**Question 1: Continuous Aggregate Granularities**

What aggregation granularities should continuous aggregates pre-compute? Daily, weekly, monthly, and quarterly are obvious candidates, but should we also consider:
- Hourly aggregates for real-time dashboards?
- Year-over-year comparisons (annualized)?
- Running totals (cumulative sum)?

---

**Answer:**

**Recommended Continuous Aggregate Strategy:**

| Granularity | Use Case | Chunks | Compression | Refresh Policy |
|-------------|----------|--------|-------------|----------------|
| **Hourly** | Real-time dashboards, anomaly detection | 1 hour | After 24 hours | Continuous |
| **Daily** | Standard queries ≤90 days | 1 day | After 7 days | Continuous |
| **Weekly** | Medium-term trends (3-12 months) | 1 week | After 30 days | Hourly |
| **Monthly** | Long-term trends, reporting | 1 month | After 90 days | Hourly |
| **Quarterly** | Year-over-year comparisons | 1 quarter | After 1 year | Hourly |

**Specific Recommendations:**

1. **Hourly aggregates: Include for Phase 1**
   - Enable same-day anomaly detection (Black Friday spikes, etc.)
   - Partition by hour: `time_bucket('1 hour', timestamp)`
   - Use case: "Any unusual activity today?" queries
   - Note: Only keep raw hourly for 7 days, then rollup to daily

2. **Year-over-year: Pre-compute YoY growth rates, not raw annual sums**
   - CREATE MATERIALIZED VIEW yoy_growth_quarterly (pre-computed)
   - Formula: (current_period - prior_period) / prior_period * 100
   - Avoids runtime calculation across large date ranges
   - Also pre-compute trailing 4-quarter sums for rolling comparisons

3. **Running totals (cumulative): Pre-compute for common windows**
   - Year-to-date (YTD) running totals
   - Trailing 12 months (TTM)
   - Trailing 13 weeks (quarter-to-date proxy)
   - Implement as window functions in continuous aggregates, not runtime

**What NOT to Pre-compute:**
- Hourly for periods >7 days (wasteful storage)
- Annual aggregates at any granularity finer than quarterly
- Cumulative sums for arbitrary date ranges (too many combinations)

---

**Question 2: Pre-Computed Derived Metrics**

What derived metrics should the API pre-compute? Beyond `SUM`, `COUNT`, `AVG` on transaction amounts:
- Market share percentages (per brand within category)
- Year-over-year growth rates
- Category mix percentages (percentage of total spend within category)

---

**Answer:**

**Essential Pre-Computed Metrics (Priority Order):**

1. **Market Share (per brand within category)**
   ```
   Pre-compute: daily_brand_category_share
   - time_bucket (day, week, month)
   - brand_id, category_id
   - SUM(amount) as brand_spend
   - SUM(amount) OVER (PARTITION BY time_bucket, category_id) as category_spend
   - brand_spend / category_spend as market_share_pct
   ```
   - Critical for: instant market share queries without runtime division
   - Storage cost: modest (adds 1-2 columns)

2. **Year-over-Year Growth Rates**
   ```
   Pre-compute: monthly_yoy_growth
   - time_bucket (month)
   - brand_id, category_id
   - SUM(amount) as current_period
   - LAG(SUM(amount), 12) as prior_year_same_period (window function)
   - (current_period - prior_year_same_period) / prior_year_same_period * 100 as yoy_growth_pct
   ```
   - Critical for: "How is Brand X performing vs. last year?" queries
   - Eliminates expensive self-join on hypertable

3. **Category Mix Percentages**
   ```
   Pre-compute: daily_category_mix
   - time_bucket (day)
   - category_id, generation, income_band, channel
   - SUM(amount) as category_spend
   - SUM(SUM(amount)) OVER () as total_spend
   - category_spend / total_spend as mix_pct
   ```
   - Critical for: "What % of Gen Z spending goes to fast food?" queries

4. **Rank within Category/Segment**
   ```
   Pre-compute: weekly_brand_rankings
   - time_bucket (week)
   - category_id, region
   - brand_id
   - SUM(amount) as total_spend
   - RANK() OVER (PARTITION BY time_bucket, category_id ORDER BY total_spend DESC) as brand_rank
   ```
   - Critical for: "Top 5 brands in category" queries

5. **Customer Counts (Unique) - Approximate**
   - Use HyperLogLog (PostgreSQL extension) for approximate unique counts
   - Pre-compute daily unique customers per brand/category/geography
   - Tradeoff: ~2% error rate, but 100x faster than COUNT(DISTINCT)

**Metrics NOT Worth Pre-Computing:**
- Cross-category basket analysis (too high cardinality)
- Customer-level CLV estimates (requires customer_id persistence)
- Arbitrary time window combinations (use running totals windows instead)

---

## From Consumer Spending SME (consumer-spending-sme)

---

**Question 1: Transaction Amount Distributions**

For the synthetic transaction data generation, what statistical distributions should we use for transaction amounts (skewed, log-normal typical for spending)? Should we model at transaction-level or generate pre-aggregated data?

---

**Answer:**

**Modeling Decision: Always model at transaction-level, never pre-aggregated.**

Rationale:
- Pre-aggregated data cannot answer new questions (e.g., "median transaction at Whole Foods for Gen Z in urban areas")
- Anomaly detection requires raw transaction visibility
- Cross-shopping analysis requires individual basket linkage
- Pre-aggregation loses distributional information

**Recommended Distribution: Log-Normal with Category-Specific Parameters**

```python
import numpy as np

def generate_transaction_amount(category: str, income_band: int) -> float:
    """
    Log-normal distribution for transaction amounts.
    Parameters vary by category and income band.
    """
    # Base parameters by category tier
    category_params = {
        'essential': {'mu': 3.0, 'sigma': 0.8},   # groceries, utilities
        'mid': {'mu': 3.5, 'sigma': 1.0},           # general retail
        'premium': {'mu': 4.2, 'sigma': 1.2},      # luxury, electronics
        'dining': {'mu': 3.2, 'sigma': 0.9},       # restaurants
        'fast_food': {'mu': 2.2, 'sigma': 0.6},    # QSR
    }

    # Income multiplier (premium brands show stronger income effect)
    income_multipliers = {
        1: 0.6,   # <$25K
        2: 0.75,  # $25K-$50K
        3: 0.9,   # $50K-$75K
        4: 1.0,   # $75K-$100K (baseline)
        5: 1.3,   # $100K-$150K
        6: 1.7,   # $150K+
    }

    params = category_params[get_category_tier(category)]
    amount = np.random.lognormal(params['mu'], params['sigma'])
    return round(amount * income_multipliers[income_band], 2)
```

**Distribution Parameters by Category Type:**

| Category Type | Mean | Median | 95th Percentile | Distribution Shape |
|--------------|------|--------|-----------------|-------------------|
| Groceries | $45 | $35 | $120 | Right-skewed |
| Fast Food | $12 | $9 | $28 | Moderately skewed |
| Dining | $38 | $28 | $95 | Skewed |
| Premium Retail | $180 | $95 | $550 | Highly skewed |
| Essential Services | $75 | $55 | $200 | Moderately skewed |

**Key Implementation Notes:**
1. Transaction amounts MUST be generated with controlled randomness (seeded) for reproducibility but with realistic variance (do not use uniform distribution)
2. Inject 1-2% outliers (high-value purchases) to simulate real fraud/anomaly patterns
3. Monthly statements (e.g., subscriptions) should show near-identical amounts across months (low variance)
4. Use Dirichlet distribution for category mix proportions per income band to maintain population-level consistency

---

**Question 2: Cross-Shopping Panel Data**

How should customer_id be handled for cross-shopping/retention analysis? If using synthetic panel data, what panel size is realistic (1M+ panelists vs. smaller sample)?

---

**Answer:**

**Panel Size Recommendation: 100,000-500,000 unique panelists for Phase 1**

Rationale:
- 1M+ panelists creates significant storage and join complexity
- 100K panelists with 2 years of data = ~5M transaction rows (manageable)
- Statistical validity requires enough panelists to represent rare segments (high-income, rural areas)
- Cross-shopping analysis requires customer persistence (same customer appears across multiple merchants)

**Panel Structure:**

```
Panelists Table:
├── panelist_id (UUID) - persistent across all transactions
├── income_band (enumerated)
├── generation (enumerated)
├── geography (state + metro)
├── panel_start_date
└── panel_weight (scaling factor to represent population)

Transactions Table:
├── transaction_id (UUID)
├── panelist_id (FK → panelists)
├── timestamp
├── amount
├── brand_id
├── category_id
└── channel
```

**Critical Requirements for Cross-Shopping Analysis:**

1. **Panelist Persistence**: Each panelist must have 50-200 transactions over 2 years (realistic purchase frequency)
2. **Cross-Merchant Visibility**: Panelists should shop at 3-10 different brands within a category (enables cross-shopping metrics)
3. **Known Attrition**: 5-10% annual panel attrition simulates real panel decay
4. **Represents Population**: Panel weights allow scaling to national estimates

**Panel Size vs. Analysis Capability:**

| Analysis Type | Minimum Panelists | Recommended Panel |
|---------------|-------------------|-------------------|
| Overall market share | 10,000 | 50,000 |
| Brand-level share | 5,000 per brand | 25,000 per brand |
| Cross-shopping matrix | 20,000 | 100,000 |
| Gen Z specific analysis | 2,000 | 10,000 |
| Rural geography | 1,000 | 5,000 |

**Data Generation Approach:**
- Generate panelist roster first (demographics, geography)
- Generate transactions per panelist using behavioral model
- Ensure cross-shopping co-occurrence probabilities match expected overlap (30-40% overlap for adjacent competitors is realistic)

---

**Question 3: Time-Series Aggregation Strategy**

What time-series aggregation strategies balance query performance with analytical flexibility (pre-aggregated monthly tables vs. on-the-fly daily aggregation)?

---

**Answer:**

**Recommended Strategy: Hybrid with Continuous Aggregates + Query-Time Rollup**

**Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    TIMESERIES STORAGE                      │
├─────────────────────────────────────────────────────────────┤
│  Raw Transactions (hypertable, uncompressed)                │
│  - Retention: 90 days uncompressed                          │
│  - Partitioned: daily chunks                                │
│  - Indexed: brand_id, category_id, panelist_id, timestamp    │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Daily Rolls    │ │  Weekly Rolls   │ │  Monthly Rolls  │
│  (continuous)   │ │  (continuous)   │ │  (continuous)   │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ - 90 days       │ │ - 2 years       │ │ - 7 years       │
│ - brand/cat/geo│ │ - brand/cat/geo │ │ - brand/cat/geo │
│ - generation/  │ │ - generation/   │ │ - generation/  │
│   income        │ │   income        │ │   income        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Query Routing Strategy:**

| Query Type | Route To | Rationale |
|------------|----------|-----------|
| "Today" / "Yesterday" | Raw transactions | Need hour-level granularity |
| Last 7-30 days | Daily aggregates | Fast + sufficient granularity |
| 30-90 days | Daily aggregates | Pre-computed, fast |
| 3-12 months | Weekly aggregates | Reduces noise, fast |
| 1-5 years | Monthly aggregates | Trend analysis, minimal detail |
| >5 years | Quarterly aggregates | Long-term secular trends |
| Arbitrary date range | Auto-select best aggregate | Match span to appropriate granularity |

**When to Aggregate On-The-Fly:**

Only aggregate from raw transactions when:
1. Query involves unique customer counts (not pre-computed)
2. Query spans <14 days AND requests hour-level detail
3. Query requires non-standard bucketing (e.g., "bi-weekly")
4. Pre-aggregates cannot satisfy the specific dimension combination requested

**Performance Benchmarks to Target:**

| Data Volume | Raw Query | Daily Aggregate | Monthly Aggregate |
|-------------|-----------|------------------|-------------------|
| 10M rows | 800ms-2s | 50-150ms | 20-50ms |
| 100M rows | 3-8s | 100-300ms | 50-100ms |
| 1B rows | 15-60s | 300-800ms | 100-200ms |

**Key Insight:** Pre-aggregation provides 5-10x performance improvement. The 7-year monthly aggregate will be queried most often for trend analysis and should be heavily optimized.

---

## From Market Analyst SME (market-analyst-sme)

---

**Question 1: Aggregation Level for Time-Series**

What aggregation level is appropriate for synthetic transactions? Daily? Weekly? Monthly? This affects what time-series analysis is meaningful.

---

**Answer:**

**Primary Recommendation: Daily granularity for synthetic transactions (with weekly/monthly pre-aggregates)**

| Time Horizon | Natural Aggregation | Use Case |
|--------------|---------------------|----------|
| 0-30 days | Daily | Same-store sales, daily trends, anomaly detection |
| 1-6 months | Weekly | Weekly comps, rolling trends |
| 6-24 months | Monthly | Monthly comps, category trends, seasonal analysis |
| 2-5 years | Quarterly | Year-over-year, strategic trends |
| 5+ years | Annual | Long-term secular analysis |

**Why Daily is the Right Base Granularity:**

1. **Pattern visibility**: Holiday spikes (Dec 15-24), day-of-week effects (Saturday peaks), event-driven anomalies (Super Bowl) are only visible at daily granularity

2. **Aggregation is lossy**: You cannot reconstruct daily patterns from weekly aggregates, but you CAN reconstruct weekly from daily

3. **Realistic volume**: 10M transactions / 730 days = ~13,700 transactions/day. This is appropriate for a representative panel (not full population). Daily buckets are meaningful.

4. **Downstream aggregates benefit**: Weekly and monthly rollups derived from daily data maintain seasonal patterns. Directly generating monthly data loses intra-month variation.

**Minimum Viable Aggregation Set for Synthetic Data:**
- Raw: Daily bucket transactions (REQUIRED)
- Continuous Aggregate 1: Daily rollups (brand + category + geography)
- Continuous Aggregate 2: Weekly rollups (same dimensions)
- Continuous Aggregate 3: Monthly rollups (same dimensions + generation + income_band)

**What NOT to do:**
- Generate only monthly aggregated data (loses seasonal signal)
- Generate hourly data as base (overkill, storage waste)
- Generate weekly as base (misses day-of-week patterns)

---

**Question 2: Statistical Distributions for Realistic Trends**

What statistical distributions should the synthetic data follow? Normal? Power law? Zipfian? This affects how realistic trend analysis will feel.

---

**Answer:**

**Synthetic Data Must Follow These Distributions:**

| Variable | Distribution | Parameters | Why |
|----------|--------------|------------|-----|
| Transaction amounts | **Log-normal** | mu=3.0-4.5, sigma=0.8-1.3 (by category) | Real spending is right-skewed; normal is wrong |
| Brand market shares | **Power law / Zipfian** | s ~ 1.0-1.5 | Few brands dominate; long tail is realistic |
| Inter-transaction time | **Exponential** | lambda varies by category (0.5-3.0) | Memoryless property matches real purchase timing |
| Category proportions (per income band) | **Dirichlet** | alpha = [0.5, 1.0, 2.0] (concentration) | Constrained to sum=1, realistic variance |
| Daily transaction volume | **Poisson** with overdispersion | mu = base_rate * day_multiplier | Count data with realistic variance |
| Geographic concentration | **Zipfian** across states | s ~ 1.2 | CA, TX, FL dominate;Wyoming small |

**Specific Distribution Implementations:**

**1. Transaction Amounts (Log-Normal):**
```python
# Essential categories: lower mu, tighter sigma
groceries = np.random.lognormal(mean=3.0, sigma=0.8)   # ~$20-40 median

# Premium categories: higher mu, wider sigma
luxury = np.random.lognormal(mean=4.5, sigma=1.3)       # ~$60-200 median
```

**2. Brand Market Share (Power Law):**
```python
# Zipfian distribution for brand shares within category
# Top brand gets rank=1, share proportional to 1/rank^s
def zipfian_shares(n_brands, s=1.0, total=1.0):
    ranks = np.arange(1, n_brands + 1)
    shares = 1 / (ranks ** s)
    return shares / shares.sum() * total

# Realistic: top 3 brands = 50-60% share, rest is long tail
```

**3. Inter-Purchase Timing (Exponential):**
```python
# Fast food: high frequency, lambda=2.0 (mean 0.5 days)
# Groceries: medium frequency, lambda=0.7 (mean ~10 days)
# Travel: low frequency, lambda=0.1 (mean ~70 days)
inter_purchase_days = np.random.exponential(scale=1/lambda)
```

**What NOT to Use:**

| Distribution | Why It's Wrong |
|--------------|----------------|
| Normal for amounts | Spending is never normally distributed; negative values impossible but low-end too high |
| Uniform across brands | Real markets have clear leaders and followers |
| Uniform across geography | Real spending varies 3-5x between states |
| Fixed seasonal factors | Real data has year-over-year variance in seasonal strength |

**Validation Check:** Plot synthetic data distributions against known real-world benchmarks (e.g., US Census retail sales distributions). The synthetic distribution should pass a Kolmogorov-Smirnov test at alpha=0.05 against expected distribution.

---

**Question 3: Anomaly Injection for Eval Framework**

Should the eval framework include known anomalies that the system should detect? If so, what types (seasonal, one-time events, secular trends)?

---

**Answer:**

**Yes, anomaly injection is ESSENTIAL for meaningful evaluation.**

Injecting known anomalies serves two purposes:
1. Tests the system's ability to detect and contextualize anomalies (higher-order insight)
2. Validates that the system correctly attributes anomalies to real events, not data errors

**Recommended Anomaly Types to Inject:**

**Type 1: Seasonal Patterns (Recurring, Predictable)**

| Event | Injection Timing | Expected Magnitude | Affected Categories |
|-------|-----------------|-------------------|---------------------|
| Holiday season | Nov 15 - Dec 24 | +150-300% retail volume | Retail, gift cards |
| Super Bowl | Early February (2 weeks) | +40-60% food/entertainment | Restaurants, snacks |
| Back-to-School | Aug 15 - Sep 15 | +25-40% apparel/electronics | Apparel, office supplies |
| Valentine's Day | Feb 10-14 | +30-50% gifts/dining | Gifts, restaurants |
| Mother's Day | Early May | +50-70% flowers/dining | Florists, restaurants |
| Prime Day | Mid-July (2-3 days) | +80-150% electronics | Electronics, home |

**Type 2: One-Time Events (Non-Recurring)**

| Event | Year | Expected Pattern |
|-------|------|-----------------|
| COVID lockdown | 2020, Mar-May | -70% in-store, +200% online, grocery spike |
| Economic stimulus | 2020, Apr-May | +30% spending spike (stimulus checks) |
| Major weather event | Varies | Localized -50% to +100% spending shifts |
| Brand PR crisis | Varies | -30-60% for affected brand, 2-4 week recovery |

**Type 3: Secular Trends (Gradual, Long-Term)**

| Trend | Time Period | Expected Pattern |
|-------|-------------|-----------------|
| Online channel shift | 2019-2024 | Online share: 15% → 30% (linear growth) |
| Retail apocalypse | 2019-2024 | Mall-based retail: -20% overall |
| Streaming adoption | 2019-2024 | Streaming subscriptions: 3x growth |

**Eval Framework Design:**

```
Anomaly Detection Eval Cases:
├── Recurring (seasonal)
│   ├── "Detect the holiday shopping spike" → Should identify Dec pattern
│   ├── "What caused the February food spike?" → Should reference Super Bowl
│   └── "Compare this year's holiday to last year's" → Should normalize
├── One-time events
│   ├── "Why did March 2020 look different?" → Should detect COVID effect
│   └── "What happened to Brand X in June 2023?" → Should reference specific event
└── Secular trends
    ├── "Is online shopping growing?" → Should show channel trend
    └── "Are malls declining?" → Should show retail secular shift
```

**System Response Expectations:**

For anomaly-related queries, the system should:
1. Correctly identify that an anomaly exists (detection)
2. Attribute to the correct cause (contextualization)
3. Quantify the magnitude vs. baseline (measurement)
4. Compare to prior year same period (seasonal adjustment)

---

**Question 4: Market Share Calculation Method**

How should "market share" be calculated - by transaction count, by spend, by unique customers? All three give different results.

---

**Answer:**

**Standard Definition: Market Share = Brand Spend / Category Spend (%), calculated by spend.**

**Why Spend-Based is the Standard:**

| Method | Use Case | Limitation |
|--------|----------|-----------|
| **Spend-based (RECOMMENDED)** | Investment analysis, revenue comparison | Ignores basket size differences |
| Transaction count | Traffic/visit frequency analysis | Distorts toward low-price brands |
| Unique customers | Customer penetration analysis | Misses frequency and spend depth |

**Spend-Based Market Share Formula:**
```
market_share_pct = (brand_total_spend / category_total_spend) * 100
```

**Three Methods Yield Different Results:**

| Brand | Avg Transaction | Transactions | Unique Customers | Spend Share | Count Share | Customer Share |
|-------|-----------------|--------------|------------------|-------------|-------------|----------------|
| Walmart | $45 | 10,000 | 3,000 | 45% | 40% | 35% |
| Dollar General | $15 | 15,000 | 5,000 | 22% | 35% | 30% |
| Target | $65 | 5,000 | 2,500 | 33% | 25% | 35% |

In this example:
- Walmart dominates by **spend share** (larger baskets)
- Dollar General leads by **transaction count** (low prices, high frequency)
- Target leads by **unique customers** (premium positioning)

**For Proteus, recommend:**

1. **Default to spend-based** market share (industry standard)
2. **Support count-based** as secondary metric (explicitly label)
3. **Support customer-based** for acquisition/penetration analysis
4. **Make the method explicit** in visualization titles: "Market Share by Spend" vs "Share of Transactions"

**Pre-compute all three** as continuous aggregates:
```sql
CREATE MATERIALIZED VIEW brand_category_share_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    brand_id,
    category_id,
    SUM(amount) AS total_spend,
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT panelist_id) AS unique_customers,
    SUM(SUM(amount)) OVER (PARTITION BY time_bucket, category_id) AS category_spend,
    COUNT(*) OVER (PARTITION BY time_bucket, category_id) AS category_transactions,
    COUNT(DISTINCT panelist_id) OVER (PARTITION BY time_bucket, category_id) AS category_customers
GROUP BY 1, 2, 3;
```

This enables instant calculation of all three market share variants without runtime aggregation.

---

## Summary

The cross-SME questions reveal several critical data analytics requirements:

1. **Synthetic data must embed realistic correlations** between income/brand, generation/category, and geography/category. These are not optional -- analysts will immediately detect obviously fake data.

2. **Aggregation strategy is tiered**: raw daily transactions (90 days) → daily/weekly/monthly continuous aggregates (progressively longer retention) → quarterly (7+ years).

3. **Pre-computed derived metrics** (market share %, YoY growth, category mix) are essential for performance and should be computed in continuous aggregates, not at query time.

4. **Statistical distributions must match real-world**: log-normal for amounts, Zipfian for brand shares, exponential for inter-purchase timing.

5. **Anomaly injection** (seasonal, one-time, secular) is essential for meaningful eval framework.

6. **Market share defaults to spend-based**, but transaction-count and customer-count variants should be pre-computed and available.
