# Cross-SME Answers from Integration Engineer SME (Phase 2)

## From AI/NLP SME (ai-nlp-sme)

---

**Question 1: Multi-Tool API Contract Design**

> If the planner node generates multiple API calls, should these be parallelized by the frontend (fire-and-forget) or should the API expose a batch endpoint that handles parallelization internally? Parallel execution in the frontend may violate the 500ms API SLA.

**Answer:**

**Recommendation: Expose a batch endpoint that handles parallelization internally, not fire-and-forget from the frontend.**

The 500ms API SLA applies to individual query endpoints, not to the overall user-perceived latency. When the planner generates multiple API calls (e.g., one for market share, one for demographics), the system has two architectural options:

**Option A: Frontend fires multiple requests in parallel (fire-and-forget)**

```
Frontend                  API
   |--- Tool A (async) ----→|
   |--- Tool B (async) ----→|   (both sent simultaneously)
   |←-------- Tool A -------|
   |←-------- Tool B --------|
```

This puts parallelism burden on the client, introduces session management complexity (what if one fails?), and the AI pipeline typically runs server-side in FastAPI, not in a browser client. If the AI pipeline is making these calls, "fire-and-forget" is not a safe pattern for data retrieval.

**Option B: Batch endpoint (recommended)**

```python
POST /api/query/batch
{
  "queries": [
    {"tool": "market_share", "dimensions": {...}},
    {"tool": "demographics", "dimensions": {...}}
  ]
}

Response:
{
  "results": [
    {"tool": "market_share", "data": [...], "latency_ms": 120},
    {"tool": "demographics", "data": [...], "latency_ms": 85}
  ],
  "total_latency_ms": 145  # max of parallel calls, not sum
}
```

**Key advantages:**
- The API server uses a connection pool to execute queries against TimescaleDB in parallel (asyncpg supports this natively)
- Single HTTP round-trip reduces network overhead
- The AI pipeline receives all results in one response, simplifying result synthesis
- Latency becomes `max(t_A, t_B)` instead of `t_A + t_B`
- Error handling is centralized; if one query fails, the response can indicate partial success vs. full failure

**Implementation note for the FastAPI stack:** Use `asyncio.gather()` to execute multiple repository calls concurrently within the batch endpoint. The TimescaleDB connection pool (configured via asyncpg with `min_size=5, max_size=20`) handles concurrent query execution efficiently.

**Interaction with 500ms SLA:** The SLA is per-individual-query, not per-batch. A batch of 2 parallel queries that each complete in 150ms satisfies the SLA for each constituent query. The total batch response time (~150-200ms including serialization) is well within any reasonable API Gateway timeout.

---

**Question 2: Dimension Enumeration Endpoint**

> Should the API expose an endpoint that lists valid values for each dimension (e.g., GET /dimensions/brands, GET /dimensions/states)? This would allow the AI pipeline to validate extracted dimensions against allowed values before constructing the query.

**Answer:**

**Recommendation: Yes, expose dimension enumeration endpoints — but implement them as cached, lightweight endpoints, not live database queries per request.**

The AI pipeline validating dimensions against allowed values before constructing a query is a good pattern (fail-fast on invalid inputs). However, the enumeration endpoints must be designed carefully:

**Proposed endpoint structure:**

```python
GET /api/dimensions/brands          # List all valid brand names
GET /api/dimensions/categories      # List all valid category names
GET /api/dimensions/states          # List all valid US state codes
GET /api/dimensions/generations     # List: ["Gen Z", "Millennial", "Gen X", "Boomer", "Silent"]
GET /api/dimensions/income-bands     # List all income band labels
GET /api/dimensions/channels        # List: ["online", "in-store", "mobile"]
```

**Response format:**

```json
{
  "dimension": "brands",
  "values": [
    {"id": "walmart", "name": "Walmart", "tier": "mass", "aliases": ["wmt", "wal-mart"]},
    {"id": "target", "name": "Target", "tier": "mid", "aliases": ["tgt"]},
    ...
  ],
  "total_count": 147,
  "last_updated": "2024-01-15T00:00:00Z"
}
```

**Critical: Cache these aggressively**

- Store enumeration data in-memory or in a fast cache (e.g., Redis, or just a Python dict refreshed on startup)
- Do NOT hit TimescaleDB for these endpoints — they are metadata, not transaction data
- TTL: Refresh daily or on application restart
- Rationale: A `SELECT DISTINCT brand FROM transactions` on 10M rows is expensive; dimension enumerations should be stable reference data loaded once

**Alias handling:** Include brand aliases in the enumeration (e.g., "wmt" maps to "walmart"). This allows the AI pipeline to normalize extracted dimensions to canonical IDs before query construction.

**For the ingestion vs. query layer question (from Consumer Spending SME):** Brand aliases should be normalized at the data ingestion layer into a `brand_normalized` column. The enumeration endpoint returns the canonical list. This way:
1. Ingestion: "Wal-Mart", "wal-mart", "Walmart" all map to `brand_id = 'walmart'`
2. Query: API only accepts canonical brand names/IDs
3. AI validation: Checks against enumeration, not raw data

**Missing dimension values:** If the AI extracts a dimension value not in the enumeration, return a structured error with suggestions:

