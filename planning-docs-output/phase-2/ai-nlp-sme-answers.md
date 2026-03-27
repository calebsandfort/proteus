# AI/NLP Architecture SME: Phase 2 Cross-SME Answers

## Overview

This document answers all questions directed at the AI/NLP Architecture SME from other Phase 1 SME analyses. Answers are grounded in established AI/NLP best practices and reference specific architectural decisions from the Proteus HLRD.

---

## From Integration Engineer SME

### Question 1: Aggregation Level in Tool Selection Pipeline

**Question:** How does the tool selection pipeline determine which aggregation level to request from the API? If the user asks "What were Target's sales last quarter?" the pipeline must decide whether to request daily, weekly, or monthly aggregates. Does this decision happen during dimension extraction or during tool selection? Should the AI pipeline be aware of aggregation level at all, or should it always request `aggregation: "auto"` and let the API decide?

**Answer:**

The aggregation level decision should happen during **dimension extraction**, not during tool selection. Here is the recommended architecture:

**Pipeline Flow:**
```
User Query → Planner Node → Tool Selection → Dimension Extraction → API Call
                                                          ↑
                                              ┌─────────────────────────┐
                                              │ Aggregation Level Parser │
                                              │ (specialized node)       │
                                              └─────────────────────────┘
```

**Recommended Strategy: Hybrid (Explicit When Specified, Auto When Ambiguous)**

1. **Dimension Extraction Stage:** A dedicated `AggregationLevelNode` extracts explicit aggregation hints from the query
   - "daily breakdown" → `level: "daily"`
   - "monthly view" → `level: "monthly"`
   - "last quarter" without granularity → `level: "auto"`

2. **Auto-Aggregation Rules (at API layer):**
   | Time Range | Default Aggregation |
   |------------|---------------------|
   | 1-7 days | Hourly/Daily |
   | 8-90 days | Daily |
   | 91-365 days | Weekly |
   | 1+ years | Monthly |

3. **LLM-Assisted Detection:** When no explicit granularity is mentioned, the dimension extraction LLM should infer from query intent:
   - "trend" or "over time" → prefer finer granularity (daily/weekly)
   - "summary" or "overview" → prefer coarser granularity (monthly/quarterly)

**Should the AI pipeline be aware of aggregation level?**

Yes, but with a **two-tier approach**:
- **Tier 1 (Extraction):** The pipeline extracts explicit or inferred aggregation hints and passes them to the API
- **Tier 2 (API Decision):** The API retains final authority via `aggregation: "auto"`, applying domain rules the pipeline may not know (e.g., fiscal quarter boundaries, holiday-adjusted seasonality)

This avoids hard-coding business logic in the AI pipeline while still allowing user intent to influence granularity.

---

### Question 2: Expected Network Path from FastAPI to Data API

**Question:** What is the expected network path from FastAPI to the data API? If the data API is ASP.NET Core (per HLRD) vs. FastAPI endpoints (per established stack), the pipeline's call pattern differs. Is the pipeline making HTTP calls to an external API, or calling internal service methods?

**Answer:**

**Per the established tech stack (FastAPI backend container), the recommended architecture is:**

```
Next.js (Frontend)
    ↓ HTTP /api/copilotkit (CopilotKit agent route)
FastAPI (Backend Container - AI Pipeline)
    ↓ Internal service call (not HTTP)
    └── /api/query → TimescaleDB
```

**Key Architectural Points:**

1. **No HTTP call to external API.** The AI pipeline (FastAPI) and data retrieval API should be the **same FastAPI application** within the backend container. This avoids network latency penalties.

2. **Service-Level Call Pattern:**
   ```python
   # Within FastAPI, the pipeline directly calls repository methods
   @router.post("/api/copilotkit")
   async def handle_query(query: str, context: ConversationContext):
       plan = await planner.run(query, context)
       dimensions = await extractor.run(plan.selected_tool, query)

       # Direct call to repository (same process)
       result = await repository.execute(
           tool=plan.selected_tool,
           dimensions=dimensions
       )
       return await response_generator.run(query, result)
   ```

