# Market Analyst SME Answers — Phase 2 Cross-SME Consultation

## Overview

This document answers the cross-SME questions directed at the Market Analyst SME from AI/NLP, Integration Engineer, and Consumer Spending SMEs. Each question is quoted followed by a detailed answer with reasoning from the analyst/investor perspective.

---

## From AI/NLP SME (ai-nlp-sme)

### Question 1: Multi-Turn Context Window

> How many conversation turns should the system maintain for context? Analysts often ask follow-up questions ("drill into Brand X", "now compare to Brand Y").

**Answer: Maintain 6-8 conversation turns as the primary context window, with explicit session anchoring.**

**Reasoning:**

From the analyst workflow perspective, follow-up queries are the highest-value interaction pattern. Consider this realistic scenario:

1. User: "Show me Target's market share vs Walmart in grocery over the past year"
2. System: [shows market share chart]
3. User: "Drill into Q3" (follow-up on time dimension)
4. User: "Now compare that to Amazon" (Brand X added to comparison)
5. User: "What about by generation?" (adds demographic dimension)
6. User: "Has that Gen Z preference been growing?" (temporal trend on a segment)

Steps 3-6 all reference step 1-2 context. Losing that context breaks the analytical flow entirely.

**Specific recommendations:**

1. **Active context window**: 6-8 turns captures the typical drill-down sequence without token bloat
2. **Session anchor**: The first query in a session should be preserved as a "session anchor" that is always available, even if the sliding window moves past it
3. **Explicit tool-result binding**: When a user says "that" or "those results," the system must know exactly which prior tool call produced them. Tag each tool result with an internal reference ID visible in the observability panel
4. **Tool-change detection**: When the user switches to a new analytical topic (different brand/category), treat this as a new session context rather than accumulating irrelevant history

**Counterargument addressed**: Some might say "unlimited context is better." In practice, analysts do not maintain focused analytical conversations beyond 6-8 turns on a single topic. After that, they typically start fresh or export results and begin a new analysis. Unbounded context wastes tokens and introduces noise.

---

### Question 2: Confidence Signaling

> Should the system indicate confidence in its tool selection? Analysts would value knowing "I'm 72% confident this is a market share query."

**Answer: Yes, expose confidence at the tool selection level, but present it as a relative indicator, not a percentage.**

**Reasoning:**

Analysts are trained to be skeptical of single-number probabilities from systems they don't fully understand. A raw "72% confident" invites misuse (is 72% good enough to act on?) and creates calibration burden on the user.

**Recommended presentation format:**

1. **Confidence tier labels** rather than numbers:
   - "High confidence" (top candidate similarity >0.85)
   - "Moderate confidence" (top candidate 0.70-0.85)
   - "Low confidence — clarifying" (top candidate <0.70, triggering HITL)

2. **Alternative indicator**: Show top 2-3 candidate tools with their relative scores when confidence is moderate:
   ```
   Selected: Market Share Comparison (high confidence)
   vs. Category Trends (similarity: 0.34)
   ```

3. **Why not raw percentage**: Analysts will compare 72% to 70% and make decisions on 2% confidence differences. This is not meaningful at this level of abstraction. The tier system communicates "trust this result" vs. "verify this result" without false precision.

**What this enables:**
- Power users can set their own threshold for when to trust vs. verify
- The eval framework can track accuracy by confidence tier (do "high confidence" selections actually prove correct 90%+ of the time?)
- Low-confidence selections that prove correct are learning signals for tool definition improvements

---

### Question 3: Fallback Behavior for Low Confidence

> When tool selection confidence is low, what should happen? Ask for clarification? Return multiple interpretations? Make a best guess?

**Answer: For low confidence (<0.70 threshold), always ask for clarification. Do NOT make a best guess.**

**Reasoning:**

The analyst use case has a critical asymmetry: a wrong tool selection wastes significant analyst time (they may act on misleading data) and destroys trust in the system. The cost of asking for clarification is a single extra turn; the cost of acting on wrong analysis can be a bad investment decision.

**Specific behavior by confidence tier:**

| Confidence Level | Threshold | Behavior |
|-----------------|-----------|----------|
| High | >0.85 | Proceed with selected tool |
| Moderate | 0.70-0.85 | Proceed, but show competing candidates in observability panel |
| Low | <0.70 | Pause for HITL clarification |

**Low confidence clarification prompt should:**
1. State what the system understood ("It looks like you're asking about...")
2. Present 2-3 most likely interpretations as explicit options
3. Ask the user to confirm or correct

**Example low-confidence prompt:**
```
I'm not certain which analysis fits your question. Did you want:
A) Target's market share compared to Walmart
B) Target's sales trends over time
C) Target's customer demographics breakdown
[Please select one, or rephrase your question]
```

