# Proteus Requirements Draft
# Phase 3: Requirements Synthesis

**Document Version:** 1.0 (Draft)
**Date:** 2026-03-27
**Status:** Draft for SME Review

---

## Project Goal

Proteus is a natural-language chat interface that enables analysts and investors to query consumer transaction data through conversation. Users ask questions in plain English and the system translates them into structured tool calls against a parameterized REST API, returning formatted results with interactive visualizations.

**Success Criteria:**
- Natural language queries are routed to the correct tool with ≥90% accuracy on the eval suite
- Dimensional parameters are extracted correctly with ≥85% accuracy across all dimension categories
- Query-to-visualization round-trip completes in under 5 seconds for typical queries
- The system gracefully handles ambiguous queries by requesting clarification rather than returning incorrect results
- Multi-turn conversations maintain context and allow meaningful follow-up queries
- An interviewer or reviewer can understand the system's architecture and trace a query from natural language input to visualized output

---

## FR-1: Conversational Query Interface

The system **SHALL** provide a chat-based interface that enables natural language querying of consumer transaction data.

### FR-1.1: Layout and Structure

- The system **SHALL** display a CopilotKit ChatSidebar component pinned to the right side of the screen at a width of 380-420px
- The system **SHALL** display the main visualization canvas in the remaining left area
- The system **SHALL** render charts, tables, and analytical results in the main canvas area synchronized with the active conversation
- The system **SHALL** maintain conversation history per session with persistence for later reference

### FR-1.2: Multi-Turn Conversation

- The system **SHALL** support multi-turn conversations enabling follow-up questions, query refinement, and references to prior results within a session
- The system **SHALL** maintain 6-8 conversation turns as the primary context window
- The system **SHALL** preserve the first query in a session as a "session anchor" that is always available
- The system **SHALL** tag each tool result with an internal reference ID for resolution of references like "that" or "those results"
- When a user switches to a new analytical topic (different brand/category), the system **SHALL** treat this as a new session context

### FR-1.3: Observability Panel

- The observability panel **SHALL** default to hidden (off by default)
- The system **SHALL** provide a persistent toggle control in the chat interface header area
- The toggle state **SHALL** persist across sessions via localStorage
- When toggled ON, chat messages **SHALL** gain subtle expand icons in the corner
- Clicking expand **SHALL** show an inline JSON viewer with syntax highlighting

### FR-1.4: Observability Progressive Disclosure (3-Level)

- **Level 0 (Default):** Clean chat + visualization. No instrumentation visible
- **Level 1 (Toggle On):** Chat messages gain expand icons; header shows active state; displays selected tool(s), extracted dimensions, and latency per stage
- **Level 2 (Expanded Message):** Inline JSON viewer with syntax highlighting showing top-3 RAG candidates with similarity scores
- **Level 3 (Raw Response):** Full API request/response accessible via explicit "Show raw" action

### FR-1.5: Model Selector

- The system **SHALL** display a model selector dropdown in the header bar
- The dropdown **SHALL** display model names and provider logos
- The selector **SHALL** show the current selection prominently
- Changes **SHALL** apply to subsequent queries within the session

### FR-1.6: Loading and Feedback States

- For queries taking under 2 seconds, no additional feedback beyond disabled input state
- For queries taking 2-5 seconds, the system **SHALL** display a stage indicator
- For queries taking over 5 seconds, the system **SHALL** show a timeout warning with option to cancel
- The system **SHALL** display skeleton loaders with shimmer animation during visualization rendering

### FR-1.7: Error Handling

- For ambiguous queries requiring HITL clarification, the system **SHALL** present inline clarification cards within the chat stream (NOT modals)
- The input **SHALL** remain active and usable during clarification
- Clarification options **SHALL** be limited to a maximum of 3 options
- The original query **SHALL** remain visible above the clarification

---

## FR-2: Intelligent Tool Selection

The system **SHALL** maintain a registry of data retrieval tools and select the appropriate tool(s) for each user query.

### FR-2.1: Tool Registry