3. **If ASP.NET Core is Required (per HLRD):** This would require adding a fourth container. In that case:
   - Use **HTTP calls with connection pooling** (asyncpg or httpx with keepalive)
   - Target: <50ms network overhead between containers
   - Implement **circuit breaker pattern** for ASP.NET Core failures
   - Cache frequently used dimension enumerations locally

4. **Interface Boundary:** The repository abstraction should hide the data API implementation:
   ```python
   class TransactionRepository(Protocol):
       async def execute(self, tool: str, dimensions: dict) -> list[dict]: ...

   class FastAPIRepository:
       """For same-container execution"""
       async def execute(self, tool: str, dimensions: dict) -> list[dict]:
           return await self._query_timescale(tool, dimensions)

   class HttpRepository:
       """For cross-container ASP.NET Core execution"""
       async def execute(self, tool: str, dimensions: dict) -> list[dict]:
           async with httpx.AsyncClient() as client:
               response = await client.post(f"{self.base_url}/query", json={...})
               return response.json()
   ```

**Recommendation for Proteus:** Stay with FastAPI-only data API within the existing backend container. Adding ASP.NET Core as a separate service adds unnecessary network hops and container complexity for Phase 1.

---

## From UX Designer SME

### Question 1: Observability Panel Data Surface

**Question:** How does the observability panel surface tool selection reasoning? Should it show RAG retrieval scores, LLM confidence scores, or just the final selected tool? What's the performance cost of surfacing this data per message?

**Answer:**

**Recommended Data Surface for Observability Panel:**

The observability panel should expose **three tiers** of data, progressively disclosed:

| Tier | Content | When Shown |
|------|---------|------------|
| **Tier 1 (Summary)** | Selected tool(s), extracted dimensions, latency per stage | Always visible when panel is open |
| **Tier 2 (RAG Details)** | Top-3 RAG candidates with similarity scores, why top-1 was selected | Expandable per message |
| **Tier 3 (Raw)** | Full tool definitions retrieved, raw API request/response | Explicit "Show raw" action |

**What to Surface (Specific Recommendations):**

1. **RAG Retrieval Scores:** Yes, show top-3 candidates with scores (e.g., "market_share: 0.82, brand_trends: 0.71, category_analysis: 0.65"). This helps power users understand retrieval quality.

2. **LLM Confidence Scores:** Show aggregate confidence only, not per-parameter:
   - High (>=0.85): No indicator needed
   - Medium (0.70-0.84): Subtle indicator
   - Low (<0.70): Highlight with suggestion to verify

3. **Extracted Dimensions Table:**
   ```
   | Dimension    | Extracted Value | Confidence |
   |--------------|-----------------|------------|
   | brand        | Target          | High       |
   | time_range   | Q3 2024         | High       |
   | aggregation  | auto (monthly)  | Derived    |
   ```

**Performance Cost:**

Surfacing this data is **essentially free** since it is already computed:
- RAG scores: Returned from vector search, negligible cost
- Confidence scores: Computed inline with LLM response
- Latency: Adding observability data adds <5ms to response serialization

**Caveat:** Storing full raw API responses per message increases memory usage. Only keep the last 5 messages' raw data in memory; older data can be fetched from a logs endpoint if needed.

---

### Question 2: Ambiguous Query HITL Format

**Question:** For ambiguous queries triggering HITL clarification, what's the expected format from the LLM? Can it provide confidence scores for each candidate, or just a list?

**Answer:**

**Expected HITL Clarification Format:**

The LLM should output a **structured clarification response** that includes:

```json
{
  "type": "clarification",
  "message": "I found multiple ways to interpret your query:",
  "options": [
    {
      "id": "A",
      "interpretation": "Target's market share trend over the past year",
      "confidence": 0.82,
      "selected_params": {
        "tool": "market_share_trend",
        "dimensions": {"brand": "Target", "time_range": "past_12_months"}
      }
    },
    {
      "id": "B",
      "interpretation": "Target's market share compared to Walmart over the past year",
      "confidence": 0.65,
      "selected_params": {
        "tool": "competitive_comparison",
        "dimensions": {"brands": ["Target", "Walmart"], "time_range": "past_12_months"}
      }
    }
  ],
  "suggested_question": "Did you want to compare Target to another brand, or see Target's standalone trend?"
}
```

**Key Format Requirements:**