**What NOT to do:**
- Do not return multiple interpretations simultaneously (splits user attention, complicates visualization)
- Do not make a best guess and return it (risks wrong analysis)
- Do not silently pick the top candidate (user loses agency without knowing)

---

## From Integration Engineer SME (integration-engineer-sme)

### Question 1: Canonical Time Period Definitions

> "Last quarter" might mean: Calendar quarter (Q1 = Jan-Mar), Rolling quarter (prior 90 days), or Most recently completed 13-week period. What definition should the system use?

**Answer: Calendar quarter is the canonical definition. Provide rolling quarter as an explicit opt-in option.**

**Reasoning:**

In institutional investment research, calendar quarters are the universal reporting standard. Quarterly earnings, annual reports, and consensus estimates are all structured around calendar quarters. Using any other definition creates friction with external data sources and analyst mental models.

**Specific definitions to implement:**

| Term | Canonical Interpretation |
|------|--------------------------|
| "Last quarter" | Most recently completed calendar quarter (e.g., on June 15, this means Q1) |
| "This quarter" | Current calendar quarter to date (may be partial data) |
| "Q3 2024" | July 1 - September 30, 2024 |
| "Year-to-date" (YTD) | January 1 of current year to today |
| "Last 30 days" | Explicit rolling window — user said "30 days," not "month" |
| "Last 6 months" | Rolling window — use as stated |

**Key insight for the dimension extraction layer:** The parser must distinguish between:
- **Reporting periods** (calendar-based, used in competitive analysis)
- **Rolling windows** (explicit duration, used for tactical queries like "last 4 weeks")

If a user says "last quarter performance," calendar quarter is almost certainly what they mean. If they say "last 90 days of data," use the rolling window.

**API design implication**: The time dimension in the API request should carry a `period_type` field: `"calendar" | "rolling" | "event_based"`. The dimension extractor sets this based on query phrasing.

---

### Question 2: Competitive Metrics (HHI, Concentration Ratios)

> What specific competitive metrics (HHI, concentration ratios) are analysts most commonly requesting? Should these be pre-calculated in the synthetic data or computed on-the-fly?

**Answer: HHI is the most commonly requested concentration metric. Pre-calculate as continuous aggregates for daily/weekly granularity; compute monthly/quarterly on-the-fly from daily aggregates.**

**Reasoning:**

**HHI (Herfindahl-Hirschman Index)** is the standard measure of market concentration in antitrust and competitive analysis. It is calculated as the sum of squared market share percentages (e.g., a market with three players at 50%, 30%, 20% has HHI = 50^2 + 30^2 + 20^2 = 3800).

**Pre-compute for:**
- Daily HHI by category (enables trend analysis without recalculation)
- Weekly HHI by category

**Compute on-the-fly for:**
- Monthly and quarterly HHI (use daily aggregates as input, which is fast)
- Custom time periods (rolling 90-day HHI)

**What HHI signals:**
- HHI < 1500: Unconcentrated (competitive market)
- HHI 1500-2500: Moderately concentrated
- HHI > 2500: Highly concentrated

**Other concentration metrics to support:**

1. **CR3 (Concentration Ratio top 3)**: Sum of top 3 brands' market share. Analysts use this for "are the top 3 players gaining share?"
2. **Share of top brand**: Simple but frequently requested
3. **Share shift metrics**: Year-over-year share change per brand (pre-computed for common periods)

**Do NOT pre-compute:**
- Multi-dimensional HHI (brand × geography × generation). The combinations explode and most queries will be ad-hoc. Build efficient on-the-fly computation using pre-computed daily aggregates as inputs.

---

### Question 3: Category Taxonomy Standards

> Are there industry-standard category groupings beyond MCC codes that analysts expect (e.g., "discretionary" vs. "non-discretionary" classifications, "consumer staples" vs. "consumer cyclicals")?

**Answer: Yes. Implement a two-level taxonomy: (1) spending category (50-60 categories via MCC groups), and (2) spending style classification (discretionary vs. non-discretionary / consumer staples vs. consumer cyclicals).**

**Reasoning:**

Analysts filter and group by both specific categories AND macro classifications. For example:

1. **Macro classification queries:**
   - "Show me discretionary spending trends" (filters to luxury, entertainment, dining out — excludes groceries, utilities)
   - "How is consumer staples spending holding up?" (often a defensive signal in uncertain economies)
   - "Is the mix shifting from cyclicals to staples?" (indicates consumer stress)

2. **Standard classification framework:**

| Style Classification | Typical Categories |
|---------------------|-------------------|
| **Consumer Staples** | Groceries, Utilities, Healthcare, Personal Care, Household Basics |
| **Consumer Discretionary** | Apparel, Dining Out, Entertainment, Travel, Home Improvement, Electronics |
| **Financial Services** | Credit Card Spend (category agnostic), Insurance |
| **Transportation** | Gas, Auto Parts, Ride-share, Parking |

