# Consumer Spending SME Review: Requirements Draft

**Review Date:** 2026-03-27
**Domain:** Consumer transaction data, spending patterns, synthetic data generation
**Focus Areas:** FR-6 (Synthetic Data Layer), FR-3 (Dimension Extraction), NFR-3 (Synthetic Data Quality)

---

## Accuracy Assessment

### What the Draft Gets Right

**FR-6.6 - Log-Normal Transaction Distributions:** The mu/sigma parameters for transaction amounts are realistic:
- Essential categories (mu=3.0, sigma=0.8) implies median ~$20, consistent with grocery staples
- Premium (mu=4.2, sigma=1.2) implies median ~$67, reasonable for luxury purchases
- Fast food (mu=2.2, sigma=0.6) implies median ~$9, accurate for quick-service

**NFR-3.2 - Income-Brand Correlation:** The requirement that high-income ($150K+) shows 70-80% premium brand transactions is accurate. In real alternative data (e.g., Facteus, Bloomberg Second Measure), this correlation is strong and visible.

**FR-6.7 - Seasonal Patterns:** Q4 holiday spike (+25-40%), back-to-school (Aug-Sep +20-35%), and weekend vs. weekday patterns are well-documented in consumer transaction data.

**NFR-3.1 - Distribution Types:** Specifying log-normal for transaction amounts, Zipfian for brand market shares, and Dirichlet for category proportions correctly reflects how real alternative data providers structure their synthetic panels.

**FR-6.4 - Category Taxonomy:** The 3-level hierarchy (Style Classification -> Spending Category -> Merchant Group) mirrors actual industry taxonomies like the MCC (Merchant Category Code) system.

---

## Conflicts Identified

### Conflict 1: Real Brand Names vs. Archetype Brands

**Location:** FR-6.5 vs. FR-7.6 (Benchmark Queries)

**Problem:** FR-6.5 states "Brand data SHALL include recognizable archetypes rather than copying real brand names exactly," but FR-7.6 benchmark queries use actual brand names:
- "What is Walmart's market share in grocery?"
- "How much did Target grow last quarter?"
- "How is McDonald's doing vs. Burger King?"
- "Is Starbucks gaining or losing share?"

**Impact:** If the synthetic data uses fictional archetypes (e.g., "MartMart" instead of "Walmart"), these benchmark queries cannot be evaluated against actual expected values. The eval suite cannot have ground truth for fictional brands.

**Resolution Required:** Either:
1. Use actual brand names in synthetic data (accepting minor fictionalization for legal safety), or
2. Revise all benchmark queries to use fictional brand names with explicit mapping tables

---

### Conflict 2: Transaction Count vs. Panel Structure

**Location:** FR-6.1 vs. FR-6.9

**Problem:** FR-6.1 requires "10M+ synthetic transactions" over 2 years. FR-6.9 specifies "100,000-500,000 panelists" with "50-200 transactions over 2 years."

**Math Check:**
- Minimum panel: 100,000 panelists x 50 transactions = 5M transactions
- Maximum panel: 500,000 panelists x 200 transactions = 100M transactions

**Issue:** The panel structure alone can produce anywhere from 5M to 100M transactions. The 10M+ requirement is achievable but not guaranteed by the panel spec. More critically, if panelists shop at only "3-10 different brands within a category" (FR-6.9), this constrains cross-category spending patterns.

**Resolution Required:** Clarify that the panel generates the 10M+ transactions, or specify the panel size needed to reliably produce 10M+ transactions.

---

### Conflict 3: E-commerce Penetration Benchmark

**Location:** NFR-3.5 (Data Validation Benchmarks)

**Problem:** The draft states "E-commerce share of retail SHALL be 20-25% in 2024."

**Actual Data:** US Census Bureau data shows e-commerce as approximately 16-17% of total retail sales in Q4 2024. The 20-25% figure may reflect a narrow "e-commerce pure-play" definition or may be aspirational rather than factual.

**Impact:** If analysts benchmark against known external data (Census Bureau, Adobe Analytics), a 20-25% e-commerce share will appear inflated compared to reality, undermining credibility.

**Resolution Required:** Either:
1. Revise to 15-18% to match Census Bureau data, or
2. Explicitly define e-commerce as a broader category (includes mobile POS, app-based purchases) and document the rationale

---