- The system **SHALL** maintain a registry of 12-15 core data retrieval tools
- Tool definitions **SHALL** include: id, name, description, capabilities, dimensions (required and optional), example queries, output schema, and aliases
- Tool definitions **SHALL** be stored as embeddings for semantic retrieval
- Tools **SHALL** be addable, modifiable, or deprecated without pipeline changes

### FR-2.2: Core Tool Set (Priority Order)

The system **SHALL** implement the following tools as P0 (Must Have):

1. **market_share_trend** — Brand-vs-brand market share, category-wide share breakdown, share trend over time
2. **brand_comparison** — Direct Brand X vs. Brand Y analysis
3. **yoy_growth_analysis** — Transaction volume and spend growth year-over-year
4. **category_trends** — Category-level transaction counts and dollar volumes
5. **cross_shopping_overlap** — Multi-brand purchasing patterns and customer overlap
6. **demographic_breakdown** — Spending distribution by generation, income, age
7. **geographic_breakdown** — State/CBSA/regional spending patterns
8. **top_n_rankings** — Brand rankings by various metrics

### FR-2.3: RAG-Based Tool Retrieval

- The system **SHALL** use text-embedding-3-small or ember embedding model via OpenRouter
- The system **SHALL** retrieve top-8 candidate tools based on semantic similarity
- The RAG similarity threshold **SHALL** be set at 0.75
- Candidates below 0.70 similarity **SHALL** trigger HITL clarification
- Tool definitions **SHALL NOT** include dimension value enumerations (lists of brands, states) as these dilute retrieval signal

### FR-2.4: Tool Selection LLM

- The system **SHALL** use MiniMax-Text-01 for tool selection via OpenRouter
- The LLM **SHALL** select the best-matching tool(s) from the narrowed candidates
- Tool selection confidence **SHALL** be computed as a weighted combination:
  - 25% RAG similarity score
  - 35% LLM selection score
  - 40% dimension match score
- Confidence thresholds **SHALL** be:
  - ≥0.85: Proceed with selected tool
  - 0.70-0.84: Proceed but show competing candidates in observability panel
  - <0.70: Route to HITL clarification

### FR-2.5: HITL Clarification

- When confidence is below threshold, the system **SHALL** generate a structured clarification response
- The clarification **SHALL** include the interpreted parameters for each option
- The clarification **SHALL** provide a suggested follow-up question
- The system **SHALL** limit clarification options to 2-3 maximum

### FR-2.6: Multi-Tool Query Handling (Planner Node)

- The system **SHALL** implement a dedicated planner node upstream of tool selection
- The planner **SHALL** detect whether a query requires single-tool or multi-tool execution
- For multi-tool queries, the planner **SHALL** output a structured execution plan specifying tool order and parameters
- Multi-tool queries **SHALL** execute in parallel with results synthesized by a result synthesizer
- The planner **SHALL** use GLM-4-Air via OpenRouter for planning decisions

---

## FR-3: Dimension Extraction Pipeline

The system **SHALL** extract dimensional parameters from user queries using parallel, category-specialized extraction nodes.

### FR-3.1: Dimension Categories

The system **SHALL** extract parameters for the following dimension categories:
- **brand/merchant**: Brand names with fuzzy matching and alias resolution
- **merchant_category**: Category names via enum lookup
- **geography**: State, CBSA, metro area, zip code with hierarchical normalization
- **time_range**: Start date, end date, period type (calendar, rolling, event-based)
- **generation**: Gen Z, Millennial, Gen X, Boomer, Silent
- **income_band**: Six income bands from <$25K to $150K+
- **card_type**: credit, debit, prepaid, corporate
- **channel**: online, in-store, mobile
- **aggregation_level**: hourly, daily, weekly, monthly, quarterly, annual, auto

### FR-3.2: Parallel Extraction Architecture

- The system **SHALL** execute dimension extraction nodes in parallel
- **Time Range Parser**: Deterministic logic for patterns like "last quarter," "Q3 2024," "YTD" — target latency 10-50ms
- **Geography Normalizer**: State abbreviations, metro name resolution, zip-to-region mapping
- **Brand Matcher**: LLM + fuzzy matching for aliases, misspellings, parent company resolution
- **Category Lookup**: LLM + enum lookup against hierarchical category taxonomy
- **Generation/Income Parsing**: LLM with validation against enumerated values