```json
{
  "error": "invalid_dimension",
  "dimension": "brand",
  "provided_value": "Walmert",
  "suggestions": ["Walmart (similar: 0.89)", "Target (similar: 0.72)"],
  "hint": "Did you mean one of these brands?"
}
```

---

**Question 3: Result Pagination Strategy**

> For queries that return large result sets (e.g., daily transactions for 2 years across 100 brands), should the API handle aggregation or return raw data? From AI perspective, raw data is harder to visualize; prefer pre-aggregated results.

**Answer:**

**Recommendation: API should always return aggregated data by default, with an optional `raw` flag for explicit raw data requests. Never default to raw data on large result sets.**

This is critical for both performance and the 500ms SLA. A query for "daily transactions for 2 years across 100 brands" without aggregation:
- Time range: ~730 days
- Result set: 73,000 rows minimum (730 days × 100 brands)
- Network transfer: Large JSON payloads
- Visualization: 73,000 individual data points — no chart can render this meaningfully

**Default behavior: Aggregated results**

```python
POST /api/query
{
  "tool": "transaction_volume",
  "dimensions": {
    "brands": ["Chipotle", "Taco Bell", "McDonalds"],
    "period": {"start": "2022-01-01", "end": "2024-01-01"}
  },
  "aggregation": {
    "level": "auto",  # API determines: monthly for 2-year span
    "metric": "sum"
  }
}

Response:
{
  "data": [
    {"brand": "Chipotle", "month": "2022-01", "total_amount": 1450000, "transaction_count": 89000},
    {"brand": "Chipotle", "month": "2022-02", "total_amount": 1380000, "transaction_count": 85000},
    ...
  ],
  "meta": {
    "aggregation_level": "monthly",
    "record_count": 72,
    "truncated": false
  }
}
```

**Aggregation level selection logic (from my Phase 1 analysis):**

| Time Range | Default Aggregation |
|------------|---------------------|
| 1-7 days | Daily |
| 8-90 days | Daily |
| 91-365 days | Weekly |
| 1+ years | Monthly |

**When raw data IS needed (explicit opt-in):**

```python
POST /api/query
{
  "tool": "transaction_volume",
  "dimensions": { ... },
  "aggregation": {
    "level": "raw",
    "limit": 1000  # Required cap — API rejects without
  }
}
```

The `limit` parameter is mandatory for raw queries. The API enforces a hard maximum (e.g., 1,000 rows) to prevent runaway queries. Queries requesting raw data beyond the limit receive a `400 Bad Request` with a suggestion to use aggregation.

**For the AI visualization pipeline:** Pre-aggregated results are the correct interface. The AI response generation stage should never receive raw transaction rows — it receives shaped, aggregated data that maps naturally to chart types. Raw data in the AI context would hallucinate visualization patterns.

**Time-series with high cardinality:** If the user requests "daily data for 50 brands over 2 years" and the result set would exceed display capacity, the API should:
1. Return the aggregated (monthly) result as default
2. Include a `pagination` hint: `{"next_cursor": "...", "has_more": true, "suggested_aggregation": "monthly"}`

---

## From UX Designer SME (ux-designer-sme)

---

**Question 1: Chat Sidebar Minimum Width**

> The chat sidebar width (380-420px) affects how much of the main canvas is visible. Is there a minimum viewport width we should design for? Should we collapse the chat on smaller screens, or is this out of scope for Phase 1?

**Answer:**

**Recommendation: Design for 1280px minimum viewport width for Phase 1. Below 1024px, collapse the chat to an overlay/drawer pattern. This is a Phase 1 requirement, not out of scope.**

**Viewport breakpoints for the Proteus dashboard:**

| Viewport | Layout Behavior |
|----------|-----------------|
| >= 1280px | Full layout: visualization canvas (remaining width) + chat sidebar (380-420px) |
| 1024-1279px | Narrower chat sidebar (320px) + visualization canvas |
| < 1024px | Chat becomes a floating overlay button; visualization is full-width |

**Rationale for 1280px minimum:**
- The HLRD specifies a professional analyst/investor tool — these users typically work on laptops/desktops with >= 1280px displays
- 1280px is the minimum width for "comfortable" split-view analytics work
- Bloomberg terminals and similar tools target 1280px+ as baseline
- Phase 1 should establish the primary experience; responsive adaptation is straightforward given the component structure

**Phase 1 scope clarification:** Implementing responsive collapse is not out of scope — it's a standard practice for web applications. The CopilotKit ChatSidebar component supports right-side pinning; the collapse behavior can be implemented as a CSS/media-query-based visibility toggle.

**Minimum functional width:** The chat sidebar should never go below 320px (icon-only mode is not recommended for Phase 1 — it adds implementation complexity without analytical value). If viewport is < 768px (mobile), show only the visualization with a "Open Chat" floating action button.

**Layout calculation for 1280px reference:**
```
Viewport: 1440px (common analyst display)
Sidebar: 400px
Canvas: 1040px — ample space for ECharts visualizations
```

---

**Question 2: API Error State Mapping**

> How does the API return error states that map to user-friendly messages? Should 500 errors, timeout errors, and validation errors all surface differently in the UI?

**Answer:**

**Recommendation: Yes, errors must be structured and categorized. The API returns machine-readable error codes; the frontend maps these to user-friendly messages. Different error categories require different UI treatments.**

**API Error Response Structure:**

