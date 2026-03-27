# Consumer Spending Behavior SME Analysis
## Proteus Requirements Elaboration — Phase 1

---

## Answers to [SME:ConsumerSpending] Questions

### Question 1: Core Analytical Capabilities and Tool Categories

**Essential Tool Categories (Must-Have)**

1. **Market Share Analysis**
   - Brand-level share of wallet within category
   - Share trajectory over time (gaining/losing share)
   - Cross-category market share (where does brand rank across adjacent categories)
   - *Data dimensions required*: brand, category, time range, geography, demographic cohort

2. **Cross-Shopping Behavior**
   - Multi-brand purchasing patterns (which brands appear in same shopping basket)
   - Brand loyalty vs. brand switching metrics
   - Category adjacency analysis (which categories co-purchase)
   - *Data dimensions required*: brand, category, time range, customer_id (for cross-shopping linkage), transaction_frequency

3. **Spending Volume Trends**
   - Category-level transaction counts and dollar volumes
   - Year-over-year and month-over-month growth rates
   - Seasonally-adjusted vs. raw trend lines
   - *Data dimensions required*: category, time range (daily/weekly/monthly/quarterly), geography, channel

4. **Customer Demographics Analysis**
   - Spending distribution by generation (Gen Z, Millennial, Gen X, Boomer+)
   - Income band spending patterns
   - Age-by-category spending heat maps
   - *Data dimensions required*: generation, income_band, age_bucket, category, brand

5. **Geographic Performance**
   - State/CBSA/MSA-level spending patterns
   - Urban vs. suburban vs. rural spending differentiation
   - Regional category preferences
   - *Data dimensions required*: geography (hierarchical: state > CBSA > MSA > zip), category, brand

6. **Channel Performance**
   - Card-present (in-store) vs. card-not-present (online, mobile)
   - Channel trend over time
   - Category-channel affinity
   - *Data dimensions required*: channel, category, time_range, brand

7. **Card Type Analysis**
   - Credit vs. debit vs. prepaid spending distribution
   - Card type by category and income band
   - *Data dimensions required*: card_type, category, income_band, generation

**Important but Secondary (Should-Have)**

8. **Customer Retention / Cohort Analysis**
   - Repeat purchase rates by brand and category
   - Cohort retention curves
   - Customer lifetime value estimation
   - *Note*: Requires customer_id linkage which may not be present in all transaction panels

9. **Price Sensitivity / Basket Analysis**
   - Average ticket by category/brand/income
   - Price elasticity proxies (transaction count response to seasonal promotions)
   - *Note*: This is inferential from transaction data rather than explicit

10. **Competitive Intensity Metrics**
    - Category concentration (HHI indices)
    - New entrant velocity
    - Category commoditization trends

**Nice-to-Have**

11. **Real-Time / Near-Real-Time Spending Signals**
    - Daily or weekly spending accelerations
    - News-event response tracking
    - Requires higher-frequency data refresh

12. **Private Label / Store Brand Analysis**
    - National brand vs. private label share
    - Requires retailer-level data with brand classification

---

### Question 2: Complete Dimension Set and Cardinalities

**Dimensional Structure for Synthetic Data**

| Dimension | Cardinality (Realistic) | Notes |
|-----------|-------------------------|-------|
| **brand** | 100-200 distinct brands | Mix of national brands and large retailers; include parent-subsidiary relationships |
| **merchant_category** (MCC-based) | 40-60 categories | Based on ~50 high-spend MCC groups (not full 600+ MCC codes) |
| **geography** | | Hierarchical structure |
| - state | 51 (50 US + DC) | Full coverage required |
| - CBSA (metro area) | 350-400 | Major metros |
| - MSA | 380-400 | Subset of CBSAs |
| - zip code | 20,000-30,000 | For synthetic data, 3-digit zip aggregates may suffice |
| **time_range** | Daily granularity | 2+ years = 730+ days; synthetic should support daily, weekly, monthly aggregation |
| **generation** | 5 cohorts | Gen Z (18-27), Millennial (28-43), Gen X (44-59), Boomer (60-78), Silent (79+) |
| **income_band** | 6-8 bands | <$25K, $25K-$50K, $50K-$75K, $75K-$100K, $100K-$150K, $150K-$200K, $200K+ |
| **age_bucket** | 6-8 buckets | 18-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75+ (alternative to generation) |
| **card_type** | 3-4 types | Credit, Debit, Prepaid, Corporate |
| **channel** | 3 types | In-store (card-present), Online (card-not-present), Mobile (card-not-present with mobile indicator) |
| **aggregation_level** | 4 levels | Transaction-level, Daily-agg, Weekly-agg, Monthly-agg |

**Secondary Dimensions (Important for Filtering)**

