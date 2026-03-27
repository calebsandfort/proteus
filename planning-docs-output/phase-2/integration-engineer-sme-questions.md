# Cross-SME Questions for Integration Engineer SME (integration-engineer-sme)

## From AI/NLP SME (ai-nlp-sme)

**Context:** The AI/NLP SME is designing the multi-tool orchestration and dimension validation. They need to understand the API contract for batch operations and dimension enumeration.

1. **Multi-Tool API Contract Design:**
   If the planner node generates multiple API calls, should these be parallelized by the frontend (fire-and-forget) or should the API expose a batch endpoint that handles parallelization internally? Parallel execution in the frontend may violate the 500ms API SLA.

2. **Dimension Enumeration Endpoint:**
   Should the API expose an endpoint that lists valid values for each dimension (e.g., GET /dimensions/brands, GET /dimensions/states)? This would allow the AI pipeline to validate extracted dimensions against allowed values before constructing the query.

3. **Result Pagination Strategy:**
   For queries that return large result sets (e.g., daily transactions for 2 years across 100 brands), should the API handle aggregation or return raw data? From AI perspective, raw data is harder to visualize; prefer pre-aggregated results.

---

## From UX Designer SME (ux-designer-sme)

**Context:** The UX Designer is designing responsive layouts and error state handling. They need technical constraints to inform design decisions.

1. **Chat Sidebar Minimum Width:**
   The chat sidebar width (380-420px) affects how much of the main canvas is visible. Is there a minimum viewport width we should design for? Should we collapse the chat on smaller screens, or is this out of scope for Phase 1?

2. **API Error State Mapping:**
   How does the API return error states that map to user-friendly messages? Should 500 errors, timeout errors, and validation errors all surface differently in the UI?

---

## From Consumer Spending SME (consumer-spending-sme)

**Context:** The Consumer Spending SME is designing the dimensional model and query interface. They need to understand API parameter handling and database partitioning.

1. **API Parameter Cardinality:**
   What is the expected cardinality for tool parameters in the REST API? If a query specifies brand, category, geography, generation, income_band, time_range simultaneously, how does the API handle this (AND vs. OR logic)?

2. **TimescaleDB Partitioning Strategy:**
   For TimescaleDB, what hypertable partitioning strategy supports both time-range queries and high-cardinality dimension filters (e.g., filtering by specific brand + zip simultaneously)?

3. **Brand Alias Normalization:**
   How should brand aliases and name normalization be handled at the data ingestion layer vs. query layer?

---

## From Market Analyst SME (market-analyst-sme)

**Context:** The Market Analyst is concerned about query latency and data refresh. They need technical details on performance characteristics.

1. **Query Latency at Scale:**
   With 10M+ rows, what are realistic query latency expectations? Can true interactive speeds (<5s) be achieved with proper indexing, or is caching required?

2. **Tool Selection Scale:**
   Is RAG + LLM selection tractable for 10-50 tools with 30+ dimensions each? What embedding approach is recommended?

3. **Time Travel Queries:**
   How should the synthetic data layer handle "time travel" queries (e.g., "what did the data show as of Q1 2024")?

---

## From Data Analytics SME (data-analytics-sme)

**Context:** The Data Analytics SME is designing caching and data refresh strategies. They need to understand the data architecture constraints.

1. **Caching Strategy:**
   Should aggregation results be cached? What's the appropriate invalidation strategy when underlying data might be considered "current" vs "historical"?

2. **Real-Time Data Expectations:**
   Is any component expected to show real-time or near-real-time data, or is all data effectively batch-loaded synthetic data?

3. **API Pagination Approach:**
   For result sets exceeding display capacity, should API return paginated results with cursor-based pagination or offset-based?

4. **Multi-Tenancy Requirements:**
   Should the data layer support tenant isolation, or is this a single-tenant demonstration system?