1. **Include confidence scores per option** — This lets the UI render options with visual ranking (e.g., highlight Option A if confidence is notably higher)

2. **Show the interpreted parameters** — Users can verify if the system understood their intent correctly

3. **Provide a follow-up prompt** — The `suggested_question` field gives the UX a natural follow-up phrase to use

4. **Limit to 2-3 options** — If more exist, show top 2 plus "Something else..." option

**UX Rendering Example:**

```
┌──────────────────────────────────────────────────────────────┐
│  I found a few ways to interpret your query:                 │
│                                                              │
│  ○ A) Target's market share trend over the past year        │
│      [High confidence]                                       │
│                                                              │
│  ● B) Target vs Walmart comparison over the past year        │
│      [Medium confidence] ← UI highlights this option        │
│                                                              │
│  Did you want to compare Target to another brand,            │
│  or see Target's standalone trend?                           │
│                                                              │
│  [ Select A ]  [ Select B ]  [ Show me both ]                │
└──────────────────────────────────────────────────────────────┘
```

---

## From Consumer Spending SME

### Question 1: Multi-Tool Query Handling

**Question:** How does the RAG-based tool retrieval handle cases where a user query spans multiple analytical capabilities (e.g., "show me Target's market share trend by generation compared to Walmart" requires both market share and demographic analysis)?

**Answer:**

**Multi-Tool Query Handling via Planner Node:**

The planner node (documented in my Phase 1 analysis) is responsible for detecting and decomposing multi-tool queries.

**Pipeline for Compound Queries:**

```
User Query: "show me Target's market share trend by generation compared to Walmart"

    ↓

Planner Node (chain-of-thought):
    ├─ Detection: "This query requires TWO tools:"
    │   ├─ Tool 1: market_share_trend (for brand comparison)
    │   └─ Tool 2: customer_demographics (for generation breakdown)
    │
    ├─ Execution Plan:
    │   {
    │     "tools": [
    │       {"tool_id": "market_share_trend", "params": {"brands": ["Target", "Walmart"]}},
    │       {"tool_id": "demographic_breakdown", "params": {"brand": "Target", "dimension": "generation"}}
    │     ],
    │     "synthesis_needed": true,
    │     "synthesis_instruction": "Overlay demographic skew on market share trend"
    │   }
    │
    ↓

Parallel Execution → Result Synthesizer → Unified Response
```

**RAG Retrieval for Multi-Tool:**

1. **First pass:** RAG retrieves top-8 candidates as normal
2. **Planner evaluation:** The planner LLM receives the query + top-8 tool definitions and determines:
   - Single-tool sufficient? (e.g., "show Target's market share")
   - Multiple tools required? (e.g., "market share by generation compared to Walmart")
   - Ambiguous? (route to clarification)

3. **Tool selection for each sub-query:** Run RAG retrieval again with the decomposed query if needed

**Handling Overlapping Capabilities:**

When tools have overlapping capabilities (e.g., both `market_share_trend` and `brand_performance` could answer a query):
- The planner should select the **most specific** tool for each sub-task
- Log the alternative consideration for observability
- If confidence is low on which tool is correct, surface HITL

---

### Question 2: Dimension Disambiguation Strategy

**Question:** What is the strategy for disambiguating dimension references when users say vague terms like "recently," "most," or "growing"? How do you map these to specific time ranges or comparison operators?

**Answer:**

**Dimension Disambiguation Strategy:**

Implement a **three-stage pipeline** for vague references:

```
Stage 1: Deterministic Pattern Matching (fast, ~10ms)
Stage 2: LLM-Assisted Resolution (slower, ~200ms)
Stage 3: HITL Clarification (last resort)
```

**Stage 1: Deterministic Patterns (Time/Quantifiers)**

| Vague Term | Mapping Rule | Output |
|------------|-------------|--------|
| "recently" | Last 30 days | `{"start": "2024-02-25", "end": "2024-03-27"}` |
| "most" | Top 1 by some metric | Requires context for metric |
| "growing" | Positive trend detection | Requires temporal data |
| "last week" | Rolling 7 days | `{"start": "2024-03-20", "end": "2024-03-27"}` |
| "this month" | Current calendar month | `{"start": "2024-03-01", "end": "2024-03-31"}` |
| "Q1" | Current year Q1 | `{"start": "2024-01-01", "end": "2024-03-31"}` |