```python
{
  "error": {
    "code": "DIMENSION_VALIDATION_FAILED",
    "message": "Invalid brand value provided",
    "details": {
      "dimension": "brand",
      "provided_value": "Walmert",
      "allowed_values_endpoint": "/api/dimensions/brands",
      "suggestions": ["Walmart", "Target"]
    },
    "recovery_hint": "Did you mean one of these brands?",
    "timestamp": "2024-01-15T10:23:45Z",
    "request_id": "req_abc123"  # For support/debugging
  }
}
```

**Error categorization and UI treatment:**

| Error Category | HTTP Status | Code | UI Treatment |
|----------------|-------------|------|--------------|
| Validation error (missing required dimension) | 400 | `MISSING_REQUIRED_DIMENSION` | Inline form error; highlight missing field; show fix suggestion |
| Validation error (invalid value) | 400 | `INVALID_DIMENSION_VALUE` | Inline error with suggestions; don't clear previous visualization |
| Query timeout | 504 | `QUERY_TIMEOUT` | Toast notification: "Query took too long. Try a shorter time range." |
| Rate limit exceeded | 429 | `RATE_LIMIT_EXCEEDED` | Toast with Retry-After; disable input until cooldown |
| Database unavailable | 503 | `DATABASE_UNAVAILABLE` | Banner: "Data temporarily unavailable. Retrying..." with auto-retry |
| Internal server error | 500 | `INTERNAL_ERROR` | Generic error to user; log `request_id` for debugging |
| Partial results | 200 | `PARTIAL_RESULTS` | Show available data with disclaimer: "Showing partial data (some brands unavailable)" |

**Key principle:** The API should NEVER return raw exception messages or stack traces. All errors return the `request_id` which maps to server-side logs.

**Timeout handling:** The API should enforce its own timeout (e.g., 500ms at the database query level). If TimescaleDB exceeds this, return a `504` with partial results if available. The frontend should not implement its own timeout logic — the API enforces the SLA contract.

**Error recovery UX patterns:**
- Validation errors: User can correct and resubmit without losing context
- Timeout errors: Offer a "Retry with shorter range" quick action
- Rate limit: Show countdown timer for cooldown period
- Database errors: Auto-retry with exponential backoff (3 attempts) before surfacing to user

**Structured errors enable AI pipeline handling too:** The AI pipeline (FastAPI) should check for `error.code` in responses before passing to visualization. If `DIMENSION_VALIDATION_FAILED`, the AI can generate a clarification prompt using `recovery_hint`.

---

## From Consumer Spending SME (consumer-spending-sme)

---

**Question 1: API Parameter Cardinality**

> What is the expected cardinality for tool parameters in the REST API? If a query specifies brand, category, geography, generation, income_band, time_range simultaneously, how does the API handle this (AND vs. OR logic)?

**Answer:**

**Recommendation: All dimension filters are combined with AND logic (conjunction). When multiple values are provided for a single dimension, they are combined with OR within that dimension.**

**Examples:**

```python
# Query: Chipotle + Taco Bell, in Texas + California, for Millennials + Gen Z
{
  "dimensions": {
    "brand": ["Chipotle", "Taco Bell"],        # (Chipotle OR Taco Bell)
    "geo": ["TX", "CA"],                        # (TX OR CA)
    "generation": ["Millennial", "Gen Z"],       # (Millennial OR Gen Z)
    "period": {"start": "2024-01-01", "end": "2024-03-31"}
  }
}

# SQL semantics:
# WHERE brand IN ('Chipotle', 'Taco Bell')
#   AND geo_state IN ('TX', 'CA')
#   AND generation IN ('Millennial', 'Gen Z')
#   AND transaction_timestamp BETWEEN '2024-01-01' AND '2024-03-31'
```

**This is the standard analytical query pattern.** Analysts want to see "Chipotle vs Taco Bell in TX and CA" as a combined comparison, not as four separate queries.

**What about exclusive constraints?**

If a user says "Show me Chipotle in Texas but NOT in California" — this is an exclusion filter. Support this explicitly:

```python
{
  "dimensions": {
    "brand": "Chipotle",
    "geo": {
      "include": ["TX"],        # States to include
      "exclude": ["CA"]          # States to explicitly exclude
    },
    "period": {"start": "2024-01-01", "end": "2024-03-31"}
  }
}
```

**Cardinality concerns:** With 6 simultaneous dimensions, each with moderate cardinality:
- brand: 100-200 values
- category: 40-60 values
- geo: 51 states (or 350 CBSAs)
- generation: 5 values
- income_band: 6-8 values
- time_range: 730 days max

The maximum row count for a full cross-product is `200 × 60 × 350 × 5 × 8 × 730` — impossibly large. **The API must require at least one filter on high-cardinality dimensions (brand, category, or geography) to prevent full-table scans.** This is the "required dimension filters" guardrail mentioned in the HLRD.

**Enforcement rule:**
```python
# Minimum one of these must be present:
required_filters = ["brand", "category", "geo", "period"]

if not any(f in dimensions for f in required_filters):
    raise ValidationError(
        code="INSUFFICIENT_FILTERS",
        message="Query must include at least one of: brand, category, geo, or time range",
        hint="Try adding a specific brand, category, or time period to narrow results."
    )
```