### FR-3.3: Time Range Parsing Rules

- **Explicit wins**: "daily" → daily, "monthly" → monthly, "quarterly" → quarterly
- **Time range size defaults**:
  - ≤14 days → daily
  - 15-90 days → weekly
  - 91-365 days → monthly
  - >365 days → quarterly
- **Query intent inference**: "trend" or "over time" → prefer finer granularity; "summary" → prefer coarser
- The dimension extractor **SHALL** set `period_type` field as "calendar", "rolling", or "event_based"

### FR-3.4: Synonym and Layman Term Handling

- The system **SHALL** use LLM + lookup table hybrid for dimension value mapping
- Examples:
  - "young people" → Gen Z (confidence 0.7) with Millennial as alternative
  - "credit card" → credit (confidence 0.8) with debit as alternative
  - "fancy" → premium tier (confidence 0.8)
- Brand aliases **SHALL** be resolved via fuzzy matching (e.g., "Walmart" → Walmart)

### FR-3.5: Dimension Validation

- The system **SHALL** validate extracted dimensions against the API's dimension enumeration endpoint before constructing queries
- If an extracted value is not found in enumeration, the system **SHALL** provide suggestions based on string similarity
- The system **SHALL** reject queries missing required dimensions for the selected tool with a clarification request

### FR-3.6: Conflict Resolution

- When dimension conflicts are detected (e.g., "Target sales in TX and CA last month and last year"), the system **SHALL** surface structured disambiguation
- The system **SHALL NOT** silently generate multiple API calls or make best-effort interpretations
- Disambiguation options **SHALL** be limited to 2-3 maximum

---

## FR-4: Data Retrieval API (ASP.NET Core)

The system **SHALL** provide a REST API built in ASP.NET Core as the data access layer between the AI pipeline and the database.

### FR-4.1: API Contract Design

- The API **SHALL** implement a hybrid approach with unified query endpoint and tool-scoped routing
- The primary endpoint **SHALL** be `POST /api/query` accepting:
  ```json
  {
    "tool": "market_share_comparison",
    "dimensions": {
      "brand": ["Chipotle", "Taco Bell"],
      "geo": "TX",
      "period": {"start": "2024-01-01", "end": "2024-03-31"}
    },
    "aggregation": {
      "level": "auto",
      "metric": "sum"
    },
    "pagination": {
      "limit": 100,
      "cursor": null
    }
  }
  ```

### FR-4.2: Batch Endpoint for Multi-Tool Queries

- The API **SHALL** expose `POST /api/query/batch` for parallel multi-tool execution
- The batch endpoint **SHALL** execute queries against TimescaleDB in parallel
- The response **SHALL** include latency per constituent query

### FR-4.3: Query Guardrails

- The API **SHALL** require at least one high-cardinality dimension filter (brand, category, or geography) to prevent full-table scans
- Queries without sufficient filters **SHALL** return 400 with `INSUFFICIENT_FILTERS` error code
- Raw queries **SHALL** require a `limit` parameter with maximum of 1,000 rows

### FR-4.4: Aggregation Level Handling

- The API **SHALL** auto-select aggregation level based on time range when `level: "auto"` is specified:
  - 1-7 days → daily
  - 8-90 days → daily
  - 91-365 days → weekly
  - 1+ years → monthly
- Explicit aggregation levels **SHALL** override auto-selection

### FR-4.5: Repository Pattern

- The API **SHALL** follow clean repository/adapter patterns allowing future database migration without contract changes
- The repository abstraction **SHALL** hide data access implementation details

### FR-4.6: Dimension Enumeration Endpoints

- The API **SHALL** expose dimension enumeration endpoints cached in-memory:
  - `GET /api/dimensions/brands`
  - `GET /api/dimensions/categories`
  - `GET /api/dimensions/states`
  - `GET /api/dimensions/generations`
  - `GET /api/dimensions/income-bands`
  - `GET /api/dimensions/channels`
