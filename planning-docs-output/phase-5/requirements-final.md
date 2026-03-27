# Proteus Requirements Document
# Phase 5: Final Requirements

**Document Version:** 1.0 (Final)
**Date:** 2026-03-27
**Status:** Final - Ready for Implementation

---

## Project Goal

Proteus is a natural-language chat interface that enables analysts and investors to query consumer transaction data through conversation. Users ask questions in plain English and the system translates them into structured tool calls against a parameterized REST API, returning formatted results with interactive visualizations.

**Success Criteria:**
- Natural language queries are routed to the correct tool with >=90% accuracy on the eval suite
- Dimensional parameters are extracted correctly with >=85% accuracy across all dimension categories
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
- At viewports below 1024px width, the chat sidebar **SHALL** collapse into a slide-out drawer
- A floating action button in the bottom-right corner **SHALL** trigger the drawer
- The main visualization canvas **SHALL** fill the full width when sidebar is collapsed

### FR-1.2: Multi-Turn Conversation

- The system **SHALL** support multi-turn conversations enabling follow-up questions, query refinement, and references to prior results within a session
- The system **SHALL** maintain the most recent messages whose total token count does not exceed 75% of the current model's context window limit, with a minimum of the 4 most recent turns plus session anchor
- The system **SHALL** preserve the first query in a session as a "session anchor" that is always available
- The system **SHALL** tag each tool result with an internal reference ID for resolution of references like "that" or "those results"
- When a user switches to a new analytical topic (different brand/category), the system **SHALL** treat this as a new session context
- When context approaches 80% of model token limit, older messages **SHALL** be summarized or compressed
- Summarization **SHALL** preserve key extracted dimensions and tool selections for reference

### FR-1.3: Observability Panel

- The observability panel **SHALL** default to hidden (off by default)
- The system **SHALL** provide a persistent toggle control in the chat interface header area
- The toggle state **SHALL** persist across sessions via localStorage
- When toggled ON, chat messages **SHALL** gain subtle expand icons in the corner
- Clicking expand **SHALL** show an inline JSON viewer with syntax highlighting

### FR-1.4: Observability Progressive Disclosure (4-Level)

- **Level 0 (Default):** Clean chat + visualization. No instrumentation visible
- **Level 1 (Toggle ON):** Header shows active state; chat messages gain expand icons; displays selected tool(s), extracted dimensions, and latency per stage
- **Level 2 (Expanded Message):** Click expand icon -> inline JSON viewer showing top-3 RAG candidates with similarity scores
  - JSON viewer **SHALL** use `font-mono text-xs` styling (per design system)
  - JSON **SHALL** be formatted with collapsible tree nodes for objects/arrays beyond 3 levels
  - Maximum initial display of 20 lines with "Show more" expansion
  - Syntax highlighting **SHALL** use the design system's code colors (slate palette for keys, blue for strings, amber for numbers)
- **Level 3 (Raw Response):** Explicit "Show raw" action -> full API request/response

### FR-1.5: Model Selector

- The system **SHALL** display a model selector dropdown in the header bar
- The selector **SHALL** appear to the right of the observability toggle
- If header space is insufficient, the selector **SHALL** appear in a settings popover
- The dropdown **SHALL** display model names and provider logos
- The selector **SHALL** show the current selection prominently
- Changes **SHALL** apply to subsequent queries within the session

### FR-1.6: Loading and Feedback States

- For queries taking under 2 seconds, no additional feedback beyond disabled input state
- For queries taking 2-5 seconds, the system **SHALL** display a stage indicator
- For queries taking over 5 seconds, the system **SHALL** show a timeout warning with option to cancel
- The system **SHALL** display skeleton loaders with shimmer animation during visualization rendering
- Skeleton loaders **SHALL** show chart-shaped placeholders (axis lines, bar outlines) rather than generic loading text
- For multi-tool queries, the system **SHALL** display a "Waiting for results..." indicator per pending tool while others complete
- Completed tool results **SHALL** render inline as they become available, with a subtle animation
- A summary message **SHALL** appear only after all tools complete, synthesizing the results

### FR-1.7: Error Handling and HITL Clarification

- For ambiguous queries requiring HITL clarification, the system **SHALL** present inline clarification cards within the chat stream (NOT modals)
- The input **SHALL** remain active and usable during clarification
- Clarification options **SHALL** be limited to a maximum of 3 options
- The original query **SHALL** remain visible above the clarification
- API errors **SHALL** appear as inline error messages within the chat stream with `text-red-600` coloring and an error icon
- Each error **SHALL** include a "Try adjusting: [specific dimension]" suggestion when applicable
- Rate limit errors (429) **SHALL** show countdown timer until retry is available
- All error messages **SHALL** use user-friendly language, not raw error codes
- Session timeout **SHALL** display an inline banner above the chat input (NOT a modal)
- The banner **SHALL** allow re-authentication without losing the current conversation context
- Conversation context **SHALL** be preserved for 30 minutes after timeout to allow resumption

