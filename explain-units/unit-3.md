# Unit 3: ASP.NET Core Data API

> **Status:** Implemented
> **FR Coverage:** FR-4.1, FR-4.2, FR-4.3, FR-4.4, FR-4.5, FR-4.6, FR-4.7
> **Dependencies:** IU-1 (Database Infrastructure)

## Overview

Unit 3 is the data access layer for the Proteus system — a REST API built with ASP.NET Core (.NET 10) that sits between the AI agent backend and the TimescaleDB database. It provides structured query endpoints that the LangGraph agent (Unit 7) will use to retrieve consumer spending data, along with dimension enumeration endpoints that downstream units (Tool Registry, Dimension Extraction, OpenRouter Integration) depend on for understanding the available filter values.

The API follows a minimal API pattern with Dapper and Npgsql for high-performance database access. It enforces query guardrails to prevent expensive full-table scans, auto-resolves aggregation levels based on time ranges, and returns structured error responses with request tracing. Dimension values are loaded from static YAML configuration files and cached in-memory, avoiding unnecessary database queries for metadata lookups.

This unit is a critical dependency in the architecture — Units 4, 5, and 6 (the AI foundation layer) all depend on the API contracts and dimension enumerations defined here.

## Functionality Implemented

**Query Endpoints**
- **Unified Query Endpoint** (FR-4.1) — `POST /api/query` accepting tool name, dimension filters, aggregation config, and pagination
- **Batch Query Endpoint** (FR-4.2) — `POST /api/query/batch` executing multiple tool queries in parallel with per-query latency tracking

**Query Safety**
- **Query Guardrails** (FR-4.3) — Validates that queries include at least one high-cardinality filter (1-50 brands, 1-10 categories, 1-20 geographies, or 90+ day time range); enforces 1,000 row limit
- **Auto-Aggregation** (FR-4.4) — Resolves `"auto"` aggregation level based on time range: daily (1-14d), weekly (15-90d), monthly (91-365d), quarterly (1-2y), annual (2+y)

**Data Access**
- **Repository Pattern** (FR-4.5) — `IQueryRepository` interface with `QueryRepository` implementation using Dapper + Npgsql against TimescaleDB
- **Dimension Enumeration** (FR-4.6) — `GET /api/dimensions/{dimension}` for 8 dimension types (brands, categories, states, generations, income-bands, channels, day-of-week, payment-networks) with canonical names and aliases

**Error Handling**
- **Structured Errors** (FR-4.7) — Machine-readable error codes (`INSUFFICIENT_FILTERS`, `INVALID_DIMENSION_VALUE`, `QUERY_TIMEOUT`, `RATE_LIMIT_EXCEEDED`, `DATABASE_UNAVAILABLE`, `INTERNAL_ERROR`), UUID request_id injection via middleware, no leaked stack traces

## Implementation Details

**Technology stack:** ASP.NET Core minimal API on .NET 10, Dapper micro-ORM for SQL mapping, Npgsql for PostgreSQL/TimescaleDB connectivity, YamlDotNet for dimension configuration parsing, xUnit for testing.

**Architectural patterns:**
- **Minimal API** — Endpoints registered directly on `WebApplication` via `MapPost`/`MapGet` rather than controllers, keeping the API lightweight
- **Repository pattern** — `IQueryRepository` abstracts database access so the data store can be swapped without changing endpoint code
- **Middleware pipeline** — `ErrorHandlingMiddleware` wraps all requests, injecting `X-Request-ID` headers and converting exceptions to structured `ErrorResponse` objects
- **In-memory dimension cache** — `DimensionCacheService` loads all YAML dimension files at startup with a 24-hour TTL, serving dimension lookups without database queries

**Key design decisions:**
- Dimension values are stored as YAML files (`api/config/dimensions/*.yaml`) rather than queried from the database, ensuring fast startup and zero database dependency for metadata
- Query guardrails are implemented as a dedicated validator class (`QueryGuardrailValidator`) that runs before query execution, returning 400 errors early
- The aggregation resolver uses a simple switch expression on day count, making the auto-selection logic transparent and testable
- Batch queries execute via `Task.WhenAll` for true parallel execution, with `TotalExecutionTimeMs` reflecting wall-clock time (max of individual latencies)

## Key Files