**Stage 2: LLM-Assisted Resolution**

When deterministic rules cannot resolve:

```
Query: "Show me the most growing categories"
Context: Previous message asked about "grocery vs apparel"

LLM Resolution:
  - "most" refers to highest growth rate
  - "growing" implies YoY comparison
  - Requires metric: transaction_volume_growth
  - Maps to: top_categories_by_growth with sort=desc, limit=5
```

**Stage 3: HITL Clarification**

When even the LLM cannot resolve confidently:

```
┌──────────────────────────────────────────────────────────────┐
│  I see "most" in your query. Did you mean:                   │
│                                                              │
│  ○ The top 5 categories by transaction volume                │
│  ○ Categories with the highest growth rate (YoY)             │
│  ○ Categories with the most customers                        │
│                                                              │
│  [ Select one ]  [ Tell me more ]                            │
└──────────────────────────────────────────────────────────────┘
```

**Key Principle:** Never silently default vague terms to a specific interpretation without at least attempting deterministic resolution. If deterministic fails, try LLM. Only escalate to HITL when both fail.

---

### Question 3: Synonym and Layman Term Handling

**Question:** How will the system handle dimension extraction when users use synonyms or layman terms (e.g., "young people" for Gen Z, "credit card" broadly for all card types)?

**Answer:**

**Synonym and Layman Term Handling:**

**Strategy: LLM + Lookup Table Hybrid**

```
┌─────────────────────────────────────────────────────────────┐
│  Query: "spending by young people at Amazon"                │
│                                                             │
│  LLM Extraction:                                           │
│    "young people" → generation: "Gen Z" OR "Millennial"?   │
│                                                             │
│  Resolution via lookup:                                     │
│    "young people" → {                                       │
│      "canonical": "Gen Z",                                 │
│      "confidence": 0.7,                                    │
│      "alternatives": ["Millennial"]                        │
│    }                                                        │
│                                                             │
│  Since confidence < 0.85, surface disambiguation:          │
│  "Did you mean Gen Z (ages 18-27) or Millennials (28-43)?" │
└─────────────────────────────────────────────────────────────┘
```

**Synonym Mapping Tables (Initial Set):**

| Layman Term | Canonical Value | Confidence | Alternatives |
|-------------|-----------------|------------|--------------|
| "young people" | Gen Z | 0.7 | Millennial |
| "old people" | Boomer | 0.7 | Gen X |
| "millennials" | Millennial | 1.0 | — |
| "credit card" | credit | 0.8 | debit (if ambiguous) |
| "debit card" | debit | 1.0 | — |
| "store card" | credit | 0.6 | In-store channel |
| "kids" | Gen Z | 0.5 | Millennial children |
| "teenagers" | Gen Z | 0.8 | — |
| "rich people" | income_band_5 (75K-100K) | 0.4 | income_band_6 (100K-150K) |
| "budget" | budget tier | 1.0 | — |
| "premium" | premium tier | 1.0 | — |
| "fancy" | premium tier | 0.8 | — |
| "cheap" | budget tier | 0.7 | — |

**Brand Alias Handling:**

Brand names require fuzzy matching due to:
- Common misspellings: "Targer" → Target
- Parent/subsidiary: "Walmart" includes "Sam's Club"
- Retailer vs. Brand: "Amazon" as retailer vs. "Amazon Basics"
- Regional variants: "McDonalds" vs "McDonald's"

Implementation:
```python
# Use fuzzywuzzy or similar for string matching
from fuzzywuzzy import fuzz

def resolve_brand(query_brand: str, valid_brands: list[str]) -> tuple[str, float]:
    scores = [(brand, fuzz.ratio(query_brand.lower(), brand.lower()))
              for brand in valid_brands]
    best_match, score = max(scores, key=lambda x: x[1])
    return (best_match, score / 100.0)
```

**General Principle:** Always validate extracted values against the API's dimension enumeration endpoint. Never pass an unvalidated brand/category name to the API.

---

## From Market Analyst SME

### Question 1: Tool Prioritization for Eval Suite

