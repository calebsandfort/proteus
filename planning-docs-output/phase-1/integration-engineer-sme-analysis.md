# Integration Engineer SME Analysis: Proteus

## Critical Architecture Conflict (Must Resolve First)

**The HLRD specifies ASP.NET Core for the Data Retrieval API, but the established tech stack (AGENTS.md) specifies FastAPI (Python) as the backend, with a clear separation that it handles AI/ML only.**

This is not a minor inconsistency. It affects:
- Container orchestration (currently: Next.js frontend, FastAPI backend, TimescaleDB)
- Network topology (FastAPI is internal, not browser-exposed)
- Database access patterns (Drizzle ORM in frontend for auth tables)

**The established stack has no provision for a standalone ASP.NET Core service.** If the goal is to demonstrate a C# data API, the project requires a fourth container (C# API service) and a major revision to the Docker Compose architecture.

**Recommendation**: Resolve this conflict before proceeding. If demonstrating C# proficiency is essential, add an ASP.NET Core container to Docker Compose and establish a clear network path: FastAPI → ASP.NET Core → TimescaleDB. If the FastAPI stack is the constraint, the data API should be implemented as Python/FastAPI endpoints within the existing backend container.

---

## Question 1: API Contract Design — Tool-Specific vs. Generic Endpoints

### Direct Answer

**Recommendation: Hybrid approach with a unified query endpoint and tool-scoped route handlers.**

The HLRD describes 10-50 tools with 30+ dimensions each. A purely tool-specific approach (one endpoint per tool) creates maintenance sprawl and makes cross-tool query composition impossible. A purely generic approach (single endpoint with a flexible `query` parameter) loses type safety and makes documentation, validation, and client generation difficult.

### Design Pattern: Unified Query Endpoint with Tool Router

```typescript
// Unified query endpoint
POST /api/query
{
  "tool": "market_share_comparison",
  "dimensions": {
    "brand": ["Chipotle", "Taco Bell"],
    "geo": "TX",
    "period": "Q3"
  },
  "aggregation": {
    "level": "monthly",
    "metric": "transaction_volume"
  },
  "pagination": {
    "limit": 100,
    "offset": 0
  }
}
```

### Tradeoff Analysis

| Approach | Pros | Cons |
|----------|------|------|
| **Tool-specific endpoints** (`/tools/market-share`, `/tools/cross-shopping`) | Clear documentation per capability; type-safe request/response per tool; natural mapping from tool registry to API; easy to add per-tool validation | Proliferation of endpoints; difficult to compose multi-tool queries; inconsistent parameter naming across endpoints; hard to maintain 50+ distinct contract definitions |
| **Single generic endpoint** (`/query` with tool/dimensions params) | Single contract to maintain; flexible composition; easier to add new tools (just schema updates); simpler client SDK surface | Loses type safety; documentation becomes complex; validation logic becomes a monolith; harder to version per capability |
| **Hybrid (recommended)** | Best of both: type-safe per-tool schemas with unified routing; tools can compose via shared dimension vocabulary; easy to add new tools by adding schema definitions; maintains API contract clarity | Slightly more complex routing logic; requires disciplined schema management |

### Implementation Recommendation (Assuming FastAPI Stack)

Given the established tech stack uses FastAPI, implement the data retrieval API within the existing backend container as FastAPI endpoints. The repository/adapter pattern mentioned in the HLRD maps directly to FastAPI's dependency injection system:

```python
# Example structure within backend/src/api/
from abc import ABC, abstractmethod
from typing import Protocol

class QueryRepository(Protocol):
    async def execute(self, tool: str, dimensions: dict, aggregation: dict) -> list[dict]: ...

class TimescaleRepository:
    async def execute(self, tool: str, dimensions: dict, aggregation: dict) -> list[dict]:
        # Build parameterized SQL from tool + dimensions
        # Route to appropriate hypertable or continuous aggregate
        pass

# FastAPI endpoint
@router.post("/query")
async def execute_query(request: QueryRequest, repo: TimescaleRepository = Depends()):
    validated = validate_tool_and_dimensions(request.tool, request.dimensions)
    return await repo.execute(validated.tool, validated.dimensions, validated.aggregation)
```

### Security Analysis

- **Tenant isolation**: With TimescaleDB as the single database, row-level security (RLS) policies should enforce tenant context on all queries
- **Query guardrails**: The HLRD mentions "required dimension filters to prevent full-table scans" — implement these as validation rules at the API layer (e.g., reject queries without at least one of: brand, category, geo, or time range)
- **Rate limiting**: ASP.NET Core middleware or FastAPI middleware (`slowapi`) to limit queries per session
- **Input validation**: Pydantic models (FastAPI) or Zod schemas (if keeping TypeScript validation at the Next.js proxy layer) must validate all dimension values against enumerated lists

### Performance Implications