| File | Purpose |
|------|---------|
| `api/Models/QueryModels.cs` | Request/response models: `QueryRequest`, `QueryResponse`, `Dimensions`, `AggregationConfig`, `PaginationConfig`, `QueryMetadata` |
| `api/Models/ErrorResponse.cs` | `ErrorResponse` model with error codes, request_id, suggestions, retry_after |
| `api/Endpoints/QueryEndpoint.cs` | `POST /api/query` — single tool query execution with guardrail validation |
| `api/Endpoints/BatchQueryEndpoint.cs` | `POST /api/query/batch` — parallel multi-tool query execution |
| `api/Endpoints/DimensionEndpoints.cs` | `GET /api/dimensions/{dimension}` — cached dimension enumeration |
| `api/Repositories/IQueryRepository.cs` | Repository interface for database query abstraction |
| `api/Repositories/QueryRepository.cs` | TimescaleDB implementation using Dapper + Npgsql |
| `api/Validators/QueryGuardrails.cs` | High-cardinality filter validation and row limit enforcement |
| `api/Services/AggregationLevelResolver.cs` | Auto-aggregation level selection based on time range |
| `api/Services/DimensionCacheService.cs` | YAML-based dimension value loading and in-memory caching |
| `api/Middleware/ErrorHandlingMiddleware.cs` | Request_id injection, exception-to-error mapping, structured error responses |
| `api/Program.cs` | Application entry point, service registration, middleware/endpoint wiring |
| `api/config/dimensions/*.yaml` | Static dimension configuration files (brands, categories, states, etc.) |
| `api/Tests/QueryGuardrailsTests.cs` | 197-line test suite for guardrail validation rules |
| `api/Tests/AggregationLevelResolverTests.cs` | Tests for auto-aggregation level resolution |
| `api/Tests/QueryModelsTests.cs` | Tests for request/response model serialization |
| `api/Tests/BatchQueryTests.cs` | Tests for batch query execution |
| `api/Tests/DimensionValueTests.cs` | Tests for dimension enumeration |
| `api/Tests/ErrorResponseTests.cs` | Tests for error response formatting |

## Integration Points

### This Unit Provides

- **`POST /api/query`** — Primary query endpoint consumed by the LangGraph agent (IU-7) for executing data retrieval tools
- **`POST /api/query/batch`** — Batch endpoint for multi-tool queries, used when the agent needs to compare multiple data slices
- **`GET /api/dimensions/{dimension}`** — Dimension enumeration used by:
  - IU-4 (Tool Registry) for understanding available filter values
  - IU-5 (Dimension Extraction) for validating extracted dimension values against canonical lists
  - IU-9, IU-10 (Frontend) for populating filter dropdowns and chart labels
- **C# model contracts** (`QueryRequest`, `QueryResponse`, `DimensionValue`, `ErrorResponse`) — Shared types that downstream units code against

### This Unit Depends On

- **IU-1 (Database Infrastructure)** — TimescaleDB schema with `transactions` hypertable, continuous aggregates, and dimension reference tables
- **PostgreSQL connection** — Via `ConnectionStrings__DefaultConnection` environment variable or `appsettings.json`
- **YAML dimension files** — Static configuration in `api/config/dimensions/` (self-contained within this unit)

## Usage Guide

### Running the API

```bash
# From the project root
cd api && dotnet run

# Or with a specific port
ASPNETCORE_URLS="http://0.0.0.0:5000" dotnet run --project api

# Via the workmux start script
./scripts/start-api
```

The API starts on the port configured in `API_PORT` (default varies by environment).

### Querying Data

**Single query:**
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "market_share_trend",
    "dimensions": {
      "brands": ["Walmart", "Target"]
    },
    "aggregation": {"level": "auto", "metric": "sum", "period": {"start": "2024-01-01", "end": "2024-06-30"}},
    "pagination": {"limit": 100}
  }'
```

**Batch query:**
```bash
curl -X POST http://localhost:5000/api/query/batch \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      {"tool": "market_share_trend", "dimensions": {"brands": ["Walmart"]}, "aggregation": {"level": "monthly", "metric": "sum", "period": {"start": "2024-01-01", "end": "2024-06-30"}}, "pagination": {"limit": 50}},
      {"tool": "brand_comparison", "dimensions": {"brands": ["Target", "Costco"]}, "aggregation": {"level": "monthly", "metric": "avg", "period": {"start": "2024-01-01", "end": "2024-06-30"}}, "pagination": {"limit": 50}}
    ]
  }'
```

**Dimension enumeration:**
```bash
curl http://localhost:5000/api/dimensions/brands
curl http://localhost:5000/api/dimensions/generations
curl http://localhost:5000/api/dimensions/income-bands
```

### Running Tests

```bash
cd api && dotnet test --verbosity normal
```

48 unit tests covering guardrails, aggregation, models, batch queries, dimensions, and error responses.

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ConnectionStrings__DefaultConnection` | PostgreSQL/TimescaleDB connection string | From `appsettings.json` |
| `ASPNETCORE_URLS` | Listen address and port | `http://0.0.0.0:5000` |
| `API_PORT` | Port (used by start scripts) | Varies by environment |

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `97d0155` | 2026-03-28 | feat: implement Unit 3 ASP.NET Core Data API |
| `0f38e2c` | 2026-03-27 | feat: add workmux support for api (ASP.NET Core) project |
| `aeeb755` | 2026-03-26 | feat: add ASP.NET Core Web API container with Dapper + Npgsql |