**Question:** Given the 10-50 tool range, which analytical capabilities are most valuable for investor/analyst audiences? The Market Analyst needs this to prioritize which tools to implement first for the eval suite.

**Answer:**

**Recommended Tool Prioritization (from AI/NLP Architecture Perspective):**

Based on query complexity and multi-turn conversation patterns, here is the prioritized tool set:

| Priority | Tool | Rationale for AI/NLP | Eval Query Complexity |
|----------|------|----------------------|----------------------|
| **P0** | market_share_trend | High-frequency, clear intent signals, good for baseline eval | L1: Simple |
| **P0** | brand_comparison | Requires multi-brand dimension extraction, frequent | L2: Comparative |
| **P0** | yoy_growth_analysis | Temporal disambiguation testing, YoY is common pattern | L1-L2: Simple |
| **P0** | category_trends | Single category dimension extraction | L1: Simple |
| **P1** | cross_shopping_analysis | Multi-tool candidate (share + demographics) | L3: Complex |
| **P1** | demographic_breakdown | Generation/income extraction testing | L2: Moderate |
| **P1** | geographic_heatmap | State/region extraction, hierarchical geo | L2: Moderate |
| **P2** | channel_analysis | Channel dimension (online/in-store) | L1-L2: Simple |
| **P2** | customer_retention | Cohort/time-series complexity | L3: Complex |
| **P2** | basket_analysis | Avg transaction extraction | L1: Simple |

**For Phase 1 Eval Suite, implement these 8 tools first:**

1. `market_share_trend` — Most common, straightforward
2. `brand_comparison` — Tests multi-brand extraction
3. `yoy_growth_analysis` — Tests time range extraction
4. `category_trends` — Single-dimension testing
5. `demographic_breakdown` — Generation/income extraction
6. `geographic_breakdown` — State/region extraction
7. `cross_shopping_overlap` — Multi-tool decomposition
8. `top_n_rankings` — Ordinal/limit extraction

---

### Question 2: Eval Query Examples

**Question:** The Market Analyst can provide 20-30 representative queries across complexity levels for the eval suite. What natural language phrasing should these queries use?

**Answer:**

**Recommended Eval Query Phrasing Guidelines:**

**Level 1 (Simple Factual):** Direct questions with clear dimensions
- "What is Walmart's market share in grocery?"
- "How much did Target grow last quarter?"
- "Show me Chipotle's sales by region"
- "What is the average basket size at Home Depot?"
- "Which brands have the highest transaction volume in electronics?"

**Level 2 (Comparative):** Multi-brand or multi-dimension
- "How is McDonald's doing vs. Burger King?"
- "Compare Target and Walmart's market share trends over the past year"
- "Which fast food chain has the highest growth?"
- "Show me Amazon vs. eBay by category"
- "Is Starbucks gaining or losing share in coffee?"

**Level 3 (Contextual/Analytical):** Requires inference or multiple tools
- "Why did Target's sales spike in March?" (event analysis)
- "Are Target's customers trading up or down compared to last year?" (cross-shopping + trend)
- "Show me the top 5 automotive brands by sales, and how has that changed over 3 years?" (ranking + trend)
- "Which brands are taking share from each other in apparel?" (share shift analysis)

**Synonym Variations to Include:**

| Concept | Phrasings to Test |
|---------|------------------|
| Market Share | "share of market", "market position", "% of category", "competitive position" |
| YoY Growth | "vs last year", "year over year", "grew X%", "changed from last year" |
| Generation | "young people", "millennials", "gen z", "boomers" |
| Geography | "southwest", "texas", "the south", "sunbelt" |
| Time | "recently", "last quarter", "Q3", "the past 6 months" |

**Key Phrasing Anti-Patterns to Test:**
- "How's Nike doing?" (ambiguous — tests clarification routing)
- "Show me trends" (no dimension — tests default behavior)
- "Who's winning?" (undefined metric — tests clarification)
- "I want to see Amazon, Target, and Walmart" (comma-separated list — tests multi-brand extraction)

---

### Question 3: Clarification Language Expectations

**Question:** When the system asks for clarification, what phrasing do analysts expect? For example, "Which time period?" vs. "Did you mean last quarter or the past 3 months?" Domain-appropriate phrasing improves user trust.

