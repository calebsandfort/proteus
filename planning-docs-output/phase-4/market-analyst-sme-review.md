# Market Analyst SME Review: Requirements Draft

**Review Date:** 2026-03-27
**SME Domain:** Market Analysis, Competitive Research, Industry Trends, Strategic Planning
**Relevant FRs:** FR-2 (Tool Selection), FR-5 (Visualization), FR-7 (Eval Framework)

---

## Gaps Found

### Gap 1: Missing Core Analytical Tools

**FR-2.2 Core Tool Set** lists 8 P0 tools, but several high-value analyst queries are not covered:

| Missing Tool | Why Analysts Need It | Example Query |
|--------------|---------------------|---------------|
| **Same-Store Sales** | Cornerstone metric for retail/ restaurant analysis; separates organic growth from new unit contributions | "What was Chipotle's same-store sales growth in Q3 2024?" |
| **Wallet Share Analysis** | Critical for understanding customer loyalty and cross-brand potential | "What share of Starbucks customers' dining budget goes to Starbucks?" |
| **Customer Retention/Churn** | Essential for subscription and retail brand health | "What % of Target's customers from 2023 returned in 2024?" |
| **Promotional Sensitivity** | Key for understanding price elasticity and promotional ROI | "How did Target's sales respond to Amazon Prime Day?" |

**Recommendation:** Add same-store sales and wallet share as P0 tools. Customer retention can remain P1 but should not be omitted entirely.

### Gap 2: Cross-Shopping Overlap Metrics Are Insufficiently Specified

**FR-2.2 #5 (cross_shopping_overlap)** is marked P1 and listed as "multi-brand purchasing patterns and customer overlap." However, analysts need multiple distinct metrics:

- **Jaccard similarity** (set intersection/union)
- **Customer overlap %** (what % of Brand A's customers also shop at Brand B)
- **Cross-purchase spend** (share of wallet spent on secondary brands)
- **Competitive intensity index**

A single tool cannot adequately serve all these use cases without confusing output schemas.

**Recommendation:** Split into two tools: `customer_overlap` (binary: shopped both) and `wallet_share_cross_purchase` (spend-based). Or define a richer output schema with multiple metrics.

### Gap 3: Visualization Missing Key Chart Types

**FR-5.1 Auto Chart-Type Selection** covers the basics but omits chart types that are standard in equity research and competitive analysis:

| Missing Chart | Use Case | Example Query |
|--------------|----------|---------------|
| **Waterfall chart** | Decomposing sales change into volume/mix/price contributions | "Show me what drove Target's Q2 sales change: new stores vs. existing store growth" |
| **Bump chart** | Tracking ranking changes over time | "Show how Starbucks' ranking among coffee shops changed over the past 8 quarters" |
| **Area chart** | Showing market share trends with fill | "Show Chipotle vs. Qdoba market share over time" |
| **Clustered bar with trendline** | Comparing brands while showing underlying trend | "Compare McDonald's and Wendy's traffic trends over 2 years" |

**Recommendation:** Add waterfall and bump charts to the chart type selection matrix in FR-5.1.

### Gap 4: KPI Card Missing Year-over-Year Comparison

**FR-5.3 KPI Card Display** specifies "comparison to prior period, comparison to category average" but does not explicitly require **YoY comparison**. Earnings season analysis almost universally requires YoY comparisons:

> "The KPI card SHALL display: metric name, primary value, comparison to prior period, comparison to category average, **and year-over-year change %**"

### Gap 5: Dimension Extraction Missing Day-of-Week and Time-of-Day

**FR-3.1 Dimension Categories** covers 9 dimension types but omits temporal dimensions that are frequently analyzed:

- **day_of_week** (Monday-Sunday) — Weekend vs. weekday patterns are fundamental
- **hour_of_day** — Peak shopping hours matter for retail traffic analysis
- **recency** — Used for cohort analysis ("customers acquired in the last 90 days")

These are not exotic edge cases; they are standard segmentation dimensions.

**Recommendation:** Add day_of_week and hour_of_day to FR-3.1 dimension categories.

### Gap 6: Eval Benchmark Queries Do Not Cover High-Value Analyst Scenarios

**FR-7.6 Benchmark Queries** provides only 6 examples total across 3 levels. Key missing scenarios:

**Multi-dimensional competitive queries:**
- "Compare Starbucks' market share in Austin vs. Portland over the past 4 quarters"
- "Show me McDonald's YoY growth by generation for the past 2 years"

**Cross-shopping/wallet share queries:**
- "What % of Chipotle customers also ordered from DoorDash in the same month?"
- "How much of Target's customers' wallet goes to Amazon?"

**Same-store sales queries:**
- "What was Wendy's same-store sales growth in Q4 2024?"

**Causal/diagnostic queries:**
- "Did Prime Day hurt Target's in-store traffic in July?"

### Gap 7: Visualization Selection Not Evaluated

**FR-7 (Eval Framework)** measures tool selection accuracy, dimension extraction accuracy, and end-to-end correctness, but does not evaluate whether the **correct visualization was selected**. If a query asking for "market share trend" returns a bar chart instead of a line chart, the current eval would not catch this.

**Recommendation:** Add a visualization_selection_accuracy metric to FR-7.2.

---

## Conflicts Identified

### Conflict 1: Aggregation Level Rules Are Inconsistent

**FR-3.3 Time Range Parsing Rules** specifies:
- 15-90 days → weekly
- 91-365 days → monthly

**FR-4.4 Aggregation Level Handling** (API layer) specifies:
- 1-7 days → daily
- **8-90 days → daily** (contradicts FR-3.3)
- 91-365 days → weekly (contradicts FR-3.3)
- 1+ years → monthly (contradicts FR-3.3)

These two specifications are in direct conflict. The FR-3.3 spec would show more granular data for medium-length queries.

**Resolution needed:** Decide whether dimension extraction or API layer governs aggregation defaults. Recommend FR-3.3 logic (more granular) since it is closer to user intent.

### Conflict 2: Evaluation Criteria vs. Presentation Requirements

**FR-7.2** sets targets of:
- Tool selection accuracy: 90%
- Dimension extraction accuracy: 85%
- End-to-end result correctness: 80%

But **FR-5.7 Result Set Handling** says:
- 1,001-10,000 rows: "Aggregated view suggested; raw data on demand"
- 10,000+ rows: "Auto-aggregate with 'View raw data' option"

If a large result set is auto-aggregated by the system without user request, the "end-to-end result correctness" eval becomes ambiguous — did the system correctly answer the query, or did it silently change the answer by aggregating?

**Resolution needed:** Clarify that large result aggregation is a presentation choice, not a query modification. The eval should validate against the aggregated result, not the hypothetical raw result.

---

## Accuracy Assessment

### What Is Accurate

**FR-2.1 Tool Registry Design:** Storing tool definitions as embeddings for semantic retrieval is the correct approach. Allowing tools to be addable/modifiable/deprecated without pipeline changes reflects how analyst needs evolve.

**FR-2.3 RAG Threshold:** The 0.75 similarity threshold with 0.70 floor for HITL is reasonable. Below 0.70 should definitely trigger clarification.

**FR-2.4 Confidence Scoring:** The weighted combination (25% RAG, 35% LLM, 40% dimension match) is a reasonable starting heuristic, though it should be empirically tuned against the eval suite.

**FR-5.1 Chart Type Selection Logic:** The mapping from query patterns to chart types is accurate. "over time" + "trend" → line chart, "share/percentage" → pie chart, etc. This aligns with how analysts mentally frame their requests.

**FR-5.2 Manual Override with Explanation:** Showing a tooltip explaining auto-selection reasoning when override differs is a thoughtful feature. Analysts want to understand why the system made a choice.

**FR-5.7 Result Set Thresholds:** The tiered approach (100 rows full display, 1,000 paginated, 10,000 aggregated) is practical and realistic.

**FR-7.3 Clarification Rubric:** The 0-2 scoring is appropriate for HITL evaluation. The definitions for "correct," "partially correct," and "incorrect" are clear and actionable.

**FR-7.5 Anomaly Injection:** Including seasonal patterns, COVID-style channel shifts, and secular trends in the eval framework is excellent. This ensures the system is tested on the same patterns analysts analyze in real data.

### What Needs Correction

**FR-2.2 Tool Prioritization:** The P0/P1/P2 classification is reasonable but incomplete. The synthesis notes (lines 668-670) list additional tools but they are not in the actual FR-2.2 table. This creates confusion about what is actually required.

**FR-3.4 Synonym Handling Example:** The confidence scores (0.7 for "young people" → Gen Z, 0.8 for "credit card" → credit) seem underspecified. Gen Z vs. Millennial is a meaningful distinction with real analytical consequences. A 0.7 confidence should not allow silent resolution; it should at least be surfaced in the observability panel.

**FR-4.3 Query Guardrails:** Requiring at least one high-cardinality filter is correct, but the logic should also consider **time range** as a high-cardinality filter. A query with brand + 3 years of data can still be very large even without geography.

**FR-5.6 Chart Interactivity (Recommended):** Data zoom and click-to-highlight are listed as "recommended" but should be **required** for time-series analysis. An analyst looking at 8+ quarters of market share trends needs zoom to see detail. This is not optional.

---

## Recommended Changes

### FR-2.2 (High Priority)

Replace the Core Tool Set table with this expanded version:

**P0 (Must Have):**
1. `market_share_trend` — Brand-vs-brand market share, category-wide share breakdown, share trend over time
2. `brand_comparison` — Direct Brand X vs. Brand Y analysis (competitive positioning)
3. `yoy_growth_analysis` — Transaction volume and spend growth year-over-year
4. `same_store_sales` — Organic growth metric separating new units from existing store performance
5. `category_trends` — Category-level transaction counts and dollar volumes
6. `wallet_share` — Share of customer's total category spend per brand

**P1 (Should Have):**
7. `cross_shopping_overlap` — Multi-brand purchasing patterns and customer overlap (binary)
8. `demographic_breakdown` — Spending distribution by generation, income, age
9. `geographic_breakdown` — State/CBSA/regional spending patterns
10. `customer_retention` — Cohort retention and churn analysis

**P2 (Nice to Have):**
11. `top_n_rankings` — Brand rankings by various metrics
12. `channel_analysis` — Online vs. in-store vs. mobile breakdown
13. `basket_analysis` — Co-purchase patterns
14. `promotional_sensitivity` — Price elasticity and promotional lift analysis

### FR-3.1 (Medium Priority)

Add to Dimension Categories:
- **day_of_week**: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
- **hour_of_day**: 0-23 (with optional bucketing: morning/afternoon/evening/night)
- **recency_band**: 0-30 days, 31-60 days, 61-90 days, 90+ days

### FR-5.1 (Medium Priority)

Add to Auto Chart-Type Selection:
- "share trend over time" → **Stacked Area Chart** (shows brand share evolution with fill)
- "decomposition", "driver", "contribution" → **Waterfall Chart**
- "ranking change", "how did ranking evolve" → **Bump Chart**

### FR-5.3 (Medium Priority)

Update KPI Card specification to explicitly include YoY:
> "The KPI card SHALL display: metric name, primary value, comparison to prior period, comparison to category average, **year-over-year change %, and growth rate indicator**"

### FR-5.6 (High Priority — Change "Recommended" to "Required")

> "Charts **SHALL** support data zoom (slider) for time-series with 8+ quarters"
> "Charts **SHALL** support click-to-highlight for legend items or bars"

### FR-7.2 (Medium Priority)

Add to Eval Dimensions and Metrics:
- **Visualization selection accuracy**: % correct chart type selected — target 85%

### FR-7.6 (High Priority)

Expand benchmark queries to include:

**Level 1 additions:**
- "What is Amazon's market share in e-commerce?"
- "How much did Nike grow last year?"

**Level 2 additions:**
- "Compare Target's market share in Texas vs. California"
- "Show me Starbucks' category share trend over 4 quarters"
- "What is McDonald's customer overlap with Wendy's?"

**Level 3 additions:**
- "Why did Chipotle's sales spike in June? (hint: new product launch)"
- "Are Target customers trading up or down in Q4?"
- "Did Prime Day impact Walmart's in-store traffic?"

### FR-3.3 / FR-4.4 Conflict Resolution (Critical)

Reconcile the aggregation level logic. Recommend the following unified specification:

| Time Range | Aggregation Level |
|------------|------------------|
| 1-14 days | Daily |
| 15-90 days | Weekly |
| 91-365 days | Monthly |
| 1-2 years | Quarterly |
| 2+ years | Annual |

---

## Summary Assessment

| Category | Rating | Notes |
|----------|--------|-------|
| **Tool Coverage** | Good | Core tools present but missing same-store sales and wallet share |
| **Dimension Coverage** | Good | Missing day-of-week and time-of-day |
| **Visualization Logic** | Good | Basic coverage good, missing waterfall/bump charts |
| **Eval Coverage** | Fair | Missing visualization selection evaluation, limited benchmark queries |
| **Priority Accuracy** | Good | P0/P1/P2 distinction is appropriate |
| **Presentation Format** | Good | Chart type selection logic is accurate |
| **Cross-SME Coordination** | Fair | Aggregation conflict with API layer needs resolution |

The overall requirements are well-structured and accurately reflect analyst workflows. The most critical gaps are the missing same-store sales tool, the aggregation level conflict, and the need for YoY comparison in KPI cards. The eval framework is the weakest component due to sparse benchmark queries and missing visualization evaluation.

---

## Questions for Other SMEs

**For Consumer Spending Data SME:**
- What is the expected cardinality of the `same_store_sales` metric? Can we distinguish new stores from existing stores with the current schema, or is this derived?
- For `wallet_share`, what is the denominator — total category spend across all categories, or total spend within the brand's primary category?

**For AI/NLP SME:**
- The confidence scoring in FR-2.4 (25/35/40 weighted) — is this empirically derived or a starting heuristic? How should we validate this against the eval suite?
- For dimension synonym handling (FR-3.4), should 0.7 confidence trigger a silent resolution or should it be surfaced in the observability panel?

**For Technical Spec Agent:**
- The aggregation level conflict between FR-3.3 and FR-4.4 — which layer should be the source of truth? Does the answer depend on where the auto-selection logic lives?