| Dimension | Cardinality | Notes |
|-----------|-------------|-------|
| **day_of_week** | 7 | Weekend vs. weekday patterns are significant |
| **month** | 12 | Seasonal patterns |
| **quarter** | 4 | Quarterly reporting cycles |
| **is_holiday_season** | 2 (bool) | Nov-Dec spike is massive |
| **is_recession_period** | 2 (bool) | If spanning 2008-2009 or 2020 |
| **region** | 4-5 | Northeast, Southeast, Midwest, Southwest, West (US Census regions) |

**Dimensions Analysts Expect to Filter and Group By**

*Primary filters (high-value, always requested)*:
- brand, merchant_category, geography, time_range, generation, income_band

*Secondary filters (analyst-level)*:
- channel, card_type, day_of_week

*Group-by dimensions (for aggregation queries)*:
- merchant_category, brand, state, generation, income_band, month, quarter

---

### Question 3: Essential Real-World Spending Patterns for Synthetic Data Credibility

**Critical Patterns (Analyst Will Reject as Fake Without)**

1. **Holiday Season Spike (Q4)**
   - Retail categories: 25-40% volume increase in Nov-Dec
   - Off-price retail: Significant Dec spike
   - Gift card categories: Dec peaks, Jan redemption
   - Restaurant: Moderate Dec increase
   - *Implementation*: Need 3-4x normal transaction volume for Nov-Dec in retail categories

2. **Back-to-School Season (Aug-Sep)**
   - Office supplies, electronics, apparel
   - Less pronounced than holiday but significant
   - 15-25% increase in affected categories

3. **Super Bowl / Big Event Spending**
   - Food & beverage, restaurant, entertainment
   - Predictable seasonal noise

4. ** generational Spending Profiles**
   - Gen Z: Higher % to apparel, fast fashion, food delivery, gaming
   - Millennials: Housing-adjacent, kids categories, groceries
   - Gen X: Home improvement, healthcare, financial services
   - Boomers: Healthcare, travel, dining out, subscriptions
   - *Implementation*: Category spend share varies significantly by generation; not just volume but *proportion*

5. **Income-to-Brand Correlations**
   - Upper income ($150K+): Luxury brands, travel, premium services
   - Mid income: Discount retailers, value brands, mid-scale dining
   - Lower income: Grocery, discount stores, essentials
   - High income do NOT shop at Walmart; this correlation is strong and visible

6. **Geographic Category Mix**
   - Coastal metros: More dining out, entertainment, fitness
   - Sunbelt: Higher outdoor, pool maintenance, AC-related
   - Midwest/Rust Belt: Higher grocery, utility spending
   - Rural: Higher auto-related, lower entertainment

7. **Card Type by Category**
   - Credit cards: Travel, dining, entertainment (rewards optimization)
   - Debit: Groceries, utilities, everyday spending
   - Prepaid: Underbanked populations, gift cards

8. **Weekend vs. Weekday Patterns**
   - Retail: Saturday highest, Monday lowest
   - Restaurants: Friday/Saturday peaks
   - Groceries: Saturday/Sunday peaks

9. **Channel Shifts Over Time**
   - Online growing share year-over-year (2019-2024 trend)
   - In-store declining proportionately
   - Acceleration during COVID period (2020)

10. **Category Seasonality Signatures**
    - Groceries: Relatively flat (less seasonal variation)
    - Apparel: Strong Q4, weak Q1
    - Home improvement: Spring/Summer peak
    - Tourism/Travel: Summer peak, December dip
    - Florists: Valentine's Day (Feb), Mother's Day (May) spikes

**Anti-Patterns (Will Make Data Look Fake)**

- Uniform distribution across time (no spikes)
- All generations have identical spending profiles
- All geographies have identical category mixes
- No correlation between income and brand selection
- Transaction amounts normally distributed (real spending is log-normal)
- No brand co-occurrence patterns
- Deterministic patterns (identical every year)

**Minimum Viable Pattern Set for Credibility**

1. Q4 holiday spike (25-40% retail increase)
2. Generation x Category spend proportions
3. Income x Brand correlations
4. State-level geographic variation in category mix
5. Weekend/weekday patterns by category
6. Channel growth trend (online gaining share)
7. Category-specific seasonality signatures

---

## Questions for Other SMEs

**For AI/NLP Architecture SME:**
- How does the RAG-based tool retrieval handle cases where a user query spans multiple analytical capabilities (e.g., "show me Target's market share trend by generation compared to Walmart" requires both market share and demographic analysis)?
- What is the strategy for disambiguating dimension references when users say vague terms like "recently," "most," or "growing"? How do you map these to specific time ranges or comparison operators?
- How will the system handle dimension extraction when users use synonyms or layman terms (e.g., "young people" for Gen Z, "credit card" broadly for all card types)?

