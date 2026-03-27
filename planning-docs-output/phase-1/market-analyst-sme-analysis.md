# Market Analyst SME Analysis: Proteus Requirements

## Overview

This analysis addresses the `[SME:MarketAnalyst]` questions in the HLRD from the perspective of an analyst or investor who uses consumer transaction data to inform investment decisions, competitive analysis, and market research. I have experience on both the buy-side (hedge funds, asset managers) and sell-side (equity research).

---

## Question 1: Most Common and Highest-Value Queries

### Most Common Query Patterns

Based on real-world analyst and investor workflows, the following query types represent the highest frequency and value:

#### 1. **Market Share Queries** (Highest Priority)
- "What is Brand X's market share in [category] for [quarter/year]?"
- "How has Brand X's share trended over the past 2 years?"
- "Brand X vs. Brand Y market share comparison"
- "Market share by channel (e-commerce vs. brick-and-mortar)"

**Why high-value**: Market share is the primary metric for investment thesis validation. Shifts of 100-200 basis points are meaningful.

#### 2. **Same-Store Sales (SSS) / Transaction Volume Trends**
- "What is the year-over-year growth for Brand X?"
- "How did Brand X perform during [holiday season / event] compared to prior year?"
- "Transaction count trends by region"

**Why high-value**: SSS is the core operational metric for retail and restaurant investments.

#### 3. **Cross-Shopping / Customer Overlap Analysis**
- "What other brands do customers who shop at Brand X also purchase from?"
- "Share of wallet: What percentage of spending at [brand] goes to [competitor]?"
- "Customer acquisition: Where are Brand X's new customers coming from?"

**Why high-value**: Identifies competitive threats and partnership opportunities.

#### 4. **Demographic Profiling**
- "What is the age/income distribution of Brand X's customers?"
- "Geographic breakdown of Brand X's customer base"
- "Generational spending patterns (Gen Z vs. Millennial vs. Gen X)"

**Why high-value**: Critical for growth thesis and target market understanding.

#### 5. **Competitive Benchmarking**
- "How is Brand X performing relative to the category average?"
- "Brand X vs. [top 3 competitors] on key metrics"
- "Category growth rate vs. Brand X growth rate"

**Why high-value**: Contextualizes individual brand performance within industry dynamics.

### Tool Prioritization Recommendation

| Priority | Tool Category | Query Volume | Business Impact |
|----------|---------------|--------------|-----------------|
| P0 (Must Have) | Market Share Analysis | Very High | Critical |
| P0 (Must Have) | YoY Trend Analysis | Very High | Critical |
| P0 (Must Have) | Competitive Comparison | High | Critical |
| P1 (High) | Cross-Shopping Analysis | High | High |
| P1 (High) | Customer Demographics | Medium-High | High |
| P2 (Medium) | Geographic Expansion | Medium | Medium |
| P2 (Medium) | Seasonal/Event Analysis | Medium | Medium |
| P3 (Lower) | Cohort Migration | Low-Medium | Medium |
| P3 (Lower) | Wallet Share Depth | Low | Medium |

### What Distinguishes "Useful Insight" from Raw Data

**Raw Data Characteristics:**
- Numbers without context ("Brand X had $50M in sales")
- No comparison point ("Sales increased 15%")
- No indication of significance ("Traffic down 5%")

**Useful Insight Characteristics:**
1. **Contextualized**: "Brand X's 15% growth outpaced category growth of 8%, indicating share gains"
2. **Comparative**: "Brand X gained 200bps of share from Brand Y in Q3, the largest quarterly shift in 2 years"
3. **Action-oriented**: "The shift in Brand X's customer age mix toward Gen Z suggests potential for premium pricing power"
4. **Anomalous**: "This quarter breaks a 6-quarter trend of declining foot traffic, warrants investigation"
5. **Predictive signal**: "Cross-shopping data suggests Brand X customers are trading down, consistent with early warning from credit card data"

**Implication for Tool Design**: The system should surface contextualized insights, not just raw metrics. Consider a "Key Insight" summary layer that interprets results for the user.

---

## Question 2: Presentation Formats and Standard Report Layouts

### Expected Presentation Formats

#### For Market Share Reports:
```
| Brand      | Q3 2024 Share | Q3 2023 Share | YoY Change | vs. Category Growth |
|------------|---------------|---------------|------------|---------------------|
| Brand X    | 18.2%         | 17.1%         | +110 bps   | Outperforming       |
| Brand Y    | 14.8%         | 15.3%         | -50 bps    | Underperforming     |
| Brand Z    | 12.1%         | 11.8%         | +30 bps    | In-line             |
```

