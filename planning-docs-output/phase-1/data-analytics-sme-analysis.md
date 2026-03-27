# Data Science SME Analysis: Proteus

## Overview

The Proteus project requires a robust data analytics foundation to support natural-language querying of consumer transaction data. This analysis addresses the data modeling, statistical methodology, and analytical requirements embedded in the HLRD.

---

## Question 1: Default Aggregation and Formatting Rules

**Question:** What default aggregation and formatting rules should apply to different data types? For example, should monetary values always show as currency-formatted, should percentages always include a comparison baseline?

### Recommended Default Aggregation Rules

| Data Type | Default Aggregation | Rationale |
|-----------|---------------------|-----------|
| **Monetary (transaction amounts)** | SUM with AVG secondary | Total spending is primary insight; average provides context |
| **Percentages** | Current period value + baseline comparison (% change) | Analysts need context of whether % is up/down from baseline |
| **Counts (transactions, users)** | COUNT DISTINCT for unique entities; COUNT for events | Distinguishing unique vs. total events is critical |
| **Time-series metrics** | ROLLUP to query granularity (daily/weekly/monthly) | Match display to user intent |
| **Geographic data** | No aggregation (raw labels) | Keep geographic granularity for drill-down |
| **Demographic attributes** | GROUP BY with count distributions | Show proportional breakdown |

### Recommended Formatting Rules

**Monetary Values:**
- Always display as currency with locale-appropriate formatting ($1,234.56 for USD)
- Show compact notation for large values ($1.2M, $3.4B)
- Include currency symbol consistently within a session
- Round to 2 decimal places for individual transactions; 0-2 for aggregates

**Percentages:**
- Always show percentage points AND percentage change from baseline
- Example: "12.5% (+2.3pp vs. prior period)"
- Use consistent decimal places (1-2) within chart types

**Time Values:**
- Date formatting based on granularity:
  - Daily data: "Mar 15, 2024"
  - Weekly: "Week 11, 2024"
  - Monthly: "Mar 2024"
  - Quarterly: "Q1 2024"

**Numeric Counts:**
- Use thousand separators (1,234,567)
- Compact notation for visuals (1.2M)

**Identifiers (transaction IDs, brand names):**
- Left-align in tables
- Use monospace or distinct styling for IDs

### Edge Cases to Handle

1. **Zero values**: Display as "$0.00" or "0%" not blank
2. **NULL/missing data**: Show "N/A" or use visual indicator (dotted line in charts)
3. **Negative monetary values**: Use parentheses or minus sign consistently
4. **Division by zero**: Return "—" or "N/A" with tooltip explanation
5. **Extreme outliers**: Consider winsorizing display or adding "exceeds axis" indicator

---

## Question 2: Synthetic Data Statistical Distributions and Correlations

**Question:** What statistical distributions and correlations should be embedded in the synthetic data to make it analytically interesting? For example, should higher-income bands show higher average transaction amounts at premium brands? Should there be seasonal patterns in specific categories?

### Recommended Statistical Embeddings

#### 1. Income-to-Spending Correlation

```
Transaction Amount ~ Normal(Income_Band_Base × Category_Multiplier, σ)
```

- **Strong correlation**: Higher income bands (5-6) show 3-5x higher average transactions at premium brands
- **Weak/no correlation**: Essential categories (groceries, utilities) show similar spending across income bands
- **Premium brands**: 60-80% of high-income transactions; 15-25% of low-income transactions

#### 2. Age Generation × Category Affinity

| Generation | Primary Categories | Avg Transaction Premium |
|------------|---------------------|-------------------------|
| Gen Z (18-27) | Fast food, streaming, fashion | +15% at trend/cult brands |
| Millennials (28-43) | Home goods, childcare, dining | +20% at family brands |
| Gen X (44-59) | Automotive, healthcare, travel | +25% at quality brands |
| Boomers (60-78) | Healthcare, groceries, gifts | +10% at traditional brands |

#### 3. Seasonal Patterns (Autoregressive Components)