- These endpoints **SHALL** return canonical names plus aliases
- These endpoints **SHALL NOT** query TimescaleDB directly

### FR-4.7: Error Response Structure

- All errors **SHALL** return machine-readable error codes:
  - `MISSING_REQUIRED_DIMENSION` (400)
  - `INVALID_DIMENSION_VALUE` (400) with suggestions
  - `INSUFFICIENT_FILTERS` (400)
  - `QUERY_TIMEOUT` (504)
  - `RATE_LIMIT_EXCEEDED` (429) with Retry-After header
  - `DATABASE_UNAVAILABLE` (503)
  - `INTERNAL_ERROR` (500)
- Errors **SHALL NOT** leak raw exception messages or stack traces
- All errors **SHALL** include a `request_id` for debugging

### FR-4.8: Response Metadata

- API responses **SHALL** include metadata:
  ```json
  {
    "data": [...],
    "meta": {
      "aggregation_level": "monthly",
      "record_count": 72,
      "data_as_of": "2024-01-14T23:59:59Z",
      "dataset_last_refreshed": "2024-01-15T02:00:00Z"
    }
  }
  ```

---

## FR-5: Data Visualization

The system **SHALL** render query results as interactive charts and tables using ECharts.

### FR-5.1: Auto Chart-Type Selection

- The system **SHALL** automatically select chart type based on query pattern and result shape:
  - "average", "total", "sum" + single value → KPI Card
  - "over time", "trend", "history" → Line Chart
  - "compare", "vs", "versus" + 2-5 categories → Bar Chart
  - "share", "percentage", "proportion" → Pie/Donut Chart
  - "across", "by", "segmented" + multiple dimensions → Stacked Bar or Heatmap
  - "correlation", "relationship", "scatter" → Scatter Plot
  - "ranking", "top", "bottom" → Horizontal Bar Chart
  - "geography", "state", "region" → Choropleth Map

### FR-5.2: Manual Override

- The system **SHALL** provide a manual chart type override control
- The override dropdown **SHALL** be in the top-right corner of the visualization canvas
- Available options **SHALL** include: Auto, Table, Line, Bar (Vertical), Bar (Horizontal), Pie, Donut, Scatter
- When override differs from auto-selection, the system **SHALL** show a tooltip explaining the auto-selection reasoning

### FR-5.3: KPI Card Display

- For single aggregate values (e.g., "average Target spend"), the system **SHALL** render a KPI card instead of a chart
- The KPI card **SHALL** display: metric name, primary value, comparison to prior period, comparison to category average
- The KPI card **SHALL** include a "View as chart" toggle

### FR-5.4: Table Toggle

- The system **SHALL** provide a toggle between chart and table views
- Toggle states **SHALL** be: Chart only, Table only, Both (split view)
- For queries returning only tabular data, the system **SHALL** show table as primary

### FR-5.5: Chart Interactivity (Required)

- Charts **SHALL** support hover tooltips showing exact values
- Charts **SHALL** support legend toggling for multi-series data
- Charts **SHALL** support responsive resize

### FR-5.6: Chart Interactivity (Recommended)

- Charts **SHALL** support data zoom (slider) for time-series with 8+ quarters
- Charts **SHALL** support click-to-highlight for legend items or bars

### FR-5.7: Result Set Handling

- For 1-100 rows: Full table display
- For 101-1,000 rows: Paginated (50 rows/page) or virtual scrolling
- For 1,001-10,000 rows: Aggregated view suggested; raw data on demand
- For 10,000+ rows: Auto-aggregate with "View raw data" option

### FR-5.8: Visualization Updates

- The canvas **SHALL** update with each new query result
- Prior visualizations **SHALL** be accessible via conversation history
- The chat sidebar **SHALL** display conversation history with thumbnail previews

---

## FR-6: Synthetic Data Layer

The system **SHALL** operate on a synthetic dataset modeled on real-world consumer transaction data.