### FR-1.8: Empty State

- The system **SHALL** display a centered placeholder visualization area on initial load
- The placeholder **SHALL** include a sample query prompt in muted text (e.g., "Try: What was Walmart's market share in grocery last quarter?")
- The placeholder **SHALL** show a subtle animated visualization placeholder to indicate where charts will appear
- The empty state **SHALL NOT** block the input field from being immediately usable
- The empty state **SHALL** disappear upon submission of the first query

---

## FR-2: Intelligent Tool Selection

The system **SHALL** maintain a registry of data retrieval tools and select the appropriate tool(s) for each user query.

### FR-2.1: Tool Registry

- The system **SHALL** maintain a registry of 12-15 core data retrieval tools
- Tool definitions **SHALL** include: id, name, description, capabilities, dimensions (required and optional), example queries, output schema, and aliases
- Tool definitions **SHALL** be stored as embeddings for semantic retrieval
- Tools **SHALL** be addable, modifiable, or deprecated without pipeline changes
- Tool templates **SHALL** be versioned and stored in configuration
- Each API request **SHALL** log the tool template version used for reproducibility

### FR-2.2: Core Tool Set (Priority Order)

The system **SHALL** implement the following tools as P0 (Must Have):

1. **market_share_trend** -- Brand-vs-brand market share, category-wide share breakdown, share trend over time
2. **brand_comparison** -- Direct Brand X vs. Brand Y analysis (competitive positioning)
3. **yoy_growth_analysis** -- Transaction volume and spend growth year-over-year
4. **same_store_sales** -- Organic growth metric separating new units from existing store performance
5. **category_trends** -- Category-level transaction counts and dollar volumes
6. **wallet_share** -- Share of customer's total category spend per brand

The system **SHALL** implement the following tools as P1 (Should Have):

7. **cross_shopping_overlap** -- Multi-brand purchasing patterns and customer overlap (binary: shopped both brands)
8. **demographic_breakdown** -- Spending distribution by generation, income, age
9. **geographic_breakdown** -- State/CBSA/regional spending patterns
10. **customer_retention** -- Cohort retention and churn analysis

The system **SHALL** implement the following tools as P2 (Nice to Have):

11. **top_n_rankings** -- Brand rankings by various metrics
12. **channel_analysis** -- Online vs. in-store vs. mobile breakdown
13. **basket_analysis** -- Co-purchase patterns
14. **promotional_sensitivity** -- Price elasticity and promotional lift analysis

### FR-2.3: RAG-Based Tool Retrieval

- The system **SHALL** use OpenAI's text-embedding-3-small via OpenRouter for embeddings
- The system **SHALL** retrieve top-8 candidate tools based on semantic similarity
- The RAG retrieval similarity threshold **SHALL** be 0.70
- If the top candidate's similarity is below 0.70, the system **SHALL** route to HITL clarification with available candidates displayed
- Tool definitions **SHALL NOT** include dimension value enumerations (lists of brands, states) as these dilute retrieval signal
- Brand aliases **SHALL** be stored in a separate lookup table, not in the tool definition

### FR-2.4: Tool Selection LLM

- The system **SHALL** use MiniMax-Text-01 for tool selection via OpenRouter
- The LLM **SHALL** select the best-matching tool(s) from the narrowed candidates
- Tool selection confidence **SHALL** be computed as a weighted combination:
  - 25% RAG similarity score
  - 35% LLM selection score
  - 40% dimension match score
- Confidence thresholds **SHALL** be:
  - >=0.85: Proceed with selected tool
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
- Multi-tool queries **SHALL** execute in parallel with results returned as a JSON object keyed by tool name, plus a `synthesized_summary` field
- The planner **SHALL** use GLM-4-Air via OpenRouter for planning decisions
- Dimension extraction nodes **SHALL** execute in parallel for independent dimensions
- Dependent extractions (e.g., brand resolution that affects category inference) **SHALL** execute sequentially with the dependency graph defined by the planner

---

## FR-3: Dimension Extraction Pipeline

The system **SHALL** extract dimensional parameters from user queries using parallel, category-specialized extraction nodes.

### FR-3.1: Dimension Categories