**Query complexity limits:** Even with filters, enforce a maximum result cardinality:
- Aggregated queries: No hard limit (continuous aggregates handle it)
- Raw queries: Maximum 1,000 rows (hard limit)

---

**Question 2: TimescaleDB Partitioning Strategy**

> For TimescaleDB, what hypertable partitioning strategy supports both time-range queries and high-cardinality dimension filters (e.g., filtering by specific brand + zip simultaneously)?

**Answer:**

**Recommendation: Use time-based hypertables with composite indexes on (timestamp, dimension columns). TimescaleDB's chunking handles time-range exclusion automatically; dimension filters use B-tree indexes within each chunk.**

**Hypertable setup:**

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_timestamp TIMESTAMPTZ NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    amount NUMERIC(10, 2) NOT NULL,
    quantity INTEGER,
    geo_state TEXT,
    geo_cbsa TEXT,
    geo_zip TEXT,
    customer_generation TEXT,
    customer_income_band TEXT,
    card_type TEXT,
    channel TEXT,
    tenant_id UUID  -- Future multi-tenancy support
);

-- Create hypertable with daily chunks
SELECT create_hypertable(
    'transactions',
    'transaction_timestamp',
    chunk_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Enable compression after 30 days
ALTER TABLE transactions SET (
    timescaledb.compression,
    timescaledb.compress_segmentby = 'brand, category'
);

-- Add compression policy: compress chunks after 30 days
SELECT add_compression_policy('transactions', INTERVAL '30 days');

-- Add retention policy: drop chunks older than 7 years
SELECT add_retention_policy('transactions', INTERVAL '7 years');
```

**Indexes for dimension filtering:**

```sql
-- Time-based queries with brand filter (most common analytical pattern)
CREATE INDEX idx_transactions_brand_time
ON transactions (brand, transaction_timestamp DESC);

-- Time-based queries with category filter
CREATE INDEX idx_transactions_category_time
ON transactions (category, transaction_timestamp DESC);

-- High-cardinality geography queries (zip-level)
CREATE INDEX idx_transactions_geo_zip
ON transactions (geo_state, geo_zip, transaction_timestamp DESC);

-- Composite for multi-dimension queries
CREATE INDEX idx_transactions_brand_cat_time
ON transactions (brand, category, transaction_timestamp DESC)
INCLUDE (amount);
```

**How chunk exclusion works with dimension filters:**

When you run:
```sql
SELECT SUM(amount)
FROM transactions
WHERE transaction_timestamp BETWEEN '2024-01-01' AND '2024-03-31'
  AND brand = 'Chipotle'
  AND geo_state = 'TX';
```

TimescaleDB:
1. Determines which chunks overlap the time range (chunk exclusion — only relevant chunks are scanned)
2. Within each chunk, the `idx_transactions_brand_time` index is used for the brand filter
3. The index includes `transaction_timestamp DESC` so the time range predicate is evaluated efficiently

**Why not spatial partitioning on brand or geography?**

Spatial partitioning (TimescaleDB's `PARTITION BY LIST` or `PARTITION BY HASH`) would make dimension-filter queries faster, but:
- You can only partition by ONE dimension
- If you partition by brand, queries filtering by category become full-table scans
- Time-based partitioning is the correct choice because time-range filters are always present in analytical queries

**Continuous aggregates for pre-computed rollups:**

```sql
-- Daily rollup by brand + category + state (most common aggregation pattern)
CREATE MATERIALIZED VIEW daily_transactions
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', transaction_timestamp) AS day,
    brand,
    category,
    geo_state,
    customer_generation,
    customer_income_band,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount
FROM transactions
GROUP BY 1, 2, 3, 4, 5, 6;

-- Add refresh policy: refresh every 5 minutes
SELECT add_continuous_aggregate_policy(
    'daily_transactions',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '5 minutes'
);
```

**Query routing for performance:** The API layer should route queries to:
- `daily_transactions` continuous aggregate if time range >= 8 days
- Raw `transactions` table only for queries spanning < 8 days with fine-grained filtering

---

**Question 3: Brand Alias Normalization**

> How should brand aliases and name normalization be handled at the data ingestion layer vs. query layer?

**Answer:**

**Recommendation: Normalize at ingestion, validate at query. Store canonical brand names; reject non-normalized input at the API layer.**

**Data Ingestion Layer:**

```python
# During synthetic data generation or ETL
BRAND_ALIAS_MAP = {
    "walmart": ["walmart", "wal-mart", "wmt", "wal mart", "walmart.com"],
    "target": ["target", "tgt", "target.com"],
    "chipotle": ["chipotle", "chipotle mexican grill", "cmg"],
    "mcdonalds": ["mcdonalds", "mcdonald's", "mcd", "micky d's"],
    # ... etc
}

def normalize_brand(raw_brand: str) -> str:
    normalized = raw_brand.lower().strip()
    for canonical, aliases in BRAND_ALIAS_MAP.items():
        if normalized in aliases:
            return canonical
    return normalized  # If not in map, use as-is but flag for review
```

**In the transactions table:**

```sql
-- Store both raw (for audit/debug) and normalized (for query)
ALTER TABLE transactions ADD COLUMN brand_normalized TEXT;
UPDATE transactions SET brand_normalized = normalize_brand(brand);

-- Index on normalized brand
CREATE INDEX idx_transactions_brand_norm ON transactions (brand_normalized);
```

**Query Layer (API):**

```python
# When AI pipeline extracts "Walmert" from a query:
extracted_brand = "Walmert"

# Check against enumeration
valid_brands = get_cached_dimensions("brands")  # Returns canonical list with aliases

# Find best match
match = find_similar_brand(extracted_brand, valid_brands)
if match.confidence > 0.8:
    canonical_brand = match.canonical_id
elif match.confidence > 0.6:
    # Suggestion to user
    raise ValidationError(
        code="BRAND_SUGGESTION",
        provided_value=extracted_brand,
        suggestions=match.alternatives
    )
else:
    # No good match
    raise ValidationError(
        code="UNKNOWN_BRAND",
        provided_value=extracted_brand,
        hint="Brand not found in dataset. Try a more common name."
    )
```

**Key principles:**

1. **Ingestion normalization:** All incoming data is mapped to canonical brand IDs. The raw original value is preserved in a separate column (e.g., `brand_raw`) for debugging and audit.

2. **Query validation:** The API only accepts canonical brand names (from the enumeration endpoint). The AI pipeline should validate extracted dimensions against the enumeration before constructing queries.

3. **Fuzzy matching at boundaries:** The API should do fuzzy matching when a provided brand is close to a canonical name (Levenshtein distance or embedding similarity), but should NOT silently normalize — it should surface the suggestion and get confirmation (or let the AI pipeline decide).

4. **Enumeration includes aliases:** The `/api/dimensions/brands` endpoint returns canonical brand names AND their aliases so the AI pipeline can map user-phrased brands to canonical ones.

**Why not normalize at query time?** Because:
- The same query with the same brand should return consistent results
- Normalization at query time means the same semantic query could hit different data if aliases change
- Ingestion-time normalization ensures consistency across all historical data

---

## From Market Analyst SME (market-analyst-sme)

---

**Question 1: Query Latency at Scale**

> With 10M+ rows, what are realistic query latency expectations? Can true interactive speeds (<5s) be achieved with proper indexing, or is caching required?

**Answer:**

**Recommendation: With continuous aggregates and proper indexing, aggregated queries on 10M+ rows can achieve 200-500ms latency. Caching provides additional保障 but is not required for the 5s SLA. Raw row queries without aggregation cannot meet the SLA.**

**Latency breakdown for aggregated queries:**

| Query Type | Data Size | Expected Latency | Mechanism |
|------------|-----------|------------------|-----------|
| Aggregated (daily rollup, single brand, 1 year) | ~365 rows | 50-100ms | Continuous aggregate |
| Aggregated (daily rollup, 10 brands, 1 year) | ~3,650 rows | 100-200ms | Continuous aggregate + index |
| Aggregated (monthly rollup, 50 brands, 2 years) | ~1,200 rows | 100-200ms | Continuous aggregate |
| Raw transactions (filtered, 1 brand, 30 days) | ~5,000 rows | 200-400ms | Index + LIMIT |
| Raw transactions (filtered, 10 brands, 1 year) | ~50,000+ rows | >500ms or reject | Must use aggregation |
| Full table scan (no filters) | 10M rows | >5s or timeout | Not allowed |

**TimescaleDB continuous aggregates are the key:**

```sql
-- Pre-compute daily brand/category/geography aggregations
CREATE MATERIALIZED VIEW daily_transactions
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', transaction_timestamp) AS day,
    brand,
    category,
    geo_state,
    customer_generation,
    customer_income_band,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount
FROM transactions
GROUP BY 1, 2, 3, 4, 5, 6;
```

**When this query runs:**
```sql
SELECT day, brand, total_amount, transaction_count
FROM daily_transactions
WHERE brand IN ('Chipotle', 'Taco Bell')
  AND day BETWEEN '2024-01-01' AND '2024-12-31'
```

It hits the materialized view (pre-computed, not raw table). Response time: ~50-100ms.

**Caching strategy (optional enhancement):**

For frequently-run queries (same brand + same time range), add a Redis cache:

```python
cache_key = f"query:{tool}:{hash(dimensions)}"
cached_result = redis.get(cache_key)
if cached_result:
    return cached_result

result = await repo.execute(tool, dimensions)
redis.setex(cache_key, ttl=300, value=result)  # 5-minute TTL
return result
```

**TTL strategy:** Use shorter TTL (5 minutes) for recent data, longer TTL (1 hour) for older/historical data. Mark cache with `data_as_of` timestamp.

**What CANNOT meet the SLA without caching:**
- Raw row queries at 10M scale (no aggregation) — always slow
- Complex multi-dimension queries without continuous aggregates
- Queries without at least one high-cardinality filter (brand, category, or geography)

**Summary: The 5s SLA is achievable for aggregated queries on 10M rows through:**
1. Continuous aggregates (pre-computed rollups)
2. Proper B-tree indexes on dimension columns
3. TimescaleDB chunk exclusion for time-range queries
4. API-level query guards (required filters, result limits)
5. Connection pooling (asyncpg with 10-20 connections)

---

**Question 2: Tool Selection Scale**

> Is RAG + LLM selection tractable for 10-50 tools with 30+ dimensions each? What embedding approach is recommended?

**Answer:**

**Recommendation: Yes, RAG + LLM selection is tractable for this scale. Use a lightweight embedding model (text-embedding-3-small or similar), retrieve top-8 candidates, and let the LLM make the final selection. The retrieval step narrows the haystack; the LLM does the actual decision-making.**

**Scalability analysis:**

| Tool Count | Embedding Dimension | Retrieval Candidates | LLM Selection Cost |
|------------|--------------------|--------------------|--------------------|
| 10 tools | 256 | Top 5 | ~500 tokens |
| 25 tools | 256-512 | Top 8 | ~800 tokens |
| 50 tools | 512 | Top 8 | ~1,000 tokens |

**50 tools with 30 dimensions each is manageable** because:
1. The retrieval step filters to top-8 candidates based on query similarity
2. The LLM only sees 8 tool definitions at selection time, not all 50
3. Tool definitions are short metadata (~100-200 tokens each), not full dimension schemas

**Recommended embedding approach:**

```python
# Use text-embedding-3-small (OpenAI) or Ember (Meta) via OpenRouter
EMBEDDING_MODEL = "text-embedding-3-small"  # 256 dimensions, fast

def embed_tools(tools: list[Tool]) -> list[Embedding]:
    """Pre-compute embeddings for all tool definitions at startup."""
    embeddings = {}
    for tool in tools:
        # Combine: name + description + capabilities + example queries
        text = f"{tool.name}. {tool.description}. {' '.join(tool.capabilities)}"
        embeddings[tool.id] = embed_model.encode(text)
    return embeddings

def retrieve_candidates(query_embedding: Embedding, top_k: int = 8) -> list[Tool]:
    """Retrieve top-k similar tools using cosine similarity."""
    scores = {}
    for tool_id, tool_emb in embeddings.items():
        scores[tool_id] = cosine_similarity(query_embedding, tool_emb)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
```

**Dimension enumeration is NOT in tool definitions:** The AI/NLP SME's analysis correctly notes that dimension value enumerations (lists of brands, states) should NOT be embedded in tool definitions — they dilute the retrieval signal. Keep tool definitions as high-level capability descriptions.

**Why not fine-tuning for tool selection?**

Fine-tuning is unnecessary at 50-tool scale. RAG + LLM achieves good accuracy without the complexity of maintaining a fine-tuned model. Re-evaluate if tool count exceeds 100.

**Retrieval embedding strategy for dimension-heavy queries:**

Queries like "Show me Target's market share in grocery" contain both:
1. Intent signals: "market share" → tool selection
2. Dimension signals: "Target", "grocery" → dimension extraction

The retrieval should weight intent signals higher. One approach: embed tool descriptions with emphasis on capabilities:

```python
tool_text = f"""
Tool: {tool.name}
What it does: {tool.description}
Use for: {', '.join(tool.capabilities)}
Examples: {'; '.join(tool.example_queries)}
""".strip()
```

**RAG threshold:** Set similarity threshold at 0.75. Below this, surface a HITL clarification: "I'm not sure which analysis fits your question. Could you rephrase?"

---

**Question 3: Time Travel Queries**

> How should the synthetic data layer handle "time travel" queries (e.g., "what did the data show as of Q1 2024")?

**Answer:**

**Recommendation: "Time travel" queries depend on whether the synthetic data layer maintains historical snapshots or only point-in-time data. For Phase 1 with batch-loaded synthetic data, treat "as of Q1 2024" as equivalent to "data available for Q1 2024." Implement true time travel only if the data pipeline supports versioning/snapshots.**

**For Phase 1 (batch synthetic data):**

The dataset represents a fixed snapshot of transactions. If the dataset spans 2022-2024, a query "as of Q1 2024" returns Q1 2024 data — there is no earlier "version" of the data to query.

```python
# Query for Q1 2024
{
  "dimensions": {
    "brand": "Target",
    "period": {"start": "2024-01-01", "end": "2024-03-31"}
  },
  "aggregation": {"level": "quarterly"}
}

# "As of Q1 2024" is semantically equivalent to "data available in Q1 2024"
# Response is just Q1 2024 data
```

**If the AI pipeline asks about historical snapshots:**

The API should clarify:
```python
{
  "error": "TIME_TRAVEL_NOT_SUPPORTED",
  "message": "The dataset represents a point-in-time snapshot. 'As of Q1 2024' returns Q1 2024 data.",
  "available_data_range": {"start": "2022-01-01", "end": "2024-12-31"},
  "hint": "Try querying a specific time period instead."
}
```

**Future: True time travel with versioned data:**

If Phase 2 requires true time travel (where "as of Q1 2024" means "the dataset as it existed in Q1 2024, even if today is Q3 2024"), the implementation would be:

```sql
-- Option 1: Temporal tables (native TimescaleDB support)
-- Add valid_from / valid_to columns
ALTER TABLE transactions ADD COLUMN valid_from TIMESTAMPTZ;
ALTER TABLE transactions ADD COLUMN valid_to TIMESTAMPTZ;

-- Query "as of" a specific point in time
SELECT * FROM transactions
WHERE valid_from <= '2024-01-01' AND valid_to > '2024-01-01';

-- Option 2: Separate snapshot tables
CREATE TABLE transactions_2024q1 (...);  -- Frozen snapshot
CREATE TABLE transactions_2024q2 (...);
```

This adds significant complexity and is not recommended for Phase 1. Document it as a future enhancement.

**Handling in AI pipeline:** The dimension extraction node should recognize "as of X" phrasing and normalize it to a time range query. If the requested time is outside the available data range, return a clear error.

---

## From Data Analytics SME (data-analytics-sme)

---

**Question 1: Caching Strategy**

> Should aggregation results be cached? What's the appropriate invalidation strategy when underlying data might be considered "current" vs "historical"?

**Answer:**

**Recommendation: Yes, cache aggregation results with a tiered TTL strategy. Separate cache keys for "current" data (recent transactions) vs "historical" data (transactions older than 30 days). Invalidate based on data freshness, not just time.**

**Cache architecture:**

```python
import redis.asyncio as redis
from datetime import datetime, timedelta

class QueryCache:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def _cache_key(self, tool: str, dimensions: dict, aggregation: dict) -> str:
        # Deterministic key from query params
        import hashlib, json
        payload = json.dumps({"tool": tool, "dimensions": dimensions, "aggregation": aggregation}, sort_keys=True)
        return f"query:{tool}:{hashlib.sha256(payload).hexdigest()}"

    def _ttl_for_data_freshness(self, period_end: date) -> int:
        """TTL in seconds based on how recent the data is."""
        days_old = (date.today() - period_end).days
        if days_old <= 7:
            return 300       # 5 minutes for recent data
        elif days_old <= 30:
            return 3600     # 1 hour for last month
        else:
            return 86400     # 24 hours for historical data

    async def get(self, tool: str, dimensions: dict, aggregation: dict) -> Optional[dict]:
        key = self._cache_key(tool, dimensions, aggregation)
        result = await self.redis.get(key)
        return json.loads(result) if result else None

    async def set(self, tool: str, dimensions: dict, aggregation: dict, result: dict):
        key = self._cache_key(tool, dimensions, aggregation)
        # Extract period end from dimensions to determine TTL
        period_end = dimensions.get("period", {}).get("end", date.today())
        ttl = self._ttl_for_data_freshness(period_end)
        await self.redis.setex(key, ttl, json.dumps(result))
```

**Cache invalidation strategy:**

| Data Type | TTL | Invalidation Trigger |
|-----------|-----|---------------------|
| Real-time / last 7 days | 5 minutes | Time-based expiry only |
| Recent / 8-30 days | 1 hour | Time-based expiry only |
| Historical / >30 days | 24 hours | Time-based expiry only |
| Pre-computed aggregates | 5 minutes | Refreshed by continuous aggregate policy |

**"Current" vs "historical" boundary:** Define "current" as the most recent completed data point (typically yesterday for daily data). Data before "current" is "historical" and changes never — it is frozen. Only "current" data may be updated.

**Do NOT invalidate cache on every new transaction ingestion.** The synthetic data is batch-loaded daily at most. Invalidation on write would be wasted effort.

**Cache warming (optional):** On application startup, pre-populate cache with common queries (top 10 brands, last 7 days). This reduces cold-start latency.

**Cache bypass:** The API should support `Cache-Control: no-cache` header for clients that explicitly want fresh data.

---

**Question 2: Real-Time Data Expectations**

> Is any component expected to show real-time or near-real-time data, or is all data effectively batch-loaded synthetic data?

**Answer:**

**Recommendation: Phase 1 uses batch-loaded synthetic data with no real-time component. All data is effectively "yesterday's snapshot" refreshed daily. If real-time is required in future phases, it would require a separate streaming ingestion pipeline.**

**Current architecture:**

```
Synthetic Data Generator (Python/Faker)
           │
           ▼ (daily batch load)
      TimescaleDB
           │
           ◄── Query API (FastAPI)
           │
           ▼
      Visualization
```

**What "real-time" means in Phase 1:**

| Expectation | Reality |
|-------------|---------|
| Data updates continuously | No — daily batch load |
| New transactions appear immediately | No — next day's batch |
| Real-time dashboards | No — last-24-hours summary via continuous aggregate |
| Streaming data | No — batch only |

**Near-real-time via continuous aggregates:**

TimescaleDB's continuous aggregates can refresh every 5 minutes (as configured). This gives a "near-real-time" view of the most recent data:

```sql
-- Continuous aggregate with 5-minute refresh
SELECT add_continuous_aggregate_policy(
    'daily_transactions',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '5 minutes'
);
```

**User-facing messaging:** If users ask about "latest" data, the API should indicate data freshness:

```json
{
  "data": [...],
  "meta": {
    "data_as_of": "2024-01-14T23:59:59Z",  # Last transaction in result set
    "dataset_last_refreshed": "2024-01-15T02:00:00Z",  # When data was last loaded
    "is_historical": false
  }
}
```

**For true real-time (future phase):** Would require:
1. Change Data Capture (CDC) from a live transaction source
2. Apache Kafka or similar message queue
3. Real-time ingestion into TimescaleDB (TimescaleDB supports continuous ingest)
4. WebSocket or SSE for pushing updates to frontend

This is out of scope for Phase 1.

---

**Question 3: API Pagination Approach**

> For result sets exceeding display capacity, should API return paginated results with cursor-based pagination or offset-based?

**Answer:**

**Recommendation: Use cursor-based pagination for aggregated time-series data. Offset-based pagination is acceptable for small result sets only. Cursor-based is more stable when data is refreshed.**

**Why cursor-based for this use case:**

Time-series aggregated data has a natural ordering (chronological). When new data is added (next day's batch), offset-based pagination breaks:

```python
# Page 1: rows 0-99 (Jan 1 - Apr 10)
# Page 2: rows 100-199 (Apr 11 - Aug 19)
# Page 3: rows 200-299 (Aug 20 - Dec 31)

# Next day: New Jan 1 data arrives
# Now: rows 0-99 (Jan 1 - Apr 9) — Page 1 has shifted!
```

With cursor-based pagination:

```python
# First request
POST /api/query
{
  "dimensions": {...},
  "pagination": {
    "limit": 100,
    "cursor": null  # First page
  }
}

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "2024-04-11",  # Day after last result
    "has_more": true,
    "total_records": 730
  }
}