### FR-6.1: Data Volume and Timespan

- The dataset **SHALL** contain 10M+ synthetic transactions
- The dataset **SHALL** span a minimum of 2 years (2023-2024 minimum; 2019-2025 ideal)
- The dataset **SHALL** include 100-125 distinct brands across multiple tiers
- The dataset **SHALL** provide full geographic coverage (51 US states + DC)

### FR-6.2: TimescaleDB Configuration

- The transactions table **SHALL** be configured as a TimescaleDB hypertable partitioned on `transaction_timestamp`
- The hypertable **SHALL** use daily chunk intervals
- Compression **SHALL** be enabled after 30 days with gzip
- A retention policy **SHALL** drop chunks older than 7 years

### FR-6.3: Hierarchical Geography

- The geography dimension **SHALL** support hierarchical levels:
  - State (51 values) — REQUIRED
  - CBSA/Metro Area (350-400 values) — REQUIRED
  - MSA (380-400 values) — OPTIONAL
  - 3-digit ZIP (800-1000 values) — NICE-TO-HAVE
  - Urban/Suburban/Rural classification — REQUIRED

### FR-6.4: Category Taxonomy (3-Level Hierarchy)

- **Level 1 - Style Classification**: Discretionary, Consumer Staples, Services, Transportation
- **Level 2 - Spending Category**: 35-45 categories (Grocery, Restaurant, Apparel, Travel, etc.)
- **Level 3 - Merchant Group**: 200-400 subcategories

### FR-6.5: Brand Tier Classification

- Each brand **SHALL** be classified by tier: luxury, premium, mid-market, value
- Each brand **SHALL** have a category archetype: fast casual, discount retailer, department store, subscription, etc.
- Brand data **SHALL** include recognizable archetypes rather than copying real brand names exactly

### FR-6.6: Statistical Distributions

- Transaction amounts **SHALL** follow log-normal distribution with category-specific parameters:
  - Essential categories: mu=3.0, sigma=0.8
  - Mid-tier retail: mu=3.5, sigma=1.0
  - Premium: mu=4.2, sigma=1.2
  - Dining: mu=3.2, sigma=0.9
  - Fast food: mu=2.2, sigma=0.6
- Income multipliers **SHALL** affect transaction amounts: income_band 6 ($150K+) gets 1.7x multiplier vs. 0.6x for band 1 (<$25K)

### FR-6.7: Embedded Spending Patterns

- **Holiday Season (Q4)**: 25-40% retail volume increase Nov-Dec with Dec 15-24 peak at +60-100%
- **Back-to-School (Aug-Sep)**: 20-35% increase in school-related categories
- **Weekend vs. Weekday**: Saturday +30-35% vs. Monday baseline for retail
- **Generational Preferences**:
  - Gen Z: 22%+ dining/delivery, 16%+ apparel/fast fashion, high online (65%)
  - Millennials: 18%+ grocery (family), 12%+ home improvement
  - Boomers: 28%+ healthcare, 14%+ travel, 75% in-store
- **Income-Brand Correlation**: High-income ($150K+) shows 70-80% premium brand transactions; Walmart correlation with lower income is strong and visible

### FR-6.8: Continuous Aggregates

The system **SHALL** pre-compute the following continuous aggregates:

- **Daily rollups**: brand + category + geo_state + generation + income_band (90-day retention)
- **Weekly rollups**: same dimensions (2-year retention)
- **Monthly rollups**: same dimensions (7-year retention)
- **Market share %**: pre-computed per brand within category
- **YoY growth rates**: pre-computed monthly
- **Category mix %**: pre-computed daily
- **Weekly brand rankings**: by category and region

### FR-6.9: Panel Data Structure

- The synthetic data **SHALL** be structured as a consumer panel (100,000-500,000 panelists)
- Each panelist **SHALL** have: persistent ID, income_band, generation, geography, panel_start_date, panel_weight
- Each panelist **SHALL** have 50-200 transactions over 2 years
- Panelists **SHALL** shop at 3-10 different brands within a category

---

## FR-7: Eval Framework