**Expected Visualization**: Stacked bar chart or grouped bar chart showing share over time. Market share pie charts are common but less useful for trend analysis.

#### For Cross-Shopping Reports:
```
| Brand X Customers Also Shop At | % Overlap | Avg. Basket Size |
|--------------------------------|-----------|-----------------|
| Brand Y                        | 34%       | $45             |
| Brand Z                        | 22%       | $32             |
| Brand W                        | 18%       | $28             |
```

**Expected Visualization**: Venn diagram or heat map for overlap; bar chart for share percentages.

#### For Competitive Benchmarks:
```
| Metric          | Brand X | Top Competitor Avg | Category Avg |
|-----------------|---------|---------------------|--------------|
| Avg Transaction | $42     | $38                 | $35          |
| Frequency/Mo    | 2.3x    | 2.1x                | 1.8x         |
| Retention Rate  | 67%     | 61%                 | 55%          |
```

**Expected Visualization**: Radar chart for multi-metric comparison; grouped bar charts for individual metrics.

#### For Trend Analysis (Time-Series):
```
| Quarter   | Brand X Sales | Category Sales | Brand X Share |
|-----------|---------------|----------------|---------------|
| Q1 2023   | $120M         | $700M          | 17.1%         |
| Q2 2023   | $135M         | $750M          | 18.0%         |
| ...       | ...           | ...            | ...           |
```

**Expected Visualization**: Dual-axis line chart (absolute values + share) or index chart (base=100) for normalized comparison.

### Standard Report Layout Expectations

1. **Header**: Clear title, time period, brands/categories covered
2. **Summary Box**: Top 3 key findings in bullet points (analysts are busy)
3. **Primary Visualization**: Largest section, interactive
4. **Data Table**: Toggle-able, allows sorting and export
5. **Contextual Notes**: Sample size, data freshness, methodology caveats

### Visualization Type Recommendations

| Query Type | Recommended Chart Types |
|------------|-------------------------|
| Market share comparison | Grouped bar, stacked bar, treemap |
| Trend over time | Line chart, area chart |
| Competitive positioning | Radar chart, bullet chart |
| Customer overlap | Venn diagram, heatmap, Sankey |
| Geographic distribution | Choropleth map |
| Demographic breakdown | Stacked bar, donut chart |
| Correlation analysis | Scatter plot, bubble chart |

### Presentation Format Requirements

- **Hover tooltips**: Essential — show exact values, time periods, sample sizes
- **Legend toggling**: Critical for multi-series charts (analysts often want to hide/show specific brands)
- **Zoom/pan**: Important for time-series with 8+ quarters
- **Export capability**: CSV export is expected; PNG/SVG export is nice-to-have
- **Table view**: Analysts need the raw data alongside visualizations

---

## Question 3: Synthetic Data Layer — Demonstrable Tools

### Realistic Tool Count for Synthetic Data

**Honest Assessment**: With 10M+ transactions, 100+ brands, 2+ years of data, you can meaningfully demonstrate approximately **15-25 distinct analytical tools/capabilities**. Attempting more creates "feature bloat" where no single capability is demonstrated well.

### Recommended Minimum Viable Tool Set (Must Have)

#### Core Analysis Tools (8-10):
1. **Market Share Query** — Share by brand, category, time period, geography
2. **YoY Growth Calculator** — Transaction volume and spend growth
3. **Competitive Pair Comparison** — Direct Brand X vs. Brand Y analysis
4. **Category Benchmark** — Brand performance vs. category average
5. **Cross-Shopping Matrix** — Customer overlap between brands
6. **Demographic Breakdown** — Age, income, gender distribution by brand
7. **Geographic Heat Map** — Regional performance comparison
8. **Seasonal/Event Analysis** — Holiday performance, Prime Day, Black Friday
9. **Trend Line Chart** — Time-series visualization with drill-down
10. **Top/Bottom Rankings** — Brand rankings by various metrics

#### Advanced Tools (5-7, if time permits):
11. **Wallet Share Analysis** — Share of customer spending within category
12. **Customer Cohort Retention** — Retention curves by acquisition quarter
13. **Generational Trend Analysis** — Gen Z/Millennial/Gen X comparative trends
14. **Price Sensitivity Analysis** — Average basket size trends
15. **Customer Lifetime Value Proxy** — Frequency × Basket analysis