# Next request
POST /api/query
{
  "dimensions": {...},
  "pagination": {
    "limit": 100,
    "cursor": "2024-04-11"
  }
}
```

**Cursor design for time-series:**

The cursor should be the timestamp or the composite sort key of the last row:

```python
cursor = f"{last_row.day}:{last_row.brand}"  # For multi-dimensional results
```

**When offset-based is acceptable:**

- Small tables (< 1,000 rows) where data rarely changes
- Explicit "export all" requests (user wants everything)

**API pagination parameters:**

```python
# Request
{
  "pagination": {
    "limit": 100,           # Required; max 1000
    "cursor": "2024-04-11", # Optional; null for first page
    # OR
    "offset": 0,            # Alternative to cursor
    "limit": 100
  }
}

# Response
{
  "data": [...],
  "pagination": {
    "next_cursor": "2024-04-12",
    "has_more": true,
    "total_records": null,  # Only provided if cheap to compute
    "remaining": 630
  }
}
```

**Display layer concern:** The visualization layer (ECharts) should receive aggregated results in a single page (max 1,000 rows). If a query returns more, the API should reject it with a suggestion to use aggregation. The visualization canvas cannot meaningfully render 10,000+ data points.

---

**Question 4: Multi-Tenancy Requirements**

> Should the data layer support tenant isolation, or is this a single-tenant demonstration system?

**Answer:**

**Recommendation: Design the schema for multi-tenancy but implement single-tenancy in Phase 1. Add `tenant_id` column now (nullable), add RLS policies in Phase 2 when multi-tenancy is introduced.**

**Phase 1: Single-tenant, no RLS**

```sql
-- Add tenant_id column (nullable for Phase 1)
ALTER TABLE transactions ADD COLUMN tenant_id UUID DEFAULT NULL;