**For UXDesigner SME:**
- When presenting market share results, what chart types effectively communicate both absolute share and share trajectory (gaining/losing)? Analysts typically want to see both at once.
- For cross-shopping analysis results (potentially many brand pairs), how should the UI handle visualization when there are 10+ significant cross-shopping relationships?
- When a user query is ambiguous and requires HITL clarification, what interaction pattern keeps users engaged without breaking conversational flow?

**For DataScientist SME:**
- For the synthetic transaction data generation, what statistical distributions should we use for transaction amounts (skewed, log-normal typical for spending)? Should we model at transaction-level or generate pre-aggregated data?
- How should customer_id be handled for cross-shopping/retention analysis? If using synthetic panel data, what panel size is realistic (1M+ panelists vs. smaller sample)?
- What time-series aggregation strategies balance query performance with analytical flexibility (pre-aggregated monthly tables vs. on-the-fly daily aggregation)?

**For IntegrationEngineer SME:**
- What is the expected cardinality for tool parameters in the REST API? If a query specifies brand, category, geography, generation, income_band, time_range simultaneously, how does the API handle this (AND vs. OR logic)?
- For TimescaleDB, what hypertable partitioning strategy supports both time-range queries and high-cardinality dimension filters (e.g., filtering by specific brand + zip simultaneously)?
- How should brand aliases and name normalization be handled at the data ingestion layer vs. query layer?

**For MarketAnalyst SME:**
- What specific competitive metrics (HHI, concentration ratios) are analysts most commonly requesting? Should these be pre-calculated in the synthetic data or computed on-the-fly?
- Are there industry-standard category groupings beyond MCC codes that analysts expect (e.g., "discretionary" vs. "non-discretionary" classifications, "consumer staples" vs. "consumer cyclicals")?
- What time periods or historical events should the synthetic data span to enable meaningful trend analysis (e.g., pre-COVID, COVID, post-COVID periods)?

---

## Assumptions and Risks

### Assumptions

1. **Panel Data Source**: The synthetic data models a consumer panel (not full population). This is how most alternative data providers (Facteus, Earnest, Bloomberg Second Measure) structure their products. Panel composition and scaling methodology affects representativeness.

2. **No Customer-Level Linking**: Real alternative data often lacks persistent customer_id across merchants. We assume the synthetic data can simulate cross-shopping patterns through controlled co-occurrence but may not support true customer-level journeys.

3. **MCC-Based Category Codes**: We assume merchant categories map to MCC codes or MCC groups. Full MCC taxonomy (600+ codes) is overkill; 40-60 aggregated categories is sufficient.

4. **US-Focused Data**: The HLRD implies US consumer transaction data. International patterns (different holiday calendars, geographic hierarchies) are not addressed.

5. **Seeded Determinism**: Python Faker with seeding provides reproducibility but may produce patterns that repeat identically each year (real spending has stochastic variation even in seasonal patterns).

### Risks

1. **Brand Correlations Too Strong**: If synthetic data over-correlates income and brand, analysts will notice. Real spending has significant within-income-band variance.

2. **Missing Anomalous Events**: Synthetic data spanning 2020 COVID period will look strange if it doesn't model the massive channel shift to online. If spanning 2008, it needs recession patterns.

3. **Aggregation Masks Granularity**: Pre-aggregated monthly data may not support week-level or day-level queries that analysts want for event-driven analysis.

4. **Scale vs. Realism Trade-off**: 10M transactions across 2 years is ~13,700 transactions/day. This is low for a national dataset. Real transaction data providers handle billions of monthly transactions scaled to represent the population.

5. **Brand Name Recognition**: Using recognizable real brand names creates liability but also credibility. Synthetic brand names may feel inauthentic. This is a judgment call.

---

## Summary

The three core SME questions establish a framework for Proteus:

1. **Tool Categories**: 7 essential categories (market share, cross-shopping, spending trends, demographics, geography, channel, card type) plus 3-4 important secondary categories form the tool registry.

2. **Dimensions**: A hierarchical geographic structure (state > CBSA > MSA > zip), ~50 merchant categories, 5 generation cohorts, 6-7 income bands, 3 card types, 3 channels, and full temporal coverage are the minimum viable dimensional model.

3. **Synthetic Data Patterns**: Holiday spikes, generational profiles, income-brand correlations, geographic variation, and seasonal signatures must be present. Missing these will make synthetic data appear obviously fake to analysts familiar with real transaction data.

The synthetic data layer is the foundation. If it lacks credible spending patterns, no amount of NLP sophistication will make the tool useful. Investment in pattern modeling is critical.