The system **SHALL** extract parameters for the following dimension categories:
- **brand**: Brand names (e.g., Walmart, Target, Chipotle) with fuzzy matching and alias resolution
- **merchant_category**: Category names via enum lookup
- **geography**: State, CBSA, metro area, zip code with hierarchical normalization
- **time_range**: Start date, end date, period type (calendar, rolling, event-based)
- **generation**: Gen Z (1997-2024), Millennial (1981-1996), Gen X (1965-1980), Boomer (1946-1964), Silent (before 1946)
- **income_band**: Band 1 (<$25,000), Band 2 ($25,000-$49,999), Band 3 ($50,000-$74,999), Band 4 ($75,000-$99,999), Band 5 ($100,000-$149,999), Band 6 ($150,000+)
- **card_type**: credit, debit, prepaid, corporate
- **payment_network**: visa, mastercard, amex, discover
- **channel**: online, in-store, mobile
- **day_of_week**: monday, tuesday, wednesday, thursday, friday, saturday, sunday
- **aggregation_level**: hourly, daily, weekly, monthly, quarterly, annual, auto

### FR-3.2: Parallel Extraction Architecture

- The system **SHALL** execute dimension extraction nodes in parallel for independent dimensions
- Each dimension extraction prompt **SHALL** include only the relevant conversation turns and **SHALL NOT** exceed 2,000 tokens
- **Time Range Parser**: Deterministic logic for patterns like "last quarter," "Q3 2024," "YTD" -- target latency 10-50ms
- **Geography Normalizer**: State abbreviations, metro name resolution, zip-to-region mapping -- 50-150ms with cached lookups
- **Brand Matcher**: LLM + fuzzy matching for aliases, misspellings, parent company resolution -- 400-800ms
- **Category Lookup**: LLM + enum lookup against hierarchical category taxonomy -- 400-800ms
- **Generation/Income Parsing**: LLM with validation against enumerated values -- 400-800ms
- **Total parallel extraction budget: 600-1200ms**

### FR-3.3: Time Range Parsing Rules

This section **SHALL** be the authoritative source for aggregation level auto-selection throughout the pipeline:

- **Explicit wins**: "daily" -> daily, "monthly" -> monthly, "quarterly" -> quarterly
- **Time range size defaults**:
  - 1-14 days -> daily
  - 15-90 days -> weekly
  - 91-365 days -> monthly
  - 1-2 years -> quarterly
  - 2+ years -> annual
- **Query intent inference**: "trend" or "over time" -> prefer finer granularity; "summary" -> prefer coarser
- The dimension extractor **SHALL** set `period_type` field as "calendar", "rolling", or "event_based"

### FR-3.4: Synonym and Layman Term Handling

- The system **SHALL** use LLM + lookup table hybrid for dimension value mapping
- Examples:
  - "young people" -> Gen Z (confidence 0.7) with Millennial as alternative (confidence below 0.70 should be surfaced in observability, not silently resolved)
  - "credit card" -> credit (confidence 0.8) with debit as alternative
  - "fancy" -> premium tier (confidence 0.8)
- Brand aliases **SHALL** be resolved via fuzzy matching (e.g., "Walmart" -> Walmart)

### FR-3.5: Dimension Validation

- The system **SHALL** validate extracted dimensions against the API's dimension enumeration endpoint before constructing queries
- If an extracted value is not found in enumeration, the system **SHALL** provide suggestions based on string similarity
- The system **SHALL** reject queries missing required dimensions for the selected tool with a clarification request

### FR-3.6: Conflict Resolution

- When dimension conflicts are detected (e.g., "Target sales in TX and CA last month and last year"), the system **SHALL** surface structured disambiguation
- The system **SHALL NOT** silently generate multiple API calls or make best-effort interpretations
- Disambiguation options **SHALL** be limited to 2-3 maximum

### FR-3.7: Extraction Output Schema

- Dimension extraction output **SHALL** conform to a defined JSON Schema
- The system **SHALL** validate LLM outputs against the schema before proceeding
- Invalid outputs **SHALL** trigger retry with explicit system prompt correction

---

## FR-4: Data Retrieval API (ASP.NET Core)

The system **SHALL** provide a REST API built in ASP.NET Core as the data access layer between the AI pipeline and the database.

### FR-4.1: API Contract Design