-- Index for future RLS
CREATE INDEX idx_transactions_tenant ON transactions (tenant_id) WHERE tenant_id IS NOT NULL;
```

**Phase 2: Multi-tenant with row-level security**

```sql
-- Enable RLS
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Policy: Users only see their own tenant's data
CREATE POLICY tenant_isolation ON transactions
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- Set tenant context at connection time
SET app.current_tenant = 'tenant-uuid-here';
```

**Why not implement RLS in Phase 1?**

- RLS has performance overhead (~5-10% per query)
- Phase 1 is a demonstration with known users
- Multi-tenancy requirements may differ (shared database vs. schema-per-tenant vs. database-per-tenant)
- Adding the column now costs nothing; enabling RLS later is a migration, not a redesign

**API design for multi-tenancy readiness:**

```python
# Every API request includes tenant context
@router.post("/query")
async def execute_query(request: QueryRequest, tenant_id: UUID = Depends(get_tenant_from_session)):
    # Set tenant context for this request
    await pool.execute(f"SET app.current_tenant = '{tenant_id}'")

    # All queries now respect tenant isolation
    result = await repo.execute(request.tool, request.dimensions)
    return result
```

**Multi-tenant isolation models (for future decision):**

| Model | Pros | Cons |
|-------|------|------|
| Shared database + RLS | Low cost, single DB | Performance overhead, complexity |
| Schema per tenant | Good isolation | Schema migrations multiply |
| Database per tenant | Maximum isolation | High operational cost |

Recommend starting with shared database + RLS. Migrate to schema-per-tenant only if tenant count is <50 and isolation requirements are high.

**Synthetic data and multi-tenancy:** If the demonstration shows multiple tenants (e.g., "Demo for Acme Corp vs. Demo for Beta Inc"), each tenant sees a different data slice. This requires RLS to be enabled even in the demo phase.

---

## Summary

The integration engineering requirements for Proteus resolve around these core decisions:

1. **API design:** Hybrid unified query endpoint with tool-scoped routing; batch endpoint for multi-tool queries; dimension enumeration endpoints cached in-memory
2. **TimescaleDB:** Time-based hypertable partitioning with daily chunks; composite indexes on (dimension, timestamp); continuous aggregates for pre-computed rollups
3. **Performance:** 500ms SLA achievable via continuous aggregates + indexing + query guards; caching provides additional headroom
4. **Error handling:** Structured error codes mapped to specific UI treatments; never leak raw exceptions
5. **Multi-tenancy:** Schema-ready with nullable tenant_id; RLS deferred to Phase 2
6. **Brand normalization:** At ingestion, not query time; API validates against cached enumeration

These foundations support Phase 1 demonstration while preserving a clear migration path for multi-tenancy, real-time data, and expanded analytical capabilities.