**Implementation requirement:** Each merchant category in the taxonomy should have a `style_classification` attribute. This enables queries like "discretionary vs. staples" without enumerating 20 categories each time.

**Beyond MCC groups:** The standard GfK / Nielsen / IRI category groupings used in consumer research are close enough to MCC groups that a mapping is feasible. Avoid creating custom taxonomy that doesn't map to industry-standard groupings — analysts will need to reconcile with external data.

---

### Question 4: Historical Time Period for Trend Analysis

> What time periods or historical events should the synthetic data span to enable meaningful trend analysis (e.g., pre-COVID, COVID, post-COVID periods)?

**Answer: Minimum 3 years (2022-2024 or 2023-2025) to capture normal seasonal patterns. Ideally span 2019-2025 to include pre-COVID baseline, COVID disruption period, and post-COVID normalization.**

**Reasoning:**

For analysts to trust trend analysis, they need:

1. **Baseline comparison period**: "Brand X grew 10% this year" is meaningless without context. Is 10% growth above or below category growth? Is it accelerating or decelerating? You need at least 2 years of history to compute year-over-year comparisons.

2. **Seasonal pattern visibility**: Retail categories have pronounced Q4 spikes. One year of data doesn't show whether a Q4 spike is normal or exceptional. Minimum 2 years, ideally 3+ years to see multi-year seasonal averages.

3. **Event period coverage (if possible):**

| Period | Why It Matters |
|--------|----------------|
| Pre-COVID (2019) | Baseline for "normalized" growth; COVID-era comparisons |
| COVID Peak (Apr-May 2020) | Massive channel shift to e-commerce; essential vs. discretionary divergence |
| Reopening (H2 2020 - H1 2021) | Pent-up demand, stimulus-driven spending |
| Post-COVID Normalization (2022-2023) | Return to historical patterns; inflation impacts |
| Recent (2024-2025) | Current trend extrapolation |

**Minimum viable for Phase 1:** 2 years (e.g., 2023-2024) with Q4 data that shows realistic holiday spike. This enables YoY comparison for one holiday cycle.

**Ideal for credible demo:** 3 years including one full pre-COVID year. This allows analysts to say "this year's Q4 is up X% vs. the same period in 2019" — a very common comparison frame.

**Note**: If 2019 data is not feasible for synthetic generation, at minimum include 2020-like patterns (COVID-style channel shift to online) even if dated 2023, to demonstrate the system's ability to surface unusual events.

---

## From Consumer Spending SME (consumer-spending-sme)

### Question 1: Benchmark Data for External Validation

> Should synthetic data include externally benchmarkable metrics (e.g., category spending as % of disposable income) that mirror real market research?

**Answer: Yes, include benchmark ratios that allow analysts to validate synthetic data against known real-world metrics.**

**Reasoning:**

A key concern when analysts evaluate a new data source is "is this data real?" Including externally benchmarkable metrics allows analysts to perform sanity checks:

1. **Examples of benchmarkable metrics:**
   - Grocery spending as % of total spend (~20-25% for typical household)
   - Dining out as % of total spend (~10-15%)
   - Healthcare as % of total spend (~5-8%)
   - E-commerce share of retail (~20-25% in 2024)
   - Holiday Q4 retail spike (+25-35% vs. Q3 average)

2. **Why this matters:** If an analyst knows that groceries typically represent ~22% of consumer spending and the synthetic data shows 40%, the data appears fake. If it shows 21-23%, the analyst gains confidence that the dataset is credible.

3. **Implementation approach:** Include a "data validation suite" — pre-computed ratios that can be surfaced in the observability panel when analysts express skepticism. Show "Grocery share of total spend: 22.3% (historical benchmark: 20-25%)."

4. **Caution**: Do not make these benchmarks exact — embed realistic variance so they don't look generated. Real consumer data varies significantly by demographic and economic conditions.

---

### Question 2: Category Taxonomy Detail

> Is the current essential/premium category split sufficient, or do you require a more detailed 2-3 level category hierarchy for meaningful analysis?

**Answer: Essential/premium is insufficient. Implement a 3-level hierarchy: (1) style classification, (2) spending category, (3) merchant group.**

**Reasoning:**

"Essential vs. premium" is binary and lossy. Consider:

- "Dental care" is essential but not premium
- "Pet food" is essential but not premium
- "Premium pet food" is premium within essential
- "Gym membership" is discretionary but has essential/health characteristics

The system needs:

| Level | Example | Count |
|-------|---------|-------|
| **Style** | Discretionary, Staples, Services | 3-5 |
| **Category** | Restaurants, Grocery, Apparel, Travel | 50-60 |
| **Merchant Group** | Fast Food, Casual Dining, Supermarket, Department Store | 200-400 |