- **Connection pooling**: TimescaleDB connection pool via `asyncpg` (Python) or `pg` (Node.js). Pool size should be tuned for concurrent query load — typically 10-20 connections for a dev environment
- **Query performance**: With 10M+ transactions and TimescaleDB hypertable partitioning on `transaction_timestamp`, time-range queries will use chunk exclusion. Continuous aggregates pre-compute daily/weekly/monthly rollups, reducing query-time aggregation
- **Target**: API responds in under 500ms (per HLRD constraint). With proper indexing on dimension columns (brand, category, geo) and continuous aggregates, this is achievable for aggregated queries. Raw row retrieval at 10M scale would not meet this target without aggressive pagination limits.

---

## Question 2: Aggregation-Level Flexibility

### Direct Answer

**Recommendation: Aggregation level should be a request parameter, not separate endpoints. The API should auto-select the appropriate aggregation based on the time range when not explicitly specified.**

### Design Pattern: Aggregation as Dimension Parameter

```typescript
// Request
{
  "tool": "transaction_volume",
  "dimensions": {
    "brand": "Chipotle",
    "period": { "start": "2024-01-01", "end": "2024-03-31" }
  },
  "aggregation": {
    "level": "auto",  // or explicit: "daily" | "weekly" | "monthly" | "quarterly"
    "metric": "sum"   // or "count", "avg", "min", "max"
  }
}
```

### Aggregation Selection Logic

| Time Range | Suggested Default Aggregation | Rationale |
|------------|-------------------------------|-----------|
| 1-7 days | Hourly or daily | Fine-grained enough to see patterns within the range |
| 8-90 days | Daily | Balances detail vs. readability |
| 91-365 days | Weekly | Monthly would show too few data points |
| 1+ years | Monthly or quarterly | Consistent with financial reporting periods |

### Auto-Aggregation Rules

```python
def select_aggregation_level(period_start: date, period_end: date) -> str:
    days = (period_end - period_start).days
    if days <= 7:
        return "hourly"  # if data supports it
    elif days <= 90:
        return "daily"
    elif days <= 365:
        return "weekly"
    else:
        return "monthly"
```

### Why Not Separate Endpoints?

- **Consistency**: A single `transaction_volume` tool with `aggregation_level` parameter maintains tool identity regardless of output granularity
- **Client simplicity**: One API contract, one SDK method, one documentation page
- **Extensibility**: Adding new aggregation levels (e.g., "quarterly") requires only a new value in an enum, not a new endpoint
- **Multi-tool composition**: When combining multiple tools in a single query, consistent aggregation parameters prevent mismatched time buckets

### Continuous Aggregate Strategy (TimescaleDB)

TimescaleDB continuous aggregates should be created for each common rollup combination:

```sql
-- Daily totals by brand and category
CREATE MATERIALIZED VIEW daily_brand_category_totals
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 day', transaction_timestamp) AS day,
  brand,
  category,
  COUNT(*) AS transaction_count,
  SUM(amount) AS total_amount,
  AVG(amount) AS avg_amount
FROM transactions
GROUP BY day, brand, category;

-- Weekly rollup
CREATE MATERIALIZED VIEW weekly_brand_category_totals
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('7 days', transaction_timestamp) AS week,
  brand,
  category,
  COUNT(*) AS transaction_count,
  SUM(amount) AS total_amount,
  AVG(amount) AS avg_amount
FROM transactions
GROUP BY week, brand, category;
```

**Benefit**: Queries for daily/weekly/monthly aggregates hit pre-computed views instead of scanning the raw hypertable. This is critical for achieving the 500ms response time target with 10M+ rows.

---

## Architectural Recommendations

### 1. API Layer Location

Given the established FastAPI stack, the data retrieval API should be implemented as FastAPI routes within the existing backend container:

```
frontend (Next.js) → /api/copilotkit → FastAPI (AI pipeline)
                                        └── /api/query → TimescaleDB
```

This keeps the three-container architecture but adds query routes to FastAPI alongside the CopilotKit agent endpoint. The alternative (adding ASP.NET Core as a fourth service) requires Docker Compose redesign and is only justified if the goal is explicitly to demonstrate C#/.NET proficiency.

### 2. Repository Pattern for Database Migration

The HLRD mentions "clean repository/adapter patterns for future database migration without contract changes." Implement this in FastAPI using dependency injection:

```python
from typing import Protocol

class TransactionRepository(Protocol):
    async def get_transaction_volume(
        self, brand: str, period: tuple[date, date], aggregation: str
    ) -> list[dict]: ...

    async def get_market_share(
        self, brands: list[str], geo: str, period: tuple[date, date]
    ) -> list[dict]: ...

class TimescaleTransactionRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_transaction_volume(self, brand, period, aggregation):
        # Implementation using raw SQL via asyncpg
        pass

# Future migration to a different DB:
class PostgreSQLTransactionRepository:
    """Alternative implementation for standard PostgreSQL."""
    pass
```

The API contract (request/response models) never changes; only the repository implementation changes.

### 3. TimescaleDB Schema Design