- The API **SHALL** implement a hybrid approach with unified query endpoint and tool-scoped routing
- The primary endpoint **SHALL** be `POST /api/query` accepting:
  ```json
  {
    "tool": "market_share_trend",
    "dimensions": {
      "brand": ["Walmart", "Target"],
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
- Valid `metric` values **SHALL** be: sum, avg, count, min, max, median

### FR-4.2: Batch Endpoint for Multi-Tool Queries

- The API **SHALL** expose `POST /api/query/batch` for parallel multi-tool execution
- The batch endpoint **SHALL** execute queries against TimescaleDB in parallel
- The response **SHALL** include latency per constituent query
- Results **SHALL** be returned as a JSON object keyed by tool name, plus a `synthesized_summary` field for multi-tool queries

### FR-4.3: Query Guardrails

- The API **SHALL** require at least one high-cardinality dimension filter (brand, category, or geography) to prevent full-table scans
- A query is considered sufficiently filtered if it includes at least one of:
  - (a) 1-50 specific brands
  - (b) 1-10 categories
  - (c) 1-20 state/CBSA values
  - (d) a time range of 90+ days
- Queries without sufficient filters **SHALL** return 400 with `INSUFFICIENT_FILTERS` error code
- Raw queries **SHALL** require a `limit` parameter with maximum of 1,000 rows

### FR-4.4: Aggregation Level Handling

- The API **SHALL** auto-select aggregation level based on time range when `level: "auto"` is specified, per the authoritative rules in FR-3.3:
  - 1-14 days -> daily
  - 15-90 days -> weekly
  - 91-365 days -> monthly
  - 1-2 years -> quarterly
  - 2+ years -> annual
- Explicit aggregation levels **SHALL** override auto-selection

### FR-4.5: Repository Pattern

- The API **SHALL** follow clean repository/adapter patterns allowing future database migration without contract changes
- The repository abstraction **SHALL** hide data access implementation details

### FR-4.6: Dimension Enumeration Endpoints

- The API **SHALL** expose dimension enumeration endpoints cached in-memory with a 24-hour TTL
- Dimension enumeration values **SHALL** be loaded from static configuration files at API startup
- The following endpoints **SHALL** be exposed:
  - `GET /api/dimensions/brands`
  - `GET /api/dimensions/categories`
  - `GET /api/dimensions/states`
  - `GET /api/dimensions/generations`
  - `GET /api/dimensions/income-bands`
  - `GET /api/dimensions/channels`
  - `GET /api/dimensions/day-of-week`
  - `GET /api/dimensions/payment-networks`
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
- The API **SHALL** generate a UUID request_id on incoming requests and include it in all log entries and error responses
- The FastAPI pipeline **SHALL** pass request_id via `X-Request-ID` header to the Data API

---

## FR-5: Data Visualization

The system **SHALL** render query results as interactive charts and tables using ECharts.

### FR-5.1: Auto Chart-Type Selection

- The system **SHALL** automatically select chart type based on query pattern and result shape:
  - "average", "total", "sum" + single value -> KPI Card
  - "over time", "trend", "history" -> Line Chart
  - "compare", "vs", "versus" + 2-5 categories -> Bar Chart
  - "share", "percentage", "proportion" -> Pie/Donut Chart
  - "across", "by", "segmented" + multiple dimensions -> Stacked Bar or Heatmap
  - "correlation", "relationship", "scatter" -> Scatter Plot
  - "ranking", "top", "bottom" -> Horizontal Bar Chart
  - "geography", "state", "region" -> Choropleth Map
  - "share trend over time" -> Stacked Area Chart
  - "decomposition", "driver", "contribution" -> Waterfall Chart
  - "ranking change", "how did ranking evolve" -> Bump Chart

### FR-5.2: Manual Override

- The system **SHALL** provide a manual chart type override control
- The override dropdown **SHALL** appear in a floating toolbar above the chart, aligned to the right
- Available options **SHALL** include: Auto, Table, Line, Bar (Vertical), Bar (Horizontal), Pie, Donut, Scatter
- When override differs from auto-selection, the system **SHALL** show a tooltip explaining the auto-selection reasoning

### FR-5.3: KPI Card Display

- For single aggregate values (e.g., "average Target spend"), the system **SHALL** render a KPI card instead of a chart
- The KPI card **SHALL** display: metric name, primary value, comparison to prior period, comparison to category average, year-over-year change %, and growth rate indicator
- KPI comparison to prior period **SHALL** be calculated as: ((current - prior) / prior) * 100
- Prior period selection logic: if query specifies a quarter, use same quarter prior year (YoY); if query specifies a month, use prior month (MoM)
- Category average comparison **SHALL** use unweighted average of all brands in the queried category
- The KPI card **SHALL** include a "View as table" toggle

### FR-5.4: Table Toggle

- The system **SHALL** provide a toggle between chart and table views
- Toggle states **SHALL** be: Chart only, Table only, Both (split view)
- For queries returning only tabular data, the system **SHALL** show table as primary

### FR-5.5: Chart Interactivity (Required)

- Charts **SHALL** support hover tooltips showing exact values
- Charts **SHALL** support legend toggling for multi-series data
- Charts **SHALL** support responsive resize

### FR-5.6: Chart Interactivity (Required)

- Charts **SHALL** support data zoom (slider) for time-series with 8+ data points
- Charts **SHALL** support click-to-highlight for legend items or bars
- Data zoom **SHALL** display a reset button when zoom is active

### FR-5.7: Result Set Handling

- For 1-100 rows: Full table display
- For 101-1,000 rows: Paginated (50 rows/page) or virtual scrolling
- For 1,001-10,000 rows: Aggregated view shown by default; raw data on demand
- For 10,000+ rows: Aggregation mandatory; raw data requires explicit query parameter

### FR-5.8: Visualization Updates

- The canvas **SHALL** update with each new query result
- Prior visualizations **SHALL** be accessible via conversation history
- The chat sidebar **SHALL** display conversation history with thumbnail previews
- Thumbnails **SHALL** be 64x48px with 4:3 aspect ratio
- Thumbnails **SHALL** show a scaled-down rendering of the actual chart (SVG or canvas snapshot)
- Hover **SHALL** show a tooltip with the full query text and timestamp
- Click **SHALL** smooth-scroll to that message and re-render the visualization in the canvas

### FR-5.9: Chart Interaction Details

- Clicking a bar/segment **SHALL** show a detailed tooltip with the value AND offer a drill-down option via "Click to explore" prompt
- Chart header **SHALL** include an export dropdown (PNG, CSV) using native ECharts export methods
- Charts returning empty data **SHALL** display a centered empty state with "No data matches your query" message

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
- Compression reduces storage for chunks between 30 days and 7 years
- A retention policy **SHALL** drop chunks older than 7 years
- At the 7-year boundary, chunks are dropped per retention policy

### FR-6.3: Hierarchical Geography

- The geography dimension **SHALL** support hierarchical levels:
  - State (51 values) -- REQUIRED
  - CBSA/Metro Area (350-400 values) -- REQUIRED
  - 3-digit ZIP (800-1000 values) -- NICE-TO-HAVE
  - Urban/Suburban/Rural classification -- REQUIRED

### FR-6.4: Category Taxonomy (3-Level Hierarchy)

- **Level 1 - Style Classification**: Discretionary, Consumer Staples, Services, Transportation
- **Level 2 - Spending Category**: 35-45 categories (Grocery, Restaurant, Apparel, Travel, etc.)
- **Level 3 - Merchant Group**: 200-400 subcategories

### FR-6.5: Brand Tier Classification

- Each brand **SHALL** be classified by tier: luxury, premium, mid-market, value
- Each brand **SHALL** have a category archetype: fast casual, discount retailer, department store, subscription, etc.
- The synthetic data **SHALL** use real brand names (e.g., Walmart, Target, McDonald's, Chipotle) for analytical credibility
- Minor fictionalization is acceptable for legal safety, but brand names must be recognizable and consistent with evaluation benchmarks
- Brand-to-parent mapping **SHALL** be included (e.g., Yum Brands: Taco Bell, Pizza Hut, KFC)

### FR-6.6: Statistical Distributions

- Transaction amounts **SHALL** follow log-normal distribution with category-specific parameters:
  - Essential categories: mu=3.0, sigma=0.8
  - Mid-tier retail: mu=3.5, sigma=1.0
  - Premium: mu=4.2, sigma=1.2
  - Dining: mu=3.2, sigma=0.9
  - Fast food: mu=2.2, sigma=0.6
- Income multipliers **SHALL** affect transaction amounts: income_band 6 ($150K+) gets 1.7x multiplier vs. 0.6x for band 1 (<$25K)
- Panel weights **SHALL** be calibrated to make the panel representative of US consumer demographics (generation x income_band x geography distribution)
- Panel weights **SHALL** sum to estimated total US consumer population
- Market share calculations using panel data **SHALL** apply panel weights

### FR-6.7: Embedded Spending Patterns

- **Holiday Season (Q4)**: 25-40% retail volume increase Nov-Dec with December 15-24 peak at +60-100% vs. prior-week baseline (NOT vs. Q3 average)
- **January Normalization**: January -15-25% vs. Q4 average to balance the Q4 spike
- **Back-to-School (Aug-Sep)**: 20-35% increase in school-related categories
- **Weekend vs. Weekday**: Saturday +30-35% vs. Monday baseline for retail
- **Generational Preferences**:
  - Gen Z: 22%+ dining/delivery, 16%+ apparel/fast fashion, high online (65%)
  - Millennials: 18%+ grocery (family), 12%+ home improvement
  - Boomers: 28%+ healthcare, 14%+ travel, 75% in-store
- **Income-Brand Correlation**:
  - High-income ($150K+) **SHALL** show: 70-80% premium/luxury brand, 15-25% mid-market, 0-5% value-tier
  - Walmart transactions for income band 6 ($150K+) **SHALL** be <2% of their total transactions
  - Income-brand correlation for premium brands **SHALL** have Pearson coefficient 0.45-0.60
  - Income-brand correlation for luxury brands **SHALL** have Pearson coefficient 0.55-0.70

### FR-6.8: Continuous Aggregates

The system **SHALL** pre-compute the following continuous aggregates:

- **Daily rollups**: brand + category + geo_state + generation + income_band (90-day retention, daily chunks, compressed after 7 days)
- **Weekly rollups**: same dimensions (2-year retention)
- **Monthly rollups**: same dimensions (7-year retention)
- **Market share %**: pre-computed per brand within category
- **YoY growth rates**: pre-computed monthly
- **Category mix %**: pre-computed daily
- **Weekly brand rankings**: by category and region
- Continuous aggregates **SHALL** use composite indexes on (timestamp, brand_id, category_id) for efficient filtering

### FR-6.9: Panel Data Structure

- The synthetic data **SHALL** be structured as a consumer panel (100,000-500,000 panelists)
- Each panelist **SHALL** have: persistent ID, income_band, generation, geography, panel_start_date, panel_weight
- Each panelist **SHALL** have 50-200 transactions over 2 years
- Panelists **SHALL** shop at 3-10 different brands within a category
- The panel **SHALL** generate 10M+ transactions across the full panel
- Synthetic data **SHALL** represent settled transactions only (not authorizations or refunds)

### FR-6.10: Data Quality Metrics

The following quality metrics **SHALL** be measured and reported during data generation validation:
- Coefficient of variation for daily transaction volumes: target 0.3-0.6
- Gini coefficient for brand market share: target 0.55-0.70
- Mean absolute deviation for category proportions vs. BEA consumer expenditure data: <5%
- Weekend-to-weekday ratio by category: within 10% of survey benchmarks
- Transaction count distribution **SHALL** follow expected frequency patterns per panelist
- Zero-inflation **SHALL** be modeled appropriately for panelists with sparse transaction history

---

## FR-7: Eval Framework

The system **SHALL** include an evaluation suite measuring accuracy and reliability of the AI pipeline.

### FR-7.1: Eval Suite Size

- The eval suite **SHALL** contain a minimum of 200 test cases
- Test cases **SHALL** be distributed across 5 complexity levels:
  - Level 1 (Simple): 30% (60 cases) -- single-tool, single-dimension
  - Level 2 (Moderate): 35% (70 cases) -- single-tool, 2-4 dimensions
  - Level 3 (Complex): 15% (30 cases) -- single-tool, 5+ dimensions
  - Level 4 (Multi-tool): 10% (20 cases) -- planner decomposition correctness
  - Level 5 (Ambiguous): 10% (20 cases) -- HITL appropriateness

### FR-7.2: Eval Dimensions and Metrics

- **Tool selection accuracy**: % correct tool(s) selected -- target >=90%
- **Dimension extraction accuracy**: % correct parameter values -- target >=85%
- **Visualization selection accuracy**: % correct chart type selected -- target >=85%
- **End-to-end result correctness**: Each test case **SHALL** be run across 3 trials with temperature=0. A test case passes if 2 of 3 trials return structurally correct results. Target >=80% of test cases passing.
- **Clarification appropriateness**: Human-rated 0-2 scale -- target mean >=1.5

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

The eval suite **SHALL** use real brand names consistent with the synthetic dataset:

**Level 1:**
- "What is Walmart's market share in grocery?"
- "How much did Target grow last quarter?"

**Level 2:**
- "Compare Target's market share in Texas vs. California"
- "Show me Starbucks' category share trend over 4 quarters"
- "What is McDonald's customer overlap with Wendy's?"
- "How is McDonald's doing vs. Burger King?"
- "Is Starbucks gaining or losing share?"

**Level 3:**
- "Why did Chipotle's sales spike in June?"
- "Are Target customers trading up or down in Q4?"
- "Did Prime Day impact Walmart's in-store traffic?"
- "What was Wendy's same-store sales growth in Q4 2024?"

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
- Response generation model **SHALL** support function calling / tool use for consistency with pipeline
- These internal model selections **SHALL NOT** be user-configurable in Phase 1

### FR-8.3: Response Generation Model

- The response generation stage (natural-language answer + visualization decisions) **SHALL** be user-configurable
- Users **SHALL** be able to select from six providers: OpenAI, Google, Anthropic, Kimi, MiniMax, GLM
- Model selection **SHALL** be exposed in the UI as a settings control
- Changes **SHALL** apply to subsequent queries within the session
- If a selected model does not support function calling, the system **SHALL** fall back to text-embedding-3-small for embedding + the strongest available model for generation, with a user warning

### FR-8.4: Model-Agnostic Pipeline

- The pipeline **SHALL** be model-agnostic at the integration layer
- Swapping models **SHALL** require no code changes, only configuration
- The system **SHALL** implement a provider-agnostic normalization layer for structured output

### FR-8.5: Provider Normalization

- The system **SHALL** normalize structured output across providers
- JSON mode / function calling consistency **SHALL** be achieved via adapter layer
- Parse failures **SHALL** trigger retry once with same model before returning user-friendly error
- After retry exhaustion, the system **SHALL** return a user-friendly error with request ID

### FR-8.6: LLM Failure Handling

- The pipeline **SHALL** implement exponential backoff with jitter for transient failures (max 3 retries)
- After retry exhaustion, the system **SHALL** return a user-friendly error with request ID
- Circuit breaker pattern **SHALL** be implemented to prevent cascade failures during provider outages
- Critical paths (tool selection, dimension extraction) **SHALL** have fallback to conservative defaults

### FR-8.7: Prompt Management

- Prompt templates **SHALL** be versioned and stored in configuration
- Each API request **SHALL** log the prompt version used for reproducibility
- The observability panel **SHALL** display the rendered prompt for debugging

---

## NFR-1: Performance

The system **SHALL** meet the following performance requirements.

### NFR-1.1: End-to-End Latency

- Query-to-visualization round-trip **SHALL** complete in under 5 seconds for single-tool queries
- Multi-tool queries **SHALL** stream partial results as tools complete

### NFR-1.2: API Response Time

- The ASP.NET Core API **SHALL** respond to parameterized queries in under 500ms total response time, measured from request receipt to response serialization, excluding network transit
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
    -> HTTP /api/copilotkit
FastAPI (AI Pipeline)
    -> HTTP /api/query
ASP.NET Core (Data API)
    ->
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
- Phase 1 **SHALL** operate as single-tenant with all queries implicitly scoped to tenant_id = 1

---

## NFR-3: Synthetic Data Quality

The synthetic data **SHALL** exhibit statistical properties and patterns that make it analytically credible.

### NFR-3.1: Pattern Realism

- Transaction amounts **SHALL** be log-normally distributed (not normal)
- Brand market shares **SHALL** follow Zipfian/power law distribution
- Inter-transaction time **SHALL** follow exponential distribution
- Category proportions **SHALL** follow Dirichlet distribution
- Synthetic data generation **SHALL** accept a configurable seed parameter for reproducibility
- The default seed value **SHALL** be documented and fixed for eval suite consistency

### NFR-3.2: Correlation Requirements

- Income-band **SHALL** correlate with brand tier selection:
  - Premium brands: Pearson coefficient 0.45-0.60
  - Luxury brands: Pearson coefficient 0.55-0.70
- Generation **SHALL** correlate with category preferences and channel preferences
- Geography **SHALL** correlate with category mix (urban: +30% dining/entertainment; rural: +25% auto/gas)
- High-income customers **SHALL NOT** heavily shop at Walmart -- Walmart transactions for income band 6 ($150K+) **SHALL** be <2% of their total transactions

### NFR-3.3: Seasonal Pattern Realism

- Q4 holiday spike **SHALL** show 25-40% retail volume increase with December 15-24 peak at +60-100% vs. prior-week baseline
- January **SHALL** show normalization (-15-25% below Q4 average)
- Back-to-school **SHALL** show 20-35% increase in Aug-Sep for school-related categories
- Weekend vs. weekday patterns **SHALL** be embedded: Saturday +30-35% vs. Monday baseline for retail

### NFR-3.4: Anti-Patterns to Avoid

- The synthetic data **SHALL NOT** exhibit uniform distribution across time (no spikes would be fake)
- The synthetic data **SHALL NOT** show identical spending profiles across generations
- The synthetic data **SHALL NOT** show identical category mixes across geographies
- The synthetic data **SHALL NOT** show zero correlation between income and brand selection
- The synthetic data **SHALL NOT** have deterministic patterns that repeat identically each year

### NFR-3.5: Data Validation Benchmarks

- Grocery spending **SHALL** be 18-25% of total spend
- Dining out **SHALL** be 10-15% of total spend
- E-commerce share of retail **SHALL** be 15-18% in 2024 (matching Census Bureau reported data)
- Holiday Q4 retail spike **SHALL** be +25-35% vs. Q3 average

### NFR-3.6: Statistical Validation Tests

The following tests **SHALL** pass during data generation validation:

1. **Shapiro-Wilk test** on log-transformed transaction amounts: p > 0.05 (confirms log-normal)
2. **Kolmogorov-Smirnov test** on brand market share vs. theoretical Zipfian: p > 0.05
3. **Chi-squared test** on category proportions vs. Dirichlet parameters: p > 0.05
4. **Autocorrelation test** on daily transaction volumes: no significant autocorrelation at lag 7 (confirms no identical-year-patterns)
5. **Market share stability test**: brand rank correlation between 2023 and 2024 > 0.85
6. Regression tests for statistical properties **SHALL** verify distributions remain within tolerance across data regenerations

---

## Synthesis Notes

### Conflict Resolutions

**1. Aggregation Level Rules (FR-3.3 vs FR-4.4)**
FR-3.3 is now the authoritative source. FR-4.4 references FR-3.3 directly. Unified rules:
- 1-14 days -> daily
- 15-90 days -> weekly
- 91-365 days -> monthly
- 1-2 years -> quarterly
- 2+ years -> annual

**2. Real vs Fictional Brand Names (FR-6.5 vs FR-7.6)**
Decision: Use real brand names in synthetic data. Benchmark queries use real brand names (Walmart, Target, McDonald's, etc.) for analytical credibility. Minor fictionalization is acceptable for legal safety but brand names must be recognizable.

**3. Observability Panel States (FR-1.4)**
Clarified 4 distinct levels: Level 0 (default/hidden), Level 1 (toggle ON), Level 2 (expanded message with JSON viewer), Level 3 (raw response). The "3-level" terminology was confusing; now properly described as 4 states with Level 0 being default off.

**4. Q4 Spike Magnitude (FR-6.7 vs NFR-3.5)**
December peak (+60-100%) is vs. prior-week baseline, NOT vs. Q3 average. Q4 overall is +25-35% vs. Q3 average per NFR-3.5. January normalization (-15-25%) added to balance the annual cycle.

**5. RAG Similarity Threshold (FR-2.3)**
Unified to 0.70 as the retrieval threshold. If top candidate < 0.70, route to HITL. The 0.75 value was a target for high-quality retrieval, not a hard cutoff.

**6. E-commerce Penetration (NFR-3.5)**
Revised from 20-25% to 15-18% to match Census Bureau reported data.

**7. Embedding Model (FR-2.3)**
"ember" is not a standard OpenRouter model. Changed to "OpenAI's text-embedding-3-small via OpenRouter."

**8. Latency SLA (NFR-1.2)**
Clarified: "500ms total response time, measured from request receipt to response serialization, excluding network transit."

**9. Income-Brand Correlation (NFR-3.2)**
Revised from 0.65-0.75 to 0.45-0.60 for premium brands (more realistic). Luxury brands: 0.55-0.70.

**10. KPI Card Comparison (FR-5.3)**
Added explicit methodology: prior period = YoY for explicit periods, MoM for relative periods. Category average = unweighted mean.

### Additions from Reviews

- FR-1.8: Empty state / first-time user experience
- FR-5.9: Chart interaction details (click drill-down, zoom reset, export)
- FR-6.10: Data quality metrics section
- FR-8.6: LLM failure handling / circuit breaker
- FR-8.7: Prompt versioning and audit trail
- NFR-3.6: Statistical validation tests
- New tools: same_store_sales (P0), wallet_share (P0), customer_retention (P1)
- New dimensions: payment_network, day_of_week
- Generation and income band explicit boundaries

---

## Success Criteria Checklist

- [ ] Natural language queries routed to correct tool with >=90% accuracy
- [ ] Dimensional parameters extracted with >=85% accuracy
- [ ] Query-to-visualization completes in under 5 seconds
- [ ] Ambiguous queries trigger HITL clarification gracefully
- [ ] Multi-turn conversations maintain context (token-based limit, 75% of model context)
- [ ] 14 core tools implemented and functional (6 P0, 4 P1, 4 P2)
- [ ] Eval suite with 200+ test cases operational
- [ ] 10M+ synthetic transactions with realistic patterns
- [ ] ASP.NET Core API meets 500ms SLA for aggregated queries
- [ ] Clear architectural separation demonstrated (React/FastAPI/ASP.NET Core/TimescaleDB)
- [ ] Observability panel with 4-level progressive disclosure
- [ ] Chart type auto-selection with manual override available
- [ ] Multi-tool query support via planner node
- [ ] Streaming response generation implemented
- [ ] Docker Compose deployment for local development
- [ ] Statistical validation tests pass (Shapiro-Wilk, K-S, Chi-squared, autocorrelation, brand rank correlation)
- [ ] Circuit breaker and retry logic for LLM failures
- [ ] Prompt versioning and audit trail implemented