### Conflict 4: Aggregation Level Auto-Selection Mismatch

**Location:** FR-3.3 vs. FR-4.4

**Problem:** FR-3.3 (Time Range Parsing Rules) specifies:
- 15-90 days -> weekly
- 91-365 days -> monthly

FR-4.4 (API Aggregation Level Handling) specifies:
- 8-90 days -> daily
- 91-365 days -> weekly

**Impact:** A query spanning 60 days would be aggregated weekly by the dimension extractor (FR-3.3) but daily by the API (FR-4.4). The pipeline has conflicting instructions for the same input.

**Resolution Required:** Unify the auto-selection logic into a single authoritative rule set, likely in FR-3.3 (dimension extraction) with FR-4.4 referencing it.

---

## Gaps Found

### Gap 1: Missing Payment Network Dimension

**Location:** FR-3.1 (Dimension Categories)

**Gap:** The dimension list includes `card_type` (credit, debit, prepaid, corporate) but does not include `payment_network` (Visa, Mastercard, Amex, Discover).

**Why It Matters:** In real transaction data, payment network is a fundamental dimension. Network-level market share analysis is common. Brand affinity can differ significantly across networks (e.g., Amex cardholders may show different spending patterns than Visa users).

**Recommendation:** Add `payment_network: [visa, mastercard, amex, discover]` as a dimension category, or clarify that `card_type` subsumes network information.

---

### Gap 2: Missing Day-of-Week Dimension

**Location:** FR-3.1 (Dimension Categories)

**Gap:** While FR-6.7 embeds weekend/weekday patterns in the data, day-of-week is not listed as an extractable dimension.

**Why It Matters:** Queries like "Compare Saturday vs. Sunday spending for restaurants" or "Show weekday vs. weekend trends" require day-of-week as a parameter. Without it, such queries would require ad-hoc handling.

**Recommendation:** Add `day_of_week: [monday, tuesday, wednesday, thursday, friday, saturday, sunday]` to FR-3.1.

---

### Gap 3: Corporate Card Definition Ambiguity

**Location:** FR-3.1

**Gap:** `card_type` includes "corporate" but this category is ambiguous. In real transaction data:
- Corporate cards are employer-issued (not a bank product type)
- Corporate spending has distinct characteristics (higher average ticket, different category mix)
- Corporate cards may route through different payment networks

**Impact:** If "corporate" means "corporate card product," this is a valid dimension. If it means "business spending," it overlaps with merchant category analysis.

**Recommendation:** Clarify whether "corporate" refers to the card issuing bank (corporate vs. consumer) or the spending context (business vs. personal).

---

### Gap 4: Generation Birth Year Boundaries Not Specified

**Location:** FR-3.1

**Gap:** Generations are listed (Gen Z, Millennial, Gen X, Boomer, Silent) but birth year cutoffs are not defined.

**Why It Matters:** Generation definitions vary by data provider. Some use Census Bureau definitions, others use Pew Research. A 38-year-old in 2024 could be Gen X or Millennial depending on the definition.

**Recommendation:** Add explicit birth year ranges:
- Gen Z: 1997-2024
- Millennial: 1981-1996
- Gen X: 1965-1980
- Boomer: 1946-1964
- Silent: Before 1946

---

### Gap 5: Income Band Boundaries Not Specified

**Location:** FR-3.1

**Gap:** Six income bands are mentioned (<$25K to $150K+) but exact boundaries are not defined.

**Why It Matters:** Without defined brackets, different parts of the pipeline may use inconsistent boundaries. Common Census Bureau brackets differ from what alternative data providers typically use.

**Recommendation:** Specify exact brackets:
- Band 1: <$25,000
- Band 2: $25,000-$49,999
- Band 3: $50,000-$74,999
- Band 4: $75,000-$99,999
- Band 5: $100,000-$149,999
- Band 6: $150,000+

---

### Gap 6: CBSA vs. MSA Redundancy

**Location:** FR-6.3

**Gap:** Both CBSA (350-400 values) and MSA (380-400 values) are listed as hierarchical geography levels. CBSA (Core-Based Statistical Area) is the formal term that encompasses both Metropolitan and Micropolitan areas. MSA is a subset of CBSA (metropolitan only).

**Impact:** Having both creates redundancy and confusion. Most transaction data uses CBSA or MSA, not both.