The system **SHALL** include an evaluation suite measuring accuracy and reliability of the AI pipeline.

### FR-7.1: Eval Suite Size

- The eval suite **SHALL** contain a minimum of 200 test cases
- Test cases **SHALL** be distributed across 5 complexity levels:
  - Level 1 (Simple): 30% (60 cases) — single-tool, single-dimension
  - Level 2 (Moderate): 35% (70 cases) — single-tool, 2-4 dimensions
  - Level 3 (Complex): 15% (30 cases) — single-tool, 5+ dimensions
  - Level 4 (Multi-tool): 10% (20 cases) — planner decomposition correctness
  - Level 5 (Ambiguous): 10% (20 cases) — HITL appropriateness

### FR-7.2: Eval Dimensions and Metrics

- **Tool selection accuracy**: % correct tool(s) selected — target ≥90%
- **Dimension extraction accuracy**: % correct parameter values — target ≥85%
- **End-to-end result correctness**: Pass/fail on structured assertions — target ≥80%
- **Clarification appropriateness**: Human-rated 0-2 scale — target mean ≥1.5

### FR-7.3: Clarification Evaluation Rubric

| Score | Definition |
|-------|------------|
| 2 - Correct | System asked for clarification when appropriate; question was semantically relevant and specific |
| 1 - Partially Correct | System asked, but question was vague or missed a key ambiguity |
| 0 - Incorrect | System should not have asked OR asked for obviously wrong reason |

### FR-7.4: Test Case Structure

Each test case **SHALL** include:
- Natural language input
- Expected tool(s)
- Expected parameters
- Expected result characteristics
- Complexity level
- Synonym variations for key concepts

### FR-7.5: Anomaly Injection for Eval

- The eval framework **SHALL** include known anomalies for detection testing:
  - Seasonal patterns (holiday spikes, back-to-school)
  - One-time events (COVID-style channel shift)
  - Secular trends (online channel growth 2019-2024)

### FR-7.6: Benchmark Queries

- **Level 1**: "What is Walmart's market share in grocery?", "How much did Target grow last quarter?"
- **Level 2**: "How is McDonald's doing vs. Burger King?", "Is Starbucks gaining or losing share?"
- **Level 3**: "Why did Target's sales spike in March?", "Are Target's customers trading up or down?"

---

## FR-8: Model Configuration

The system **SHALL** use OpenRouter as a unified LLM gateway with configurable model selection.

### FR-8.1: OpenRouter Integration

- All LLM calls **SHALL** route through OpenRouter
- No direct provider API integrations **SHALL** be used
- The system **SHALL** support the following providers via OpenRouter: OpenAI, Google, Anthropic, Kimi, MiniMax, GLM

### FR-8.2: Internal Pipeline Models

- Tool selection **SHALL** use MiniMax-Text-01 via OpenRouter
- Dimension extraction **SHALL** use Kimi-Open-Assistant via OpenRouter
- Planner (multi-tool) **SHALL** use GLM-4-Air via OpenRouter
- These internal model selections **SHALL NOT** be user-configurable in Phase 1

### FR-8.3: Response Generation Model

- The response generation stage (natural-language answer + visualization decisions) **SHALL** be user-configurable
- Users **SHALL** be able to select from six providers: OpenAI, Google, Anthropic, Kimi, MiniMax, GLM
- Model selection **SHALL** be exposed in the UI as a settings control
- Changes **SHALL** apply to subsequent queries within the session

### FR-8.4: Model-Agnostic Pipeline

- The pipeline **SHALL** be model-agnostic at the integration layer
- Swapping models **SHALL** require no code changes, only configuration
- The system **SHALL** implement a provider-agnostic normalization layer for structured output

### FR-8.5: Provider Normalization

- The system **SHALL** normalize structured output across providers
- JSON mode / function calling consistency **SHALL** be achieved via adapter layer
- Parse failures **SHALL** trigger retry once with same model before returning user-friendly error

---

## NFR-1: Performance

The system **SHALL** meet the following performance requirements.

### NFR-1.1: End-to-End Latency