**Answer:**

**Clarification Language Principles:**

1. **Be specific, not generic.** "Which time period?" is too generic. Instead: "I see you mentioned Target — which time period should I use?"

2. **Offer concrete options, not open-ended questions.** Instead of "What timeframe?", say "Should I look at last quarter (Oct-Dec 2024) or the past 3 months (Jan-Mar 2024)?"

3. **Mirror analyst vocabulary.** Use terms they recognize:
   - "quarter" not "three-month period"
   - "vs." not "compared to"
   - "YoY" or "year-over-year" not "compared to same period last year" (too verbose)

**Recommended Phrasing Templates by Dimension:**

| Dimension | Generic (Avoid) | Analyst-Preferred |
|-----------|-----------------|-------------------|
| Time | "Which time period?" | "Should I use Q4 2024 (Oct-Dec) or the most recent 3 months?" |
| Time | "When?" | "Did you mean last quarter or a specific date range?" |
| Brand | "Which brand?" | "Should I include Target only, or also compare to Walmart?" |
| Brand | "Which brands?" | "I found 3 brands matching 'Starbucks' — did you mean Starbucks Coffee, Starbucks Reserve, or both?" |
| Category | "Which category?" | "Did you mean the full 'Fast Food' category, or a specific subcategory like 'Coffee Shops'?" |
| Geography | "Where?" | "Should I look at all locations, or a specific state or metro area?" |
| Aggregation | "What granularity?" | "Would you like daily data, weekly rollups, or monthly totals?" |

**Format Example:**

```
┌──────────────────────────────────────────────────────────────────┐
│  I found multiple brands matching "Starbucks":                    │
│                                                                   │
│  ○ Starbucks Coffee (majority of transactions)                    │
│  ○ Starbucks Reserve (premium, ~5% of transactions)                │
│  ○ Both                                                          │
│                                                                   │
│  [ Select one ]  [ Show me both ]                                │
└──────────────────────────────────────────────────────────────────┘
```

**Key Insight:** Analysts prefer **structured choices** over **free-text follow-up**. The clarification UI should present buttons/radio options, not just a text input asking them to rephrase.

---

## From Data Analytics SME

### Question 1: Temporal Ambiguity Resolution

**Question:** How does the NLP layer handle queries like "show spending" without explicit time range? Should we default to last 30 days, current month, or ask for clarification?

**Answer:**

**Recommended Default Behavior: Context-Dependent with Reasonable Default**

**Decision Tree:**

```
Query: "show spending"
    │
    ├─ [Has prior context with time range?]
    │   └─ Yes: Apply same time range, confirm with user
    │
    ├─ [Is this the first query in conversation?]
    │   └─ Yes: Default to "last 30 days" with visual indicator
    │
    └─ [Does "spending" imply a category?]
        └─ No clear category: Ask for clarification
```

**Default Time Range Selection:**

| Query Type | Default | Rationale |
|------------|---------|-----------|
| "show spending" | Last 30 days | Reasonable for quick scan |
| "show spending at [brand]" | Last 30 days | Quick brand health check |
| "show spending by category" | Last 30 days | Category overview |
| "show spending trend" | Last 90 days | "trend" implies longer view |
| "how much do they spend" | Last 30 days | Initial data pull |
| "spending compared to last year" | Last completed quarter + YoY | Explicit comparison |

**Why Last 30 Days (Not Current Month):**

- Current month is typically incomplete (data may not be available for current partial month)
- 30 days provides a complete, comparable period
- Easier to align with prior year (same 30-day window)

**UI Indication:**

When defaulting, show the user what was assumed:
> "Showing your spending over the **last 30 days** (Feb 25 - Mar 27). [Change]"

This gives users an easy escape hatch without requiring clarification for every ambiguous query.

**When to Ask for Clarification Instead:**

Ask when:
- Multiple reasonable defaults exist and user intent is unclear
- The query is extremely vague ("show me the data")
- Defaulting would likely be wrong based on context (e.g., user just asked about Q4, now says "show spending again")

---

### Question 2: Multi-Tool Orchestration

**Question:** With 10-50 tools each having 30+ dimensions, how should tool selection handle compound queries that span multiple tools?

**Answer:**