**Recommendation:** Use one or the other, not both. CBSA is the more comprehensive and modern term.

---

### Gap 7: Missing Brand Hierarchy / Parent Company

**Location:** FR-6.5

**Gap:** Brand tier and archetype are defined, but parent-subsidiary relationships are not. Real transaction data often needs to roll up to parent companies (e.g., Yum Brands: Taco Bell, Pizza Hut, KFC; Restaurant Brands International: Burger King, Popeyes, Tim Hortons).

**Why It Matters:** Queries like "How is Yum Brands performing?" require mapping brands to parents.

**Recommendation:** Include a brand-to-parent mapping in the synthetic data structure, even if it's simplified.

---

### Gap 8: No Transaction Type Distinction

**Location:** FR-6

**Gap:** The synthetic data does not distinguish between authorization, settlement, and refund records. In real transaction data:
- Authorizations represent intent (card-present, hold)
- Settlements represent actual transfer (post-authorization)
- Refunds are distinct transaction types

**Impact:** Mixing transaction types can distort spending metrics. A refund should not count as new spending.

**Recommendation:** Specify that synthetic data represents settled transactions only, or include `transaction_type` dimension (authorization, settlement, refund, void).

---

## Recommended Changes

### RC-1: Clarify Brand Names for Eval (High Priority)

**Location:** FR-6.5, FR-7.6

**Change:** Either use real brand names in synthetic data or create fictional brand equivalents with explicit mapping. If using archetypes, revise benchmark queries to use the same fictional names.

---

### RC-2: Unify Auto-Aggregation Logic (High Priority)

**Location:** FR-3.3, FR-4.4

**Change:** Remove the aggregation rule from FR-4.4 and have it reference FR-3.3 as the authoritative source. Alternatively, make FR-4.4 the authoritative spec and remove the conflicting rules from FR-3.3.

---

### RC-3: Revise E-commerce Benchmark (Medium Priority)

**Location:** NFR-3.5

**Change:** Revise "E-commerce share of retail SHALL be 20-25% in 2024" to "15-18% in 2024" to match Census Bureau reported data.

---

### RC-4: Add Payment Network Dimension (Medium Priority)

**Location:** FR-3.1

**Change:** Add `payment_network: [visa, mastercard, amex, discover]` to dimension categories, or clarify that card_type includes network information.

---

### RC-5: Add Day-of-Week Dimension (Medium Priority)

**Location:** FR-3.1

**Change:** Add `day_of_week: [monday, tuesday, wednesday, thursday, friday, saturday, sunday]` to enable day-specific queries.

---

### RC-6: Specify Explicit Generation Ranges (Medium Priority)

**Location:** FR-3.1

**Change:** Add birth year cutoffs for each generation as noted in Gap 4.

---

### RC-7: Specify Explicit Income Band Ranges (Medium Priority)

**Location:** FR-3.1

**Change:** Add explicit dollar ranges for each income band as noted in Gap 5.

---

### RC-8: Consolidate CBSA/MSA (Low Priority)

**Location:** FR-6.3

**Change:** Remove MSA from the hierarchy and use only CBSA with 350-400 values.

---

### RC-9: Add Parent Company Mapping (Low Priority)

**Location:** FR-6.5

**Change:** Include brand-to-parent mapping in the synthetic data schema.

---

### RC-10: Add Transaction Type Dimension (Low Priority)

**Location:** FR-6

**Change:** Specify transaction type (settlement vs. refund) or document that synthetic data contains only settled transactions.

---

## Questions for Other SMEs

**For AI/NLP Architecture SME:**
- The dimension extraction pipeline uses parallel specialized nodes (FR-3.2). How does the system handle cross-dimension dependencies? For example, if "young professional" is mentioned, both generation and income might be inferred simultaneously - does the parallel architecture handle joint inference or are there ordered dependencies?

**For Data Analytics SME:**
- The continuous aggregates specified in FR-6.8 (daily/weekly/monthly rollups) require maintaining separate aggregates. What is the expected query routing strategy - does the API automatically select the most granular available aggregate that satisfies the query, or does the pipeline need to specify aggregation level explicitly?

**For Product Manager:**
- The benchmark queries in FR-7.6 use specific real brand names. Should these be treated as ground truth that the synthetic data must support, or are these illustrative examples that could be adapted to match whatever fictional brand names appear in the synthetic data?
