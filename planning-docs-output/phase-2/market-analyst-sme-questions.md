# Cross-SME Questions for Market Analyst SME (market-analyst-sme)

## From AI/NLP SME (ai-nlp-sme)

**Context:** The AI/NLP SME is designing the eval framework and multi-turn conversation system. They need market analyst expertise on context windows, confidence signaling, and fallback behavior.

1. **Multi-Turn Context Window:**
   How many conversation turns should the system maintain for context? Analysts often ask follow-up questions ("drill into Brand X", "now compare to Brand Y").

2. **Confidence Signaling:**
   Should the system indicate confidence in its tool selection? Analysts would value knowing "I'm 72% confident this is a market share query."

3. **Fallback Behavior for Low Confidence:**
   When tool selection confidence is low, what should happen? Ask for clarification? Return multiple interpretations? Make a best guess?

---

## From Integration Engineer SME (integration-engineer-sme)

**Context:** The Integration Engineer is designing the API and query performance. They need market analyst input on time period definitions and competitive metrics.

1. **Canonical Time Period Definitions:**
   "Last quarter" might mean:
   - Calendar quarter (Q1 = Jan-Mar, Q2 = Apr-Jun, etc.)
   - Rolling quarter (prior 90 days)
   - Most recently completed 13-week period

   The API needs a single source of truth for period normalization, and this affects how dimension extraction normalizes relative dates. What definition should the system use?

2. **Competitive Metrics (HHI, Concentration Ratios):**
   What specific competitive metrics (HHI, concentration ratios) are analysts most commonly requesting? Should these be pre-calculated in the synthetic data or computed on-the-fly?

3. **Category Taxonomy Standards:**
   Are there industry-standard category groupings beyond MCC codes that analysts expect (e.g., "discretionary" vs. "non-discretionary" classifications, "consumer staples" vs. "consumer cyclicals")?

4. **Historical Time Period for Trend Analysis:**
   What time periods or historical events should the synthetic data span to enable meaningful trend analysis (e.g., pre-COVID, COVID, post-COVID periods)?

---

## From Consumer Spending SME (consumer-spending-sme)

**Context:** The Consumer Spending SME is modeling synthetic data patterns. They need market analyst input on benchmark data and category hierarchy.

1. **Benchmark Data for External Validation:**
   Should synthetic data include externally benchmarkable metrics (e.g., category spending as % of disposable income) that mirror real market research?

2. **Category Taxonomy Detail:**
   Is the current essential/premium category split sufficient, or do you require a more detailed 2-3 level category hierarchy for meaningful analysis?

3. **Competitive Brand Positioning:**
   Should synthetic brand data intentionally include known competitive positioning (e.g., Brand X is known for value, Brand Y for premium)?

4. **Pre-Computed Market Research Metrics:**
   Are there standard market research metrics (wallet share, category penetration, repurchase rate) that should be pre-computed as continuous aggregates?
