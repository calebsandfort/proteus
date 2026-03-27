# High-Level Requirements Document: Proteus

## Project Overview

This application is a natural-language chat interface that enables analysts and investors to query consumer transaction data through conversation rather than code. Users ask questions in plain English — "What's the average transaction at Target by generation over the last quarter?" — and the system translates that into structured tool calls against a parameterized REST API, returning formatted results with interactive visualizations.

The core technical challenge is intelligent tool selection across a large, dynamic set of data retrieval tools (targeting 10-50 tools), each with numerous queryable dimensions (30+). Rather than generating raw SQL, the system uses an LLM-powered pipeline to identify which tool(s) to invoke, extract the relevant dimensional parameters from the user's natural language, execute parameterized API calls, and render the results. This architecture mirrors production data-as-a-service platforms where the query complexity is abstracted behind well-defined API contracts.

The system is designed to serve two goals simultaneously: demonstrate full-stack proficiency across a modern AI-powered application (including a C# data API, Python AI orchestration layer, and React frontend), and stand on its own as a compelling portfolio product that showcases natural-language data access patterns at scale.

## Core Functionality

### Conversational Query Interface
- The chat interface uses CopilotKit's ChatSidebar component, pinned to the right side of the screen
- The remaining page area to the left serves as the main visualization canvas where charts, tables, and analytical results are displayed
- Users ask questions in natural language with no required syntax or structure
- System supports multi-turn conversations: follow-up questions, query refinement, and references to prior results within a session
- Chat responses include natural-language explanations; corresponding visualizations render in the main canvas area, synchronized with the active conversation
- Conversation history is maintained per session and persisted for later reference
- Observability toggle (hidden by default) allows users to inspect tool selection decisions, extracted parameters, and raw API responses

[SME:AIWorkflow] How should conversation context be managed across multi-turn interactions? Should the full message history be passed to the tool selection node, or should a summarization step compress prior context to stay within token limits? What's the optimal context window strategy for maintaining coherence while keeping latency low?

[SME:UXDesigner] What's the right default state for the observability panel? Should it be a persistent sidebar toggle, a per-message expandable section, or a separate debug view? How do we keep it useful for power users without cluttering the analyst experience?

### Intelligent Tool Selection
- System maintains a registry of 10-50 data retrieval tools, each representing a distinct analytical capability (e.g., market share comparison, cross-shopping analysis, customer demographics, transaction volume trends)
- Each tool has a structured definition including its purpose, accepted dimensions/parameters, return schema, and usage examples
- When a user submits a query, a RAG-based retrieval step searches tool definitions by semantic similarity to narrow the candidate set
- The LLM then selects the best-matching tool(s) from the narrowed candidates based on user intent
- When the query is ambiguous and multiple tools are equally plausible, the system routes to a HITL clarification step rather than guessing
- Tool definitions are stored as embeddings and can be added, modified, or deprecated without pipeline changes

[SME:AIWorkflow] What embedding model and similarity threshold work best for tool definition retrieval? How many candidate tools should be passed to the LLM for final selection — is there a sweet spot between too few (missed matches) and too many (decision fatigue / token waste)?

[SME:AIWorkflow] How should tool definitions be structured for optimal retrieval? Should they include synthetic example queries, dimension enumerations, or both? What metadata improves retrieval accuracy?

[SME:AIWorkflow] What's the best strategy for handling multi-tool queries where a single user question requires orchestrating calls to multiple tools (e.g., "Compare Target's market share to their customer demographics in Texas")? Should this be a planner node or handled by the tool selection LLM directly?

[SME:ConsumerSpending] What are the core analytical capabilities that consumer transaction data supports? Which tool categories are essential (e.g., market share, cross-shopping, customer retention, geographic performance) vs. nice-to-have? How do these capabilities map to the underlying data dimensions?

[SME:MarketAnalyst] What are the most common and highest-value queries that analysts and investors actually ask of consumer transaction data? How should tools be prioritized based on real-world usage patterns? What distinguishes a "useful insight" from raw data in this domain?

### Dimension Extraction Pipeline
- Once a tool is selected, the system extracts dimensional parameters from the user's query using parallel, category-specialized extraction nodes
- Dimension categories include (but are not limited to): brand/merchant, merchant category, geography (state, metro, zip), time range, demographic generation (Gen Z, Millennial, etc.), income band, card type (credit/debit), channel (online/in-store), and aggregation level
- Each extraction node runs independently and in parallel, applying domain-specific logic (e.g., geographic normalization, relative date resolution like "last quarter" → specific date range, brand alias matching)
- Extracted dimensions are validated against the selected tool's parameter schema; missing required dimensions trigger a clarification request to the user
- The assembled parameter set is used to construct the API call to the data retrieval layer

[SME:AIWorkflow] Which dimension categories benefit most from specialized extraction logic vs. general-purpose LLM extraction? For example, time range parsing and geographic normalization may need deterministic logic, while brand matching might work better with fuzzy LLM extraction.

[SME:AIWorkflow] How should we handle dimension conflicts or contradictions within a single query (e.g., "Target sales in Texas and California last month and last year")? Should the system generate multiple API calls, request clarification, or make a best-effort interpretation?

[SME:ConsumerSpending] What are the complete set of dimensions that should be modeled in the synthetic dataset to faithfully represent consumer transaction data? What cardinality is realistic for each dimension (e.g., how many merchant categories, geographic granularities, income bands)? What dimensions do analysts expect to be able to filter and group by?

### Data Retrieval API (ASP.NET Core)
- A separate REST API built in ASP.NET Core serves as the data access layer between the AI pipeline and the database
- Each tool in the tool registry maps to one or more API endpoints with strongly-typed request/response models
- API endpoints accept parameterized queries (dimensions extracted by the AI pipeline) and return structured JSON results
- The API handles query construction, database access, pagination, and result formatting
- API design follows clean repository/adapter patterns to allow future database migration without contract changes
- Endpoints include input validation, error handling, and query performance guardrails (e.g., maximum time range spans, required dimension filters to prevent full-table scans)

[SME:IntegrationEngineer] What's the optimal API contract design for supporting a wide range of analytical queries? Should endpoints be tool-specific (one endpoint per tool) or more generic with a flexible query parameter schema? What are the tradeoffs for each?

[SME:IntegrationEngineer] How should the API handle aggregation-level flexibility? For example, the same "transaction volume" tool might need to return daily, weekly, or monthly aggregates depending on the time range. Should this be a parameter or separate endpoints?

### Data Visualization
- Query results are rendered as interactive charts and tables using ECharts in the main canvas area (left of the chat sidebar)
- The system automatically selects an appropriate visualization type based on the query and result shape (e.g., time series → line chart, categorical comparison → bar chart, proportional breakdown → pie/donut chart)
- Users can view raw data tables alongside or instead of charts
- The canvas updates with each new query result; prior visualizations can be scrolled or tabbed through
- Charts support basic interactivity: hover tooltips, zoom on time axes, and legend toggling

[SME:UXDesigner] What chart types map to which analytical query patterns? Should the system offer a manual override for chart type, or is automatic selection sufficient for Phase 1?

[SME:MarketAnalyst] What presentation formats do analysts and investors expect when consuming spending data? Are there standard report layouts (e.g., market share reports, cross-shopping reports, competitor benchmarks) that the visualization layer should emulate?

[SME:DataScientist] What default aggregation and formatting rules should apply to different data types? For example, should monetary values always show as currency-formatted, should percentages always include a comparison baseline?

### Synthetic Data Layer
- The system operates on a synthetic dataset modeled on the dimensional structure of real-world consumer transaction data
- Data is generated using Python Faker and seeded into TimescaleDB
- The transaction table must be configured as a TimescaleDB hypertable partitioned on the transaction timestamp column, enabling automatic time-based partitioning, chunk-level compression, and optimized time-range queries. Continuous aggregates should be evaluated for pre-computing common rollups (daily, weekly, monthly totals by brand/category/geography)
- The dataset includes realistic dimensions: brand/merchant name, merchant category (QSR, grocery, apparel, etc.), transaction amount, transaction date, geography (state, metro area), customer generation, income band, card type, channel, and additional dimensions as needed
- Data volume should be sufficient to produce meaningful analytical results: target 10M+ synthetic transactions spanning 2+ years, 100+ brands, and full geographic coverage
- Seed data should include known patterns (e.g., seasonal spending spikes, generational spending differences, geographic variation) so that query results are plausible and demonstrable

[SME:ConsumerSpending] What real-world spending patterns and correlations are essential to model in synthetic data for it to be analytically credible? Examples: seasonal category spikes (holiday retail, back-to-school), generational spending profiles, income-to-brand correlations, geographic variation in category mix. What patterns would an analyst immediately recognize as fake if missing?

[SME:DataScientist] What statistical distributions and correlations should be embedded in the synthetic data to make it analytically interesting? For example, should higher-income bands show higher average transaction amounts at premium brands? Should there be seasonal patterns in specific categories?

[SME:MarketAnalyst] How many distinct tools/analytical capabilities can be meaningfully demonstrated with the synthetic dataset? What's the minimum set of tools that showcases the architecture while covering the query types analysts actually use?

### Eval Framework
- An evaluation suite measures the accuracy and reliability of the AI pipeline across diverse query types
- Eval dimensions include: tool selection accuracy (did the system pick the right tool?), dimension extraction accuracy (were parameters correctly parsed?), end-to-end result correctness (did the final answer match the expected output for a known query?), and clarification appropriateness (did the system ask for help when it should have?)
- Test cases are defined as structured fixtures: natural language input, expected tool, expected parameters, expected result characteristics
- The eval suite runs against the full pipeline (not just individual nodes) and produces pass/fail rates and accuracy scores per dimension
- Eval results are logged and can be compared across model versions or configuration changes

[SME:AIWorkflow] What's the minimum eval suite size to produce statistically meaningful accuracy metrics? How should test cases be distributed across query complexity levels (simple single-tool queries, multi-dimension queries, ambiguous queries, multi-tool queries)?

[SME:AIWorkflow] How should we handle eval for the clarification pathway? What constitutes a "correct" clarification — is it enough that the system asked, or does the clarification question need to be semantically appropriate?

[SME:MarketAnalyst] What are representative example queries across different complexity levels that should be included in the eval suite? What are common ways analysts phrase the same underlying question differently (e.g., "market share" vs. "competitive positioning" vs. "how is Brand X doing against Brand Y")?

### Model Configuration
- The AI pipeline uses OpenRouter as a unified LLM gateway
- Internal pipeline stages (tool selection, dimension extraction) use models from Kimi, MiniMax, or GLM for cost optimization
- The response generation stage (natural-language answer + visualization decisions) is user-configurable across six providers: OpenAI, Google, Anthropic, Kimi, MiniMax, and GLM
- Model selection is exposed in the UI as a settings control; changes apply to subsequent queries within the session
- The pipeline is model-agnostic at the integration layer — swapping models requires no code changes, only configuration

[SME:AIWorkflow] Which specific models from Kimi, MiniMax, and GLM perform best for structured tool selection and parameter extraction tasks? What evaluation criteria should be used to benchmark them (accuracy, latency, cost per query, structured output reliability)?

[SME:AIWorkflow] Are there meaningful differences in how these models handle structured output (JSON mode, function calling) that would affect the tool selection and extraction pipeline design? Should the pipeline normalize across different providers' function-calling conventions?

## Success Criteria

The system will be considered successful if:
- Natural language queries are routed to the correct tool with ≥90% accuracy on the eval suite
- Dimensional parameters are extracted correctly with ≥85% accuracy across all dimension categories
- Query-to-visualization round-trip completes in under 5 seconds for typical queries
- The system gracefully handles ambiguous queries by requesting clarification rather than returning incorrect results
- Multi-turn conversations maintain context and allow meaningful follow-up queries
- The eval framework produces actionable metrics that can differentiate model performance across providers
- The application demonstrates clear architectural separation: React frontend, FastAPI AI orchestration, ASP.NET Core data API, TimescaleDB storage
- An interviewer or reviewer can understand the system's architecture and trace a query from natural language input to visualized output

## Out of Scope for Phase 1

The following features are explicitly out of scope for the initial release but may be considered for future phases:

- Real/proprietary transaction data integration (Facteus or similar providers)
- User authentication and multi-tenancy (single-user for Phase 1)
- Saved queries, dashboards, or report generation
- Natural language to raw SQL fallback path
- Export functionality (CSV, PDF, etc.)
- Per-stage model selection in the UI (internal stages are hardcoded to Kimi/MiniMax/GLM)
- Real-time data streaming or live data updates
- Mobile-optimized interface
- Collaborative features or shared workspaces
- Snowflake or other cloud data warehouse integration (TimescaleDB only for Phase 1; repository pattern supports future migration)

## Technical Constraints

- Query-to-result latency must be under 5 seconds for single-tool queries; multi-tool queries may take longer but should stream partial results
- The ASP.NET Core API must respond to parameterized queries in under 500ms (database query time, excluding AI pipeline)
- Synthetic dataset must be large enough to produce statistically plausible results (target 10M+ rows)
- All LLM calls route through OpenRouter; no direct provider API integrations
- The system must run locally via Docker Compose for development and demonstration purposes
- ECharts is the required charting library for all data visualizations

[SME:AIWorkflow] What's the expected latency breakdown across pipeline stages (RAG retrieval, tool selection LLM call, parallel dimension extraction, API call, response generation)? Where are the bottlenecks, and should we implement streaming at the response generation stage to improve perceived performance?

## Assumptions

- Analysts and investors are comfortable asking data questions in natural language and do not expect SQL-level query precision
- The synthetic dataset is sufficient to demonstrate the architecture; users understand the data is not real
- Tool definitions can be authored manually for Phase 1; automated tool discovery is not required
- OpenRouter provides reliable access to models from all six target providers with consistent API behavior
- The eval framework can be run offline (batch mode) rather than requiring real-time accuracy monitoring
- A single-user deployment is acceptable for demonstration and interview purposes