- **Monthly seasonality factors** (multiplicative):
  - January: 0.85 (post-holiday decline)
  - February: 0.90 (Valentine's boost in gifts/dining)
  - November: 1.25 (pre-holiday)
  - December: 1.35 (peak holiday spending)

- **Day-of-week patterns**:
  - Weekend transactions: +35% volume, +20% avg amount
  - Friday/Saturday: Highest retail activity
  - Monday: Lowest spending day

- **Time-of-day patterns**:
  - 11am-2pm: Peak dining
  - 6pm-9pm: Peak entertainment/streaming
  - 10am-4pm: Peak retail

#### 4. Geographic Variation

- **Regional multipliers** (median income adjusted):
  - Northeast: 1.15x baseline
  - West Coast: 1.20x baseline
  - Midwest: 0.95x baseline
  - South: 0.90x baseline (with variance by metro area)

- **Urban vs. Rural**:
  - Urban: +40% transaction frequency, +25% avg amount
  - Rural: +15% essential category share

#### 5. Brand Loyalty and Repeat Purchase

- **Repeat purchase probability**: 0.35 within 30 days for same category
- **Brand switching**: Higher in low-income/younger segments
- **Premium retention**: High-income segments show 70% repeat at premium brands

#### 6. Statistical Distributions to Implement

| Metric | Distribution | Parameters |
|--------|--------------|------------|
| Transaction amount | Log-normal | μ=3.5, σ=1.2 (skewed positive) |
| Inter-transaction time | Exponential | λ varies by category |
| Daily transaction count | Poisson | μ varies by day-type |
| Category proportions | Dirichlet | α vector based on income/age |

#### 7. Known Patterns to Embed

1. **Holiday spikes**: December 15-24 shows 200-300% normal volume
2. **Back-to-school**: August-September category shifts
3. **Super Bowl**: Food/party category spike in early February
4. **Tax refund season**: March-April increased spending
5. **Summer travel**: June-August entertainment/travel peaks

### Synthetic Data Quality Considerations

- **No perfect correlations**: Real data has noise; embed 5-10% random variance
- **Missing data simulation**: 0.5-2% null rates in non-critical fields
- **Outlier injection**: 1-2% of transactions as outliers (fraud simulation, high-value purchases)
- **Temporal drift**: Brand preferences shift 2-3% year-over-year

---

## Data Modeling Recommendations

### 1. Core Data Schema

```
transactions
├── id (UUID, PK)
├── timestamp (TIMESTAMPTZ, NOT NULL)
├── amount (DECIMAL(10,2), NOT NULL)
├── brand_id (FK → brands)
├── category_id (FK → categories)
├── merchant_id (FK → merchants)
├── location_id (FK → locations)
├── user_id (UUID) — anonymized
└── metadata (JSONB)

dimensions
├── brands: id, name, tier (premium/mid/budget), category_affinity
├── categories: id, name, essential_score (0-1), seasonality_factor
├── locations: id, city, state, region, urban_rural, income_index
├── users: id, age, generation, income_band, geography_id
└── time: auto-generated via TimescaleDB
```

### 2. TimescaleDB Hypertable Design

- **Chunk interval**: Daily chunks for 2-year span (730 chunks)
- **Compression**: After 30 days, compress with gzip
- **Retention**: 7 years for full fidelity, then rollup to monthly

### 3. Continuous Aggregates (Required)

```sql
-- Daily rollup
CREATE MATERIALIZED VIEW daily_transactions
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    brand_id,
    category_id,
    income_band,
    generation,
    region,
    SUM(amount) AS total_amount,
    COUNT(*) AS transaction_count,
    AVG(amount) AS avg_amount
GROUP BY 1, 2, 3, 4, 5, 6;

-- Weekly and monthly similar structure
```

### 4. Indexing Strategy

```sql
-- Time-based queries
CREATE INDEX idx_transactions_timestamp ON transactions (timestamp DESC);

-- Dimension lookups
CREATE INDEX idx_transactions_brand ON transactions (brand_id, timestamp DESC);
CREATE INDEX idx_transactions_category ON transactions (category_id, timestamp DESC);
CREATE INDEX idx_transactions_user ON transactions (user_id, timestamp DESC);

-- Composite for common queries
CREATE INDEX idx_transactions_time_cat_amt
ON transactions (timestamp DESC, category_id)
INCLUDE (amount);
```

---

## Visualization Selection Logic

### Auto-Chart Selection Rules

| Query Pattern | Data Shape | Recommended Chart |
|--------------|------------|-------------------|
| "Show trend over time" | 1 temporal dimension, 1 metric | Line chart |
| "Compare X across categories" | 1 categorical, 1+ metrics | Grouped bar chart |
| "Show proportion of X" | 1 categorical with percentage | Pie/Donut chart |
| "Distribution of amounts" | Numeric series | Histogram/KDE |
| "X vs Y scatter" | 2 numeric dimensions | Scatter plot |
| "Geographic breakdown" | Geographic dimension | Choropleth map |
| "Time series with breakdown" | Time + categorical | Stacked area chart |

### Default Formatting for ECharts

```javascript
const defaultEChartsConfig = {
  line: { smooth: true, showSymbol: false, areaStyle: null },
  bar: { barWidth: '60%', label: { show: true, position: 'top' } },
  pie: { radius: ['40%', '70%'], label: { formatter: '{b}: {d}%' } },
  tooltip: { trigger: 'axis', shared: true },
  legend: { bottom: 0, type: 'scroll' }
};
```

---

## Risks and Recommendations

### Risk 1: Query Performance at Scale

**Concern**: 10M+ rows with complex aggregations may exceed 5-second SLA.

**Mitigation**:
- Pre-compute common aggregations as continuous aggregates
- Implement query result caching with 5-minute TTL
- Use TimescaleDB compression for historical data
- Limit result set to top 1000 rows with pagination

### Risk 2: Statistical Validity of Synthetic Data

**Concern**: Embedded patterns may be too "clean" or obvious.

**Mitigation**:
- Inject realistic noise (5-10% variance on correlations)
- Vary seasonal factors year-over-year
- Include counter-intuitive patterns in 5% of data

### Risk 3: Aggregation Ambiguity

**Concern**: NL queries like "show spending" are ambiguous without time context.

**Mitigation**:
- Implement clarification prompts when granularity unclear
- Default to last 30 days for spending queries
- Include default time range in all chart titles

---

## Questions for Other SMEs

### For AI/NLP SME (ai-nlp-sme):

1. **Temporal ambiguity resolution**: How does the NLP layer handle queries like "show spending" without explicit time range? Should we default to last 30 days, current month, or ask for clarification?

2. **Multi-tool orchestration**: With 10-50 tools each having 30+ dimensions, how should tool selection handle compound queries that span multiple tools?

3. **Clarification generation**: When aggregation granularity is ambiguous, what criteria should the NLP layer use to generate appropriate clarification questions?

4. **Confidence thresholds**: What tool selection confidence level should trigger a clarification prompt vs. proceeding with best guess?

### For UX Designer (ux-designer-sme):

1. **Visualization comparison**: How should users compare two different time periods' visualizations side-by-side? Tabbed interface or split-screen?

2. **Chart annotation**: Should analysts be able to annotate charts with insights or notes? If so, where should these annotations persist?

3. **Data table placement**: For charts that also show raw data, should tables be accessible via toggle, always visible below, or in expandable drawer?

4. **Query history navigation**: With canvas updates per query, what interaction pattern helps users navigate back to prior visualizations without losing context?

### For Integration Engineer (integration-engineer-sme):

1. **Caching strategy**: Should aggregation results be cached? What's the appropriate invalidation strategy when underlying data might be considered "current" vs "historical"?

2. **Real-time data**: Is any component expected to show real-time or near-real-time data, or is all data effectively batch-loaded synthetic data?

3. **API pagination**: For result sets exceeding display capacity, should API return paginated results with cursor-based pagination or offset-based?

4. **Multi-tenancy**: Should the data layer support tenant isolation, or is this a single-tenant demonstration system?

### For Market Analyst (market-analyst-sme):

1. **Benchmark data**: Should synthetic data include externally benchmarkable metrics (e.g., category spending as % of disposable income) that mirror real market research?

2. **Category taxonomy**: Is the current essential/premium category split sufficient, or do you require a more detailed 2-3 level category hierarchy for meaningful analysis?

3. **Competitive positioning**: Should synthetic brand data intentionally include known competitive positioning (e.g., Brand X is known for value, Brand Y for premium)?

4. **Metric definitions**: Are there standard market research metrics (wallet share, category penetration, repurchase rate) that should be pre-computed as continuous aggregates?

### For Consumer Spending SME (consumer-spending-sme):

1. **Behavioral patterns**: Are there specific consumer spending behavioral patterns (e.g., deal-seeking, brand loyalty, omnichannel) that should be statistically modeled in synthetic data?

2. **Life-stage modeling**: Should spending patterns correlate with life-stage indicators (new parent, homeowner, retiree) beyond simple age bands?

3. **Purchase frequency**: What transaction frequency distributions should be modeled per category to reflect realistic consumer behavior?

4. **Basket analysis**: For multi-category transactions, should there be realistic co-purchase patterns (e.g., groceries + household items)?

---

## Summary

The Proteus data layer requires:

1. **Consistent formatting standards** for monetary, percentage, and temporal data types with clear default behaviors
2. **Statistically valid synthetic data** with realistic income/age/geography correlations, seasonal patterns, and brand affinities
3. **TimescaleDB-optimized schema** with daily partitioning, continuous aggregates, and appropriate indexing
4. **Clear aggregation defaults** that balance simplicity with analytical rigor

These foundations enable the natural-language interface to deliver fast, accurate, and visually coherent analytical insights across the 10M+ transaction dataset.