- Query-to-visualization round-trip **SHALL** complete in under 5 seconds for single-tool queries
- Multi-tool queries **SHALL** stream partial results as tools complete

### NFR-1.2: API Response Time

- The ASP.NET Core API **SHALL** respond to parameterized queries in under 500ms (database query time, excluding AI pipeline)
- The 500ms SLA **SHALL** apply to individual query endpoints, not batch endpoints

### NFR-1.3: Pipeline Latency Budget

| Stage | Target Latency |
|-------|---------------|
| RAG retrieval (embedding + search) | 50-100ms |
| Tool selection LLM call | 400-800ms |
| Dimension extraction (parallel) | 600-1200ms |
| API call | 200-500ms |
| Response generation | 800-1500ms |
| **Total (non-streaming)** | **2,050-4,100ms** |

### NFR-1.4: Streaming

- The system **SHALL** implement streaming for response generation via Server-Sent Events (SSE)
- First token **SHALL** appear within 500ms of pipeline completion

### NFR-1.5: Query Performance at Scale

- With 10M+ rows and continuous aggregates, aggregated queries **SHALL** achieve 200-500ms latency
- TimescaleDB chunk exclusion **SHALL** be used for time-range queries
- Raw row queries at 10M scale **SHALL NOT** be permitted without aggregation

---

## NFR-2: Architecture

The system **SHALL** demonstrate clear architectural separation.

### NFR-2.1: Container Architecture

- The system **SHALL** run via Docker Compose for development and demonstration
- The system **SHALL** consist of four containers:
  1. **Next.js (Frontend)**: React application with CopilotKit, ECharts visualization
  2. **FastAPI (AI Pipeline)**: RAG retrieval, tool selection, dimension extraction, response generation
  3. **ASP.NET Core (Data API)**: REST API for data retrieval, repository pattern
  4. **TimescaleDB**: Time-series database for synthetic transaction data

### NFR-2.2: Network Topology

```
Frontend (Next.js)
    ↓ HTTP /api/copilotkit
FastAPI (AI Pipeline)
    ↓ HTTP /api/query
ASP.NET Core (Data API)
    ↓
TimescaleDB
```

### NFR-2.3: Technology Stack