**Queries this enables:**
- "Show me staples categories" (style level)
- "How is restaurant spending trending?" (category level)
- "Fast food vs. casual dining share shift" (merchant group within category)
- "Which discretionary categories are growing?" (filtered style + trending category)

Without the merchant group level, analysts cannot distinguish between "Chipotle" and "a local burrito joint" — both would map to the same fast food category. This loses competitive differentiation.

---

### Question 3: Competitive Brand Positioning

> Should synthetic brand data intentionally include known competitive positioning (e.g., Brand X is known for value, Brand Y for premium)?

**Answer: Yes. Brand positioning is fundamental to competitive analysis. Include tier classification (luxury, premium, mid-market, value) and known brand archetypes.**

**Reasoning:**

When analysts look at cross-shopping or competitive analysis, they are asking "who competes with whom, and why?" Brand positioning answers the "why":

1. **Value brands** (e.g., Walmart, Dollar General, McDonald's value menu): Compete on price, attract lower-income shoppers
2. **Mid-market** (Target, Wendy's, Taco Bell): Balance of price and quality, broadest demographic reach
3. **Premium** (Whole Foods, Chipotle, Nike): Higher price points, younger/higher-income skew
4. **Luxury** (Apple Store, high-end department stores): Price-insensitive customers, small share but high value

**Required brand attributes for competitive analysis:**
- **Tier**: luxury, premium, mid-market, value
- **Category archetype**: fast casual, discount retailer, department store, subscription, etc.
- **Price positioning**: low, mid, high (within category)

**What this enables:**
- "Are customers trading down from premium to mid-market?" (cross-shopping trend analysis)
- "Which brands are gaining share in the mid-market segment?" (competitive intensity)
- "Is Brand X's customer demographic shifting?" (position maintenance)

**Implementation caution**: Use recognizable brand archetypes rather than copying real brand names exactly (liability concern). Instead of "Walmart," use "MartMart" with "discount big-box retailer" as its description. The competitive dynamics will be realistic even if the names are synthetic.

---

### Question 4: Pre-Computed Market Research Metrics

> Are there standard market research metrics (wallet share, category penetration, repurchase rate) that should be pre-computed as continuous aggregates?

**Answer: Yes. Pre-compute the following metrics as continuous aggregates: wallet share by brand/category, category penetration rate, and 30-day repurchase rate.**

**Reasoning:**

**Must pre-compute (frequently used, computationally expensive):**

| Metric | Definition | Update Frequency |
|--------|------------|------------------|
| **Wallet share** | Brand's share of total customer spending in category | Weekly aggregate |
| **Category penetration** | % of customers in panel who purchased in category | Weekly aggregate |
| **Repurchase rate** | % of customers who repurchased brand within 30/60/90 days | Weekly aggregate |

**Why weekly, not daily:** These metrics require customer-level aggregation. Computing daily is overkill — customer behavior doesn't change meaningfully day-to-day. Weekly aggregates balance freshness with computational cost.

**Do NOT pre-compute (ad-hoc, use on-the-fly from aggregates):**
- Cohort retention curves (requires specific cohort definition per query)
- Cross-shopping matrix at fine-grained brand pairs (too many combinations)
- Customer lifetime value estimates (requires assumptions best made per analysis)

**Metric definitions for consistency:**

1. **Wallet share**: `brand_spend / total_category_spend` per customer, then average across customers. Range: 0-100%.
2. **Category penetration**: `unique_customers_who_purchased_category / total_panel_customers`. Range: 0-100%.
3. **Repurchase rate**: `customers_with_2+_purchases_in_30_days / customers_with_1_purchase`. Range: 0-100%.

**Output format for pre-computed aggregates:**
```sql
wallet_share_weekly (
  week_end_date,
  brand,
  category,
  avg_wallet_share,
  median_wallet_share,
  customer_count  -- for sample size confidence
)
```

---

## Summary

The Market Analyst perspective prioritizes:

1. **Context window**: 6-8 turns with explicit session anchoring for follow-up drill-downs
2. **Confidence signaling**: Tier-based (high/moderate/low), not raw percentages
3. **Low confidence behavior**: Always HITL clarification, never best-guess
4. **Time periods**: Calendar quarter canonical; rolling windows as explicit opt-in
5. **Competitive metrics**: Pre-compute daily/weekly HHI; compute monthly on-the-fly
6. **Category taxonomy**: 3-level hierarchy (style → category → merchant group)
7. **Historical depth**: Minimum 2-3 years; include COVID-like patterns if possible
8. **Benchmark data**: Include externally validatable ratios for analyst trust
9. **Brand positioning**: Tier + archetype attributes enable competitive analysis
10. **Pre-computed metrics**: Wallet share, penetration, repurchase rate at weekly granularity

These requirements reflect how analysts actually work: drill-down sequences, YoY comparisons, competitive positioning, and external validation against known market baselines.