**Multi-Tool Orchestration Architecture:**

**1. Planner Node Detection:**

The planner evaluates whether a query requires:
- **Single tool** — One tool can answer fully
- **Multi-tool sequential** — One tool feeds into another (e.g., find top brand, then get its demographics)
- **Multi-tool parallel** — Independent tools, results synthesized (e.g., market share + demographic breakdown)
- **Ambiguous** — Route to clarification

**2. Execution Patterns:**

```
Pattern A: Parallel (Independent Results)
─────────────────────────────────────────
Query: "Show Target vs Walmart market share and customer demographics"
         │
         ▼
┌─────────────────┐     ┌─────────────────────────┐
│ Tool: market_share │     │ Tool: demographics      │
│ Params: brands=... │     │ Params: brand=Target    │
└────────┬────────┘     └────────────┬──────────────┘
         │                           │
         └─────────┬─────────────────┘
                   ▼
         ┌─────────────────────┐
         │ Result Synthesizer  │
         │ (merge by time/geo)  │
         └─────────────────────┘


Pattern B: Sequential (One Feeds Into Other)
───────────────────────────────────────────
Query: "What's the market share trend for the top 3 grocery brands?"
         │
         ▼
┌─────────────────────┐
│ Tool: top_n_rankings │  → Returns: [Walmart, Target, Kroger]
│ Params: category=grocery, n=3 │
└────────┬────────────┘
         │
         ▼ (output becomes input)
┌─────────────────────┐
│ Tool: market_share  │
│ Params: brands=[Walmart, Target, Kroger] │
└─────────────────────┘
```

**3. RAG Retrieval for Multi-Tool:**

When the planner detects multi-tool intent:
- Run RAG retrieval for each sub-query separately
- Use the full query as context for each retrieval
- Merge retrieved candidates, deduplicate

**4. Handling Dimension Conflicts Across Tools:**

When two tools have overlapping dimension requirements:
- Use consistent values across tools (if user specified "Texas", apply to both)
- If conflict detected (Tool A needs "TX", Tool B needs "CA"), surface clarification

**5. Confidence Threshold for Multi-Tool:**