- **Frontend**: React (Next.js), CopilotKit, ECharts, TypeScript
- **AI Orchestration**: FastAPI (Python), OpenRouter, text-embedding-3-small
- **Data API**: ASP.NET Core (C#), REST endpoints
- **Database**: TimescaleDB (PostgreSQL extension)
- **Containerization**: Docker Compose

### NFR-2.4: CopilotKit Integration

- The frontend **SHALL** use CopilotKit's ChatSidebar component
- The CopilotKit agent endpoint **SHALL** be at `/api/copilotkit`
- The FastAPI backend **SHALL** handle CopilotKit agent requests

### NFR-2.5: Multi-Tenancy Readiness

- The schema **SHALL** include a nullable `tenant_id` column for future multi-tenancy
- Row-level security (RLS) policies **SHALL** be added in Phase 2 when multi-tenancy is introduced
- Phase 1 **SHALL** operate as single-tenant

---

## NFR-3: Synthetic Data Quality

The synthetic data **SHALL** exhibit statistical properties and patterns that make it analytically credible.

### NFR-3.1: Pattern Realism

- Transaction amounts **SHALL** be log-normally distributed (not normal)
- Brand market shares **SHALL** follow Zipfian/power law distribution
- Inter-transaction time **SHALL** follow exponential distribution
- Category proportions **SHALL** follow Dirichlet distribution

### NFR-3.2: Correlation Requirements

- Income-band **SHALL** correlate with brand tier selection (Pearson coefficient 0.65-0.75 for premium brands)
- Generation **SHALL** correlate with category preferences and channel preferences
- Geography **SHALL** correlate with category mix (urban: +30% dining/entertainment; rural: +25% auto/gas)
- High-income customers **SHALL NOT** heavily shop at Walmart — this correlation is strong and analysts will detect violations

### NFR-3.3: Seasonal Pattern Realism

- Q4 holiday spike **SHALL** show 25-40% retail volume increase with December peak at +60-100%
- January **SHALL** show normalization (-15-25% below Q4 average)
- Back-to-school **SHALL** show 20-35% increase in Aug-Sep for school-related categories
- Weekend vs. weekday patterns **SHALL** be embedded: Saturday +30-35% for retail

### NFR-3.4: Anti-Patterns to Avoid

- The synthetic data **SHALL NOT** exhibit uniform distribution across time (no spikes would be fake)
- The synthetic data **SHALL NOT** show identical spending profiles across generations
- The synthetic data **SHALL NOT** show identical category mixes across geographies
- The synthetic data **SHALL NOT** show zero correlation between income and brand selection
- The synthetic data **SHALL NOT** have deterministic patterns that repeat identically each year

### NFR-3.5: Data Validation Benchmarks

- Grocery spending **SHALL** be 18-25% of total spend
- Dining out **SHALL** be 10-15% of total spend
- E-commerce share of retail **SHALL** be 20-25% in 2024
- Holiday Q4 retail spike **SHALL** be +25-35% vs. Q3 average

---

## Synthesis Notes

### Resolution: ASP.NET Core vs. FastAPI for Data API

The HLRD specifies ASP.NET Core for the Data Retrieval API. The established tech stack specifies FastAPI for AI orchestration only. **Decision**: Keep ASP.NET Core as specified in HLRD for the data API. FastAPI handles AI orchestration. This maintains the four-container architecture demonstrating full-stack proficiency.

### Resolution: Tool Count

The HLRD specified "10-50 tools" which was overly broad. **Decision**: Implement 12-15 core tools prioritized by market analyst input:
- P0: market_share_trend, brand_comparison, yoy_growth_analysis, category_trends
- P1: cross_shopping_overlap, demographic_breakdown, geographic_breakdown
- P2: top_n_rankings, channel_analysis, customer_retention, basket_analysis

### Resolution: Observability Panel

Multiple SME inputs suggested different approaches (sidebar, per-message expand, slide-out panel). **Decision**: Hidden by default with persistent header toggle. When toggled ON, per-message expandable sections with 3-level progressive disclosure. This balances power-user needs without cluttering the analyst experience.

### Resolution: Aggregation

The aggregation level decision **SHALL** happen during dimension extraction, not tool selection. The API auto-selects based on time range when `level: "auto"` is specified. Domain rules (fiscal quarter boundaries, holiday-adjusted seasonality) remain at the API layer.

### Resolution: Synthetic Data Correlations

Critical correlations that must be embedded:
1. Q4 holiday spike (25-40% retail increase)
2. Generation x Category spend proportions
3. Income x Brand correlations (strong — high-income at Walmart would be detected as fake)
4. State-level geographic variation in category mix
5. Weekend/weekday patterns by category
6. Channel growth trend (online gaining share)

### Resolution: Eval Suite Size

**Decision**: Minimum 200 test cases across 5 complexity levels as specified by AI/NLP SME. This provides statistically meaningful accuracy differentiation with ±7% confidence interval.

---

## Success Criteria Checklist

- [ ] Natural language queries routed to correct tool with ≥90% accuracy
- [ ] Dimensional parameters extracted with ≥85% accuracy
- [ ] Query-to-visualization completes in under 5 seconds
- [ ] Ambiguous queries trigger HITL clarification gracefully
- [ ] Multi-turn conversations maintain context (6-8 turns)
- [ ] 12-15 core tools implemented and functional
- [ ] Eval suite with 200+ test cases operational
- [ ] 10M+ synthetic transactions with realistic patterns
- [ ] ASP.NET Core API meets 500ms SLA for aggregated queries
- [ ] Clear architectural separation demonstrated (React/FastAPI/ASP.NET Core/TimescaleDB)
- [ ] Observability panel with 3-level progressive disclosure
- [ ] Chart type auto-selection with manual override available
- [ ] Multi-tool query support via planner node
- [ ] Streaming response generation implemented
- [ ] Docker Compose deployment for local development