### What NOT to Build (Edge Cases with Low ROI)

- Deep learning-based prediction models (analysts don't trust black boxes)
- Natural language generation of reports (hallucination risk is unacceptable)
- Social media sentiment integration (different data source, different use case)
- Real-time data streaming (batch synthetic data is fine)

### Architectural Concern

The "10-50 tools" range in the HLRD seems overly ambitious for v1. I recommend:
- **v1 Target**: 12-15 core tools that cover 90% of analyst queries
- **Future**: Expand based on user feedback and usage analytics

---

## Question 4: Eval Framework — Representative Example Queries

### Complexity Level 1: Simple Factual Queries

These should be answered with high accuracy (>95%):

| Query | Expected Tool | Key Dimensions |
|-------|--------------|----------------|
| "What is Walmart's market share in grocery?" | Market Share | Brand, Category, Time |
| "How much did Target grow last quarter?" | YoY Growth | Brand, Time |
| "Show me Chipotle's sales by region" | Geographic Analysis | Brand, Geography, Time |
| "What is the average basket size at Home Depot?" | Basket Analysis | Brand, Time |

### Complexity Level 2: Comparative Queries

These require understanding comparative intent (>90% accuracy target):

| Query | Expected Tool | Key Dimensions |
|-------|--------------|----------------|
| "How is McDonald's doing vs. Burger King?" | Competitive Comparison | Brand X, Brand Y, Time |
| "Which fast food chain has the highest growth?" | Rankings | Category, Metric, Time |
| "Is Starbucks gaining or losing share?" | Market Share Trend | Brand, Category, Time |
| "Show me the top 5 automotive brands by sales" | Rankings | Category, Time |

### Complexity Level 3: Contextual/Analytical Queries

These require inference and context (>85% accuracy target):

| Query | Expected Tool | Key Dimensions |
|-------|--------------|----------------|
| "Why did Brand X's sales spike in March?" | Event Analysis | Brand, Time, Event Detection |
| "Are Brand X's customers trading up or down?" | Cross-Shopping + Trend | Brand, Time, Basket Analysis |
| "Which brands are taking share from each other?" | Share Shift Analysis | Category, Time, Brand Movement |
| "What's the demographic profile of new Nike customers?" | Customer Demographics | Brand, Customer Acquisition, Demographics |

### Common Phrasing Variations (Synonyms)

The system must recognize these as the same underlying query:

| Concept | Alternative Phrasings |
|---------|----------------------|
| Market Share | "share of market", "market position", "competitive position", "% of category", "how is Brand X doing" |
| YoY Growth | "year over year", "vs last year", "grew X%", "changed from last year" |
| Competitive Comparison | "Brand X vs Brand Y", "Brand X compared to", "against Brand Y", "how does Brand X stack up" |
| Cross-Shopping | "overlap", "customer overlap", "who else do they shop", "customers also buy from" |
| Wallet Share | "share of wallet", "spending share", "portion of their spend" |
| Demographics | "age breakdown", "customer profile", "who are their customers", "generational" |

### Edge Cases and Ambiguity Examples

**Ambiguous Queries (Should trigger clarification)**:
- "How is Nike doing?" (Which Nike? What metric? What time period?)
- "Show me the trends" (Which brands? What trends? What time horizon?)
- "Who's winning?" (Winning what? Market share? Growth? Customers?)

**Under-specified Queries (System should make reasonable defaults)**:
- "Brand X vs. Brand Y" → Assume market share comparison, last completed quarter
- "Show me the data" → Default to time-series chart with all available dimensions

### Eval Query Suite Recommendation

Include at minimum:
- **50 queries** across complexity levels 1-3
- **20+ brands** represented
- **10+ categories** covered
- **5+ time periods** (quarterly, annual, event-based)
- **Synonym variations** for key concepts (market share = 5+ phrasings)

---

## Questions for Other SMEs

### For ConsumerSpending SME:

1. **Seasonal Patterns**: What seasonal spending patterns are realistic for synthetic data? Are there specific holidays/events (Prime Day, Black Friday, Super Bowl) that should show distinct spikes? What magnitude of spike is realistic (10%? 50%? 200%?)?

2. **Generational Differences**: What are realistic generational spending patterns? Gen Z tends to prefer X brands, Millennials Y, Boomers Z — what spending ratios are realistic?

3. **Geographic Variation**: What geographic spending patterns exist? Urban vs. suburban vs. rural? Regional preferences (Southwest vs. Northeast)?

4. **Cross-Shopping Rigor**: What is a realistic cross-shopping overlap percentage between major brands? Is 30% overlap between two brands reasonable?

### For DataScientist SME:

1. **Aggregation Level**: What aggregation level is appropriate for synthetic transactions? Daily? Weekly? Monthly? This affects what time-series analysis is meaningful.

2. **Statistical Rigor**: What statistical distributions should the synthetic data follow? Normal? Power law? Zipfian? This affects how realistic trend analysis will feel.

3. **Anomaly Injection**: Should the eval framework include known anomalies that the system should detect? If so, what types (seasonal, one-time events, secular trends)?

4. **Metric Definitions**: How should "market share" be calculated — by transaction count, by spend, by unique customers? All three give different results.

### For IntegrationEngineer SME:

1. **Query Latency**: With 10M+ rows, what are realistic query latency expectations? Can true interactive speeds (<5s) be achieved with proper indexing, or is caching required?

2. **Tool Selection Scale**: Is RAG + LLM selection tractable for 10-50 tools with 30+ dimensions each? What embedding approach is recommended?

3. **Data Refresh**: How should the synthetic data layer handle "time travel" queries (e.g., "what did the data show as of Q1 2024")?

### For UXDesigner SME:

1. **Chart Interactions**: What ECharts interaction patterns are most valuable? Should I prioritize hover tooltips and legend toggling, or are there more advanced interactions (brush select, data zoom) that analysts actually use?

2. **Clarification UX**: How should ambiguous query clarifications be presented? Modal dialog? Inline suggestion? Chat follow-up?

3. **Report Export**: What export formats do analysts actually use? CSV for data, PNG for charts, or PDF for full reports?

4. **Dashboard Layout**: Should this feel more like a Bloomberg terminal (dense, keyboard-driven) or a modern SaaS tool (cleaner, mouse-driven)? This affects information density decisions.

### For AIWorkflow SME:

1. **Multi-Turn Context**: How many conversation turns should the system maintain for context? Analysts often ask follow-up questions ("drill into Brand X", "now compare to Brand Y").

2. **Confidence Signaling**: Should the system indicate confidence in its tool selection? Analysts would value knowing "I'm 72% confident this is a market share query."

3. **Fallback Behavior**: When tool selection confidence is low, what should happen? Ask for clarification? Return multiple interpretations? Make a best guess?

---

## Assumptions and Risks

### Assumptions

1. **Query Complexity Distribution**: I assume 70% of queries will be Level 1-2 complexity, 30% Level 3. If this distribution is wrong, tool prioritization may be misaligned.

2. **Synthetic Data Quality**: The value of this system depends heavily on synthetic data realism. If patterns feel artificial, analysts will dismiss the tool.

3. **Brand Coverage**: 100+ brands is appropriate. I assume a mix of large-caps (Walmart, Amazon), mid-caps (Target, Best Buy), and small-caps to provide competitive tension.

4. **Time Horizon**: 2+ years of data is sufficient for meaningful trend analysis. 4-5 years would be better but may not be feasible for synthetic generation.

### Risks

1. **Feature Overload**: The 10-50 tool range is too broad. If we build 50 tools, none will be polished. Recommend narrowing to 12-15 core tools.

2. **Insight vs. Data Gap**: If the system only returns raw numbers without context, analysts will find it useless. A contextualization layer is essential.

3. **Eval Framework Over-Optimization**: An eval framework measuring tool selection accuracy may lead to "gaming" rather than genuine utility. Consider user satisfaction metrics as well.

4. **Ambiguity Handling**: Analysts phrased queries many ways. If the system can't handle "How's Nike doing?" as equivalent to "What is Nike's market share?", adoption will suffer.

5. **Latency Expectations**: 5-second query-to-visualization is aggressive for 10M+ rows. Caching and pre-aggregation strategies are critical.

---

## Summary

From the Market Analyst perspective, this is a promising concept with high utility potential IF:
1. The synthetic data feels realistic and covers the right brands/categories/time periods
2. Visualization output matches standard analyst report formats
3. Tool selection prioritizes market share, competitive comparison, and trend analysis
4. The system handles common query phrasings (synonyms) gracefully
5. Query latency stays under 5 seconds through intelligent caching

The biggest risk is over-building (50 tools) rather than doing 15 tools exceptionally well.