If planner confidence for multi-tool detection is <0.70, surface HITL:
```
┌──────────────────────────────────────────────────────────────┐
│  Your query might need two analyses. Did you want:          │
│                                                               │
│  ○ Market share comparison between brands                    │
│  ○ Demographic breakdown of customers                        │
│  ○ Both combined in one view                                 │
│                                                               │
│  [ Select one ]                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### Question 3: Clarification Generation Criteria

**Question:** When aggregation granularity is ambiguous, what criteria should the NLP layer use to generate appropriate clarification questions?

**Answer:**

**Criteria for Generating Clarification Questions:**

**Trigger Conditions (any one is sufficient):**

| Condition | Example Query | Clarification |
|-----------|---------------|---------------|
| Multiple valid granularities | "Show Target's sales" | "Daily, weekly, or monthly?" |
| Implicit but unstated | "How is Target trending?" | "Should I show daily, weekly, or monthly trends?" |
| Conflicting signals | "Show monthly trend for the past week" | Time range and granularity conflict |
| Domain expectation mismatch | "Show sales for 2020" | Monthly too coarse for single year; ask for annual or show monthly with note |

**When NOT to Ask (Resolve Automatically):**

| Scenario | Resolution |
|----------|-----------|
| Query has explicit granularity | Use it ("daily sales" → daily) |
| Query has clear time range but no granularity | Apply auto-rules (see Question 1) |
| Only one valid option | Use it without asking |
| Time range <7 days | Force daily regardless of query |

**Clarification Question Design:**

1. **Present options, not free text:**
   ```
   BAD:  "What aggregation level would you like?"
   GOOD: "Should I show this daily, weekly, or monthly?"
   ```

2. **Explain the trade-off briefly if useful:**
   ```
   "Daily will show more detail but may be noisy for 2 years of data.
    Monthly gives cleaner trends. Which would you prefer?"
   ```

3. **Default selection for impatient users:**
   ```
   "I'll show you monthly trends. [Change to weekly] [Show daily]"
   ```

4. **Use smart defaults based on context:**
   - First query in session: Use default (monthly)
   - Follow-up on detailed question: Match prior granularity
   - Explicit "trend" keyword: Prefer weekly/monthly

**Response Time Impact:**

Clarification adds 1 round-trip (~2-5 seconds total). Balance this against:
- Cost of wrong granularity (user has to re-ask)
- Frequency of ambiguous queries (if rare, ask; if common, default aggressively)

---

### Question 4: Confidence Thresholds for Clarification

**Question:** What tool selection confidence level should trigger a clarification prompt vs. proceeding with best guess?

**Answer:**

**Confidence Threshold Strategy:**

**Recommended Thresholds:**

| Confidence Range | Action | User Experience |
|------------------|--------|-----------------|
| >= 0.85 | Proceed with best guess | No indication of uncertainty |
| 0.70 - 0.84 | Proceed, show low-confidence indicator | Subtle "May need to verify" in observability |
| 0.60 - 0.69 | Clarification recommended | Structured HITL with 2-3 options |
| < 0.60 | Clarification required | HITL with "I'm not sure" message |

**Threshold Calibration:**

These thresholds should be **tuned based on eval results**:

1. **If precision is high (correct tool selected but low confidence):** Lower threshold to 0.75
2. **If recall is low (missing correct tool):** Raise threshold to 0.80
3. **If false positive rate is high (wrong tool selected with high confidence):** Investigate RAG retrieval quality

**Per-Stage Thresholds:**

Tool selection and dimension extraction may have different thresholds:

| Stage | Proceed | Clarify |
|-------|---------|---------|
| Tool Selection | >= 0.80 | < 0.80 |
| Dimension Extraction (brand) | >= 0.75 | < 0.75 |
| Dimension Extraction (time) | >= 0.85 | < 0.85 (deterministic fallback first) |
| Multi-Tool Detection | >= 0.70 | < 0.70 |

**Confidence Score Computation:**

Confidence is a composite of:

```python
def compute_tool_confidence(
    rag_similarity: float,      # RAG retrieval score
    llm_selection_score: float, # LLM preference score
    dimension_match_score: float # How well extracted dimensions fit tool
) -> float:
    # Weighted combination
    return (
        0.25 * rag_similarity +
        0.35 * llm_selection_score +
        0.40 * dimension_match_score
    )
```

**What to Show in Observability Panel:**

When confidence is medium-low, surface:
- Which other tools were considered (top-3 with scores)
- Which dimensions contributed to selection
- Which dimensions were ambiguous

**Key Principle:** When in doubt, ask. The cost of a wrong tool call (wrong results, user confusion) exceeds the cost of a clarification round-trip.

---

## Summary

| SME | Question | Key Answer |
|-----|----------|------------|
| Integration Engineer | Aggregation level | Extract during dimension extraction, let API decide via "auto" |
| Integration Engineer | Network path | FastAPI-to-FastAPI internal call (no HTTP) within backend container |
| UX Designer | Observability data | Three tiers: summary, RAG details, raw; include confidence scores |
| UX Designer | HITL format | Structured JSON with options, confidence scores, suggested question |
| Consumer Spending | Multi-tool | Planner node decomposition with parallel/sequential execution |
| Consumer Spending | Disambiguation | Three-stage: deterministic → LLM → HITL |
| Consumer Spending | Synonyms | LLM + lookup table hybrid with fuzzy matching for brands |
| Market Analyst | Tool priority | P0: market_share_trend, brand_comparison, yoy_growth, category_trends |
| Market Analyst | Eval phrasing | Use analyst vocabulary; include synonym variations; test ambiguity |
| Market Analyst | Clarification language | Structured options, concrete time periods, analyst-preferred terms |
| Data Analytics | Temporal ambiguity | Default to last 30 days, show assumption, ask when multiple defaults exist |
| Data Analytics | Multi-tool orchestration | Planner node with parallel/sequential patterns and confidence thresholds |
| Data Analytics | Clarification criteria | Trigger on ambiguity; apply auto-rules when only one valid option |
| Data Analytics | Confidence thresholds | 0.85+ proceed, 0.60-0.84 clarify, <0.60 require clarification |

---

*Answers prepared by AI/NLP Architecture SME — Phase 2 Cross-SME Consultation*