```sql
-- Hypertable partitioning on timestamp
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_timestamp TIMESTAMPTZ NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    amount NUMERIC(10, 2) NOT NULL,
    quantity INTEGER,
    geo_state TEXT,
    geo_metro TEXT,
    geo_zip TEXT,
    customer_generation TEXT,  -- Gen Z, Millennial, etc.
    customer_income_band TEXT,
    card_type TEXT,  -- credit, debit
    channel TEXT,  -- online, in-store
    INDEX idx_transactions_brand (brand),
    INDEX idx_transactions_category (category),
    INDEX idx_transactions_geo (geo_state, geo_metro)
);

SELECT create_hypertable('transactions', 'transaction_timestamp');

-- Add RLS policies for multi-tenancy readiness (future)
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
```

### 4. Error Handling Strategy

The API must handle failure modes gracefully:

| Failure Mode | Handling |
|--------------|----------|
| Missing required dimension | Return 400 with clear message listing missing fields |
| Invalid dimension value | Return 400 with allowed values listed (e.g., `"brand"` must be one of: ...) |
| Query timeout (500ms exceeded) | Return 504 with partial results if available, or retry with reduced scope |
| Database connection failure | Return 503 and trigger circuit breaker |
| Rate limit exceeded | Return 429 with `Retry-After` header |
| Dimension conflict (e.g., contradictory time ranges) | Return 400 with specific conflict identified |

### 5. API Versioning Strategy

For future extensibility without breaking existing tool definitions:

```
/api/v1/query  # Current version
/api/v2/query  # Future: added dimensions, changed aggregation semantics
```

V1 remains stable; new tools or dimension vocabularies can be added to V2 while the AI pipeline can support both.

---

## Questions for Other SMEs

### For AIWorkflow SME:

**How does the tool selection pipeline determine which aggregation level to request from the API?** If the user asks "What were Target's sales last quarter?" the pipeline must decide whether to request daily, weekly, or monthly aggregates. Does this decision happen during dimension extraction or during tool selection? Should the AI pipeline be aware of aggregation level at all, or should it always request `aggregation: "auto"` and let the API decide?

**What is the expected network path from FastAPI to the data API?** If the data API is ASP.NET Core (per HLRD) vs. FastAPI endpoints (per established stack), the pipeline's call pattern differs. Is the pipeline making HTTP calls to an external API, or calling internal service methods?

### For DataScientist SME:

**What aggregation granularities should continuous aggregates pre-compute?** Daily, weekly, monthly, and quarterly are obvious candidates, but should we also consider:
- Hourly aggregates for real-time dashboards?
- Year-over-year comparisons (annualized)?
- Running totals (cumulative sum)?

**What derived metrics should the API pre-compute?** Beyond `SUM`, `COUNT`, `AVG` on transaction amounts:
- Market share percentages (per brand within category)
- Year-over-year growth rates
- Category mix percentages (percentage of total spend within category)

### For UXDesigner SME:

**What is the expected behavior when a query returns no data?** Should the API return an empty array (and the UI show "No results found for...") or return a specific "zero-state" response? How should the visualization layer handle empty result sets — show an empty chart or a placeholder message?

### For MarketAnalyst SME:

**What are the canonical time period definitions?** "Last quarter" might mean:
- Calendar quarter (Q1 = Jan-Mar, Q2 = Apr-Jun, etc.)
- Rolling quarter (prior 90 days)
- Most recently completed 13-week period

The API needs a single source of truth for period normalization, and this affects how dimension extraction normalizes relative dates.

---

## Summary of Key Decisions

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| API contract style | Hybrid: unified query endpoint with tool-scoped routing | Balances type safety with flexibility; maintains tool identity |
| Aggregation handling | Parameter-based with auto-selection | Single endpoint; scales to new aggregation levels without versioning |
| API location | FastAPI endpoints within existing backend container (per established stack) | Avoids adding fourth container; ASP.NET Core only if C# demonstration is mandatory |
| Database pattern | Repository/adapter with dependency injection | Supports future migration without contract changes |
| Query guardrails | Required dimension filters validated at API layer | Prevents full-table scans; required for 500ms SLA |
| Continuous aggregates | Pre-compute daily/weekly/monthly rollups | Critical for query performance at 10M+ row scale |
| Error handling | Structured 4xx/5xx with specific messages | Enables AI pipeline to handle errors gracefully |

---

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **ASP.NET Core vs. FastAPI conflict unresolved** | Critical | Must be decided before architecture is finalized. Impacts Docker Compose, network topology, and team skill alignment |
| **10M rows degrades query performance** | High | Continuous aggregates, proper indexing, aggressive pagination limits (max 1000 rows per query unless specifically requesting summary data) |
| **Tool proliferation creates API surface sprawl** | Medium | Tool registry should generate API contracts; avoid manual per-tool endpoint creation |
| **Ambiguous aggregation leads to inconsistent results** | Medium | Explicit `aggregation` parameter required; `auto` only applies standard rules, never infers user intent |
| **No multi-tenancy in Phase 1 limits future scaling** | Low | Schema designed with `tenant_id` column (nullable for Phase 1); RLS policies added when multi-tenancy is introduced |
