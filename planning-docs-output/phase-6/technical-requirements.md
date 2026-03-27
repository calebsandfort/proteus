# Proteus Technical Requirements Document
# Phase 6: Technical Specification Enrichment

**Document Version:** 1.0 (Technical)
**Date:** 2026-03-27
**Status:** Technical Specification - Ready for Implementation

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

#### Technical Implementation

**Component Structure (`frontend/src/components/chat/`):**
```
chat/
├── CopilotChat.tsx           # Main CopilotKit wrapper
├── ChatSidebar.tsx           # Sidebar container (380-420px width)
├── ChatDrawer.tsx            # Mobile drawer with FAB trigger
├── VisualizationCanvas.tsx   # Main canvas for charts/tables
├── MessageBubble.tsx         # Chat message with expand icon
├── ObservabilityPanel.tsx   # 4-level progressive disclosure
├── ModelSelector.tsx         # Dropdown for response generation model
└── EmptyState.tsx           # Initial placeholder visualization
```

**Key Props:**
```typescript
// ChatSidebar.tsx
interface ChatSidebarProps {
  width?: number; // 380-420, default 400
  isCollapsed?: boolean; // For mobile drawer state
}

// VisualizationCanvas.tsx
interface VisualizationCanvasProps {
  sessionId: string;
  chartType?: ChartType; // 'auto' | 'line' | 'bar' | 'pie' | etc.
  onChartTypeOverride?: (type: ChartType) => void;
}
```

**Mobile Breakpoint Handling:**
```typescript
// hooks/use-sidebar.ts
export function useSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const isMobile = useMediaQuery('(max-width: 1023px)');

  useEffect(() => {
    setIsCollapsed(isMobile);
  }, [isMobile]);

  return { isCollapsed, setIsCollapsed, isMobile };
}
```

### FR-1.2: Multi-Turn Conversation

- The system **SHALL** support multi-turn conversations enabling follow-up questions, query refinement, and references to prior results within a session
- The system **SHALL** maintain the most recent messages whose total token count does not exceed 75% of the current model's context window limit, with a minimum of the 4 most recent turns plus session anchor
- The system **SHALL** preserve the first query in a session as a "session anchor" that is always available
- The system **SHALL** tag each tool result with an internal reference ID for resolution of references like "that" or "those results"
- When a user switches to a new analytical topic (different brand/category), the system **SHALL** treat this as a new session context
- When context approaches 80% of model token limit, older messages **SHALL** be summarized or compressed
- Summarization **SHALL** preserve key extracted dimensions and tool selections for reference

#### Technical Implementation

**Conversation State Management:**
```typescript
// frontend/src/hooks/use-conversation.ts
interface ConversationTurn {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolResults?: ToolResult[];
  extractedDimensions?: Record<string, any>;
  timestamp: Date;
  isSessionAnchor?: boolean;
  referenceId?: string; // For "that result" resolution
}

interface ConversationState {
  sessionId: string;
  turns: ConversationTurn[];
  contextTokenCount: number;
  modelContextLimit: number;
}

const MAX_CONTEXT_RATIO = 0.75;
const MIN_TURNS_TO_KEEP = 4;
const SUMMARIZATION_THRESHOLD = 0.80;
```

**Session Context Preservation:**
```typescript
// Backend state management (LangGraph)
interface SessionContext {
  session_id: string;
  session_anchor: ConversationTurn; // First query, always preserved
  recent_turns: ConversationTurn[]; // Token-limited sliding window
  extracted_dimensions: Record<string, DimensionValue>; // For reference resolution
  topic_tracker: string[]; // Detected topics for session boundary detection
}
```

**Reference ID Resolution:**
```typescript
// Tool result tagging for reference resolution
interface ToolResult {
  referenceId: string; // e.g., "result_2024_03_27_001"
  toolName: string;
  dimensions: Record<string, any>;
  data: any;
  timestamp: Date;
}
```

### FR-1.3: Observability Panel

- The observability panel **SHALL** default to hidden (off by default)
- The system **SHALL** provide a persistent toggle control in the chat interface header area
- The toggle state **SHALL** persist across sessions via localStorage
- When toggled ON, chat messages **SHALL** gain subtle expand icons in the corner
- Clicking expand **SHALL** show an inline JSON viewer with syntax highlighting

#### Technical Implementation

**Observability State:**
```typescript
// frontend/src/hooks/use-observability.ts
interface ObservabilityState {
  level: 0 | 1 | 2 | 3; // 0=hidden, 1=toggle ON, 2=expanded, 3=raw
  isEnabled: boolean; // Persisted to localStorage
}

// localStorage key: 'proteus_observability_enabled'
```

### FR-1.4: Observability Progressive Disclosure (4-Level)

- **Level 0 (Default):** Clean chat + visualization. No instrumentation visible
- **Level 1 (Toggle ON):** Header shows active state; chat messages gain expand icons; displays selected tool(s), extracted dimensions, and latency per stage
- **Level 2 (Expanded Message):** Click expand icon -> inline JSON viewer showing top-3 RAG candidates with similarity scores
  - JSON viewer **SHALL** use `font-mono text-xs` styling (per design system)
  - JSON **SHALL** be formatted with collapsible tree nodes for objects/arrays beyond 3 levels
  - Maximum initial display of 20 lines with "Show more" expansion
  - Syntax highlighting **SHALL** use the design system's code colors (slate palette for keys, blue for strings, amber for numbers)
- **Level 3 (Raw Response):** Explicit "Show raw" action -> full API request/response

#### Technical Implementation

**JSON Viewer Component:**
```typescript
// frontend/src/components/observability/JsonViewer.tsx
interface JsonViewerProps {
  data: object;
  maxInitialLines?: number; // Default 20
  syntaxColors?: {
    key: string;    // slate-600
    string: string; // blue-600
    number: string; // amber-500
  };
}

interface PipelineStageMetadata {
  stage: string;
  latencyMs: number;
  selectedTool?: string;
  extractedDimensions?: Record<string, any>;
  ragCandidates?: Array<{
    toolId: string;
    similarity: number;
  }>;
}
```

**Observability Data Structure (per message):**
```typescript
interface ObservabilityMetadata {
  requestId: string;
  pipelineStages: PipelineStageMetadata[];
  totalLatencyMs: number;
  modelUsed: string;
  promptVersion: string;
  ragCandidates?: Array<{
    toolId: string;
    toolName: string;
    similarity: number;
  }>;
  rawRequest?: object; // Level 3 only
  rawResponse?: object; // Level 3 only
}
```

### FR-1.5: Model Selector

- The system **SHALL** display a model selector dropdown in the header bar
- The selector **SHALL** appear to the right of the observability toggle
- If header space is insufficient, the selector **SHALL** appear in a settings popover
- The dropdown **SHALL** display model names and provider logos
- The selector **SHALL** show the current selection prominently
- Changes **SHALL** apply to subsequent queries within the session

#### Technical Implementation

**Model Selector Component:**
```typescript
// frontend/src/components/settings/ModelSelector.tsx
interface ModelOption {
  id: string; // e.g., "openai/gpt-4o"
  provider: 'openai' | 'google' | 'anthropic' | 'kimi' | 'minimax' | 'glm';
  displayName: string;
  logoUrl?: string;
  supportsFunctionCalling: boolean;
}

const RESPONSE_GENERATION_MODELS: ModelOption[] = [
  { id: 'openai/gpt-4o', provider: 'openai', displayName: 'GPT-4o', supportsFunctionCalling: true },
  { id: 'google/gemini-2.0-flash', provider: 'google', displayName: 'Gemini 2.0 Flash', supportsFunctionCalling: true },
  { id: 'anthropic/claude-3.5-sonnet', provider: 'anthropic', displayName: 'Claude 3.5 Sonnet', supportsFunctionCalling: true },
  { id: 'moonshot/kimi-k2', provider: 'kimi', displayName: 'Kimi K2', supportsFunctionCalling: true },
  { id: 'minimax/text-01', provider: 'minimax', displayName: 'MiniMax Text-01', supportsFunctionCalling: true },
  { id: 'google/gemini-2.5-pro', provider: 'glm', displayName: 'GLM-4-Pro', supportsFunctionCalling: true },
];
```

### FR-1.6: Loading and Feedback States

- For queries taking under 2 seconds, no additional feedback beyond disabled input state
- For queries taking 2-5 seconds, the system **SHALL** display a stage indicator
- For queries taking over 5 seconds, the system **SHALL** show a timeout warning with option to cancel
- The system **SHALL** display skeleton loaders with shimmer animation during visualization rendering
- Skeleton loaders **SHALL** show chart-shaped placeholders (axis lines, bar outlines) rather than generic loading text
- For multi-tool queries, the system **SHALL** display a "Waiting for results..." indicator per pending tool while others complete
- Completed tool results **SHALL** render inline as they become available, with a subtle animation
- A summary message **SHALL** appear only after all tools complete, synthesizing the results

#### Technical Implementation

**Stage Indicator Component:**
```typescript
// frontend/src/components/feedback/StageIndicator.tsx
interface PipelineStage {
  name: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  startTime?: Date;
  endTime?: Date;
}

const PIPELINE_STAGES = [
  'Parsing query',
  'Retrieving tools',
  'Extracting dimensions',
  'Querying data',
  'Generating response',
] as const;
```

**Chart Skeleton Loader:**
```typescript
// frontend/src/components/feedback/ChartSkeleton.tsx
// Shows axis lines and bar outlines during loading
// Shimmer animation: bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100
```

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

#### Technical Implementation

**Clarification Card Component:**
```typescript
// frontend/src/components/chat/ClarificationCard.tsx
interface ClarificationOption {
  id: string;
  label: string;
  interpretedParams: Record<string, any>;
  suggestedQuestion?: string;
}

interface ClarificationCardProps {
  originalQuery: string;
  ambiguity: string;
  options: ClarificationOption[]; // Max 3
  onSelect: (optionId: string) => void;
  onDismiss: () => void;
}
```

**Error Response Display:**
```typescript
// frontend/src/components/feedback/ErrorMessage.tsx
interface ErrorDisplayProps {
  error: {
    code: string; // Machine-readable
    message: string; // User-friendly
    suggestion?: string; // "Try adjusting: [dimension]"
    retryAfter?: number; // Seconds for 429
  };
  onRetry?: () => void;
}
```

### FR-1.8: Empty State

- The system **SHALL** display a centered placeholder visualization area on initial load
- The placeholder **SHALL** include a sample query prompt in muted text (e.g., "Try: What was Walmart's market share in grocery last quarter?")
- The placeholder **SHALL** show a subtle animated visualization placeholder to indicate where charts will appear
- The empty state **SHALL NOT** block the input field from being immediately usable
- The empty state **SHALL** disappear upon submission of the first query

#### Technical Implementation

**Empty State Component:**
```typescript
// frontend/src/components/chat/EmptyState.tsx
const SAMPLE_QUERIES = [
  "What was Walmart's market share in grocery last quarter?",
  "Compare Target and Amazon in electronics",
  "Show me McDonald's year-over-year growth",
];

// Animated placeholder: subtle pulsing chart axes
```

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

#### Technical Implementation

**Tool Definition Schema (Pydantic):**
```python
# backend/src/api/models/tool.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ToolParameter(BaseModel):
    name: str
    type: str  # "string" | "number" | "boolean" | "array"
    description: str
    required: bool = False
    enum_values: Optional[List[str]] = None
    default: Optional[Any] = None

class ToolOutputSchema(BaseModel):
    type: str  # "kpi" | "time_series" | "breakdown" | "ranking"
    fields: List[Dict[str, str]]  # [{"name": "market_share", "type": "percentage"}]

class ToolDefinition(BaseModel):
    id: str  # e.g., "market_share_trend"
    name: str
    description: str
    capabilities: List[str]
    required_dimensions: List[str]  # ["brand", "period"]
    optional_dimensions: List[str]  # ["geo", "category"]
    parameters: List[ToolParameter]
    output_schema: ToolOutputSchema
    example_queries: List[str]
    aliases: List[str] = []
    version: str
    created_at: datetime
    updated_at: datetime
    is_deprecated: bool = False

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._embeddings: List[np.ndarray] = []  # For RAG

    def register(self, tool: ToolDefinition) -> None: ...
    def get(self, tool_id: str) -> Optional[ToolDefinition]: ...
    def list_active(self) -> List[ToolDefinition]: ...
    def search_by_embedding(self, query_embedding: np.ndarray, top_k: int = 8) -> List[ToolDefinition]: ...
```

**Tool Registry Storage:**
```yaml
# backend/src/config/tools/market_share_trend.yaml
id: market_share_trend
name: Market Share Trend
description: Brand-vs-brand market share, category-wide share breakdown, share trend over time
capabilities:
  - market_share
  - share_trend
  - brand_comparison
required_dimensions:
  - brand
  - period
optional_dimensions:
  - geo
  - category
  - generation
  - income_band
parameters:
  - name: brands
    type: array
    description: List of brand names to analyze
    required: true
  - name: period
    type: object
    description: Time period for analysis
    required: true
  - name: category
    type: string
    description: Merchant category
    required: false
output_schema:
  type: time_series
  fields:
    - name: timestamp
      type: datetime
    - name: brand
      type: string
    - name: market_share
      type: percentage
    - name: transaction_count
      type: integer
example_queries:
  - "What is Walmart's market share in grocery?"
  - "How has Target's share trended over the last year?"
aliases:
  - market_share
  - share_of_market
version: "1.0.0"
```

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

#### Technical Implementation

**Tool Enumeration (Backend):**
```python
# backend/src/api/router.py
from enum import Enum

class ToolPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"

TOOL_PRIORITIES = {
    "market_share_trend": ToolPriority.P0,
    "brand_comparison": ToolPriority.P0,
    "yoy_growth_analysis": ToolPriority.P0,
    "same_store_sales": ToolPriority.P0,
    "category_trends": ToolPriority.P0,
    "wallet_share": ToolPriority.P0,
    "cross_shopping_overlap": ToolPriority.P1,
    "demographic_breakdown": ToolPriority.P1,
    "geographic_breakdown": ToolPriority.P1,
    "customer_retention": ToolPriority.P1,
    "top_n_rankings": ToolPriority.P2,
    "channel_analysis": ToolPriority.P2,
    "basket_analysis": ToolPriority.P2,
    "promotional_sensitivity": ToolPriority.P2,
}
```

### FR-2.3: RAG-Based Tool Retrieval

- The system **SHALL** use OpenAI's text-embedding-3-small via OpenRouter for embeddings
- The system **SHALL** retrieve top-8 candidate tools based on semantic similarity
- The RAG retrieval similarity threshold **SHALL** be 0.70
- If the top candidate's similarity is below 0.70, the system **SHALL** route to HITL clarification with available candidates displayed
- Tool definitions **SHALL NOT** include dimension value enumerations (lists of brands, states) as these dilute retrieval signal
- Brand aliases **SHALL** be stored in a separate lookup table, not in the tool definition

#### Technical Implementation

**RAG Retrieval Interface:**
```python
# backend/src/agent/retrieval.py
from abc import ABC, abstractmethod
import numpy as np

class ToolRetriever(ABC):
    @abstractmethod
    def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        top_k: int = 8,
        similarity_threshold: float = 0.70
    ) -> List[RetrievedTool]:
        """Returns top-k tools above similarity threshold."""
        pass

class RetrievedTool(BaseModel):
    tool_id: str
    tool_definition: ToolDefinition
    similarity: float
    rank: int
```

**OpenRouter Embedding Integration:**
```python
# backend/src/api/openrouter.py
from openai import OpenAI

class OpenRouterClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

    def embed_texts(self, texts: List[str], model: str = "openai/text-embedding-3-small") -> List[np.ndarray]:
        response = self.client.embeddings.create(
            model=model,
            inputs=texts
        )
        return [np.array(e.embedding) for e in response.data]
```

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

#### Technical Implementation

**Tool Selection Output Schema:**
```python
# backend/src/agent/nodes.py
from pydantic import BaseModel
from typing import List, Optional

class ToolSelectionResult(BaseModel):
    selected_tools: List[str]  # Tool IDs
    confidence: float  # 0.0 - 1.0
    confidence_breakdown: Dict[str, float]  # {
      # "rag_similarity": 0.25,
      # "llm_selection": 0.35,
      # "dimension_match": 0.40,
    # }
    competing_candidates: Optional[List[str]] = None  # Shown if confidence 0.70-0.84
    reasoning: str

class ToolSelectionInput(BaseModel):
    query: str
    retrieved_tools: List[RetrievedTool]  # Top 8 from RAG
    extracted_dimensions: Dict[str, List[str]]  # From dimension extraction
```

**Dimension Match Scoring:**
```python
def compute_dimension_match_score(
    retrieved_tool: RetrievedTool,
    extracted_dimensions: Dict[str, List[str]]
) -> float:
    """
    Returns 0.0-1.0 based on how well extracted dimensions match tool requirements.
    - Full match (all required dims present): 1.0
    - Partial match: (matched_required / total_required) * 0.8
    - Missing required dims: heavily penalized
    """
    required = set(retrieved_tool.tool_definition.required_dimensions)
    extracted = set(extracted_dimensions.keys())

    if not required:
        return 1.0 if extracted else 0.5

    matched = required.intersection(extracted)
    score = len(matched) / len(required)

    # Bonus for optional matches
    optional = set(retrieved_tool.tool_definition.optional_dimensions)
    optional_matched = optional.intersection(extracted)
    score += (len(optional_matched) / len(optional)) * 0.2 if optional else 0

    return min(score, 1.0)
```

### FR-2.5: HITL Clarification

- When confidence is below threshold, the system **SHALL** generate a structured clarification response
- The clarification **SHALL** include the interpreted parameters for each option
- The clarification **SHALL** provide a suggested follow-up question
- The system **SHALL** limit clarification options to 2-3 maximum

#### Technical Implementation

**Clarification Output Schema:**
```python
# backend/src/agent/nodes.py
class HITLClarification(BaseModel):
    ambiguity_type: str  # "tool_selection" | "dimension_value" | "conflicting_dimensions"
    message: str  # User-friendly explanation
    options: List[ClarificationOption]  # 2-3 max
    suggested_question: Optional[str] = None

class ClarificationOption(BaseModel):
    id: str
    label: str  # Short label for UI
    interpreted_params: Dict[str, Any]  # The resolved parameters
    reasoning: str
```

### FR-2.6: Multi-Tool Query Handling (Planner Node)

- The system **SHALL** implement a dedicated planner node upstream of tool selection
- The planner **SHALL** detect whether a query requires single-tool or multi-tool execution
- For multi-tool queries, the planner **SHALL** output a structured execution plan specifying tool order and parameters
- Multi-tool queries **SHALL** execute in parallel with results returned as a JSON object keyed by tool name, plus a `synthesized_summary` field
- The planner **SHALL** use GLM-4-Air via OpenRouter for planning decisions
- Dimension extraction nodes **SHALL** execute in parallel for independent dimensions
- Dependent extractions (e.g., brand resolution that affects category inference) **SHALL** execute sequentially with the dependency graph defined by the planner

#### Technical Implementation

**Planner Node Output Schema:**
```python
# backend/src/agent/nodes.py
class ExecutionPlan(BaseModel):
    plan_id: str
    is_multi_tool: bool
    tools: List[PlannedTool]  # Ordered for sequential deps
    dimension_dependencies: Dict[str, List[str]]  # {"brand": [], "category": ["brand"]}
    estimated_latency_ms: int
    execution_mode: str  # "parallel" | "sequential"

class PlannedTool(BaseModel):
    tool_id: str
    order: int  # Execution order
    parameters: Dict[str, Any]  # Resolved from dimension extraction
    depends_on: List[str] = []  # Tool IDs this depends on
    can_parallelize: bool  # True if no dependencies on other planned tools

# Example multi-tool execution plan
# Query: "Compare Walmart vs Target market share in Texas and California"
# {
#   "plan_id": "plan_001",
#   "is_multi_tool": False,  # Same tool, different geo parameters
#   "tools": [{
#     "tool_id": "brand_comparison",
#     "order": 0,
#     "parameters": {"brands": ["Walmart", "Target"], "geo": ["TX", "CA"]},
#     "depends_on": [],
#     "can_parallelize": True
#   }]
# }
```

**Planner Prompt (GLM-4-Air):**
```python
# backend/src/agent/prompts.py
PLANNER_PROMPT = """
You are a query planner for a consumer analytics system.

Given the user's query, determine:
1. Is this a single-tool or multi-tool query?
2. What tools are needed and in what order?
3. Are there any dependencies between dimension extractions?

Query: {query}

Respond with a JSON execution plan.
"""
```

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

#### Technical Implementation

**Dimension Value Enums:**
```python
# backend/src/api/models/dimensions.py
from pydantic import BaseModel
from typing import List, Optional, Literal

class Generation(BaseModel):
    id: Literal["gen_z", "millennial", "gen_x", "boomer", "silent"]
    label: str
    birth_years: str  # "1997-2024"
    aliases: List[str] = ["young", "old", "senior"]

class IncomeBand(BaseModel):
    id: Literal["band_1", "band_2", "band_3", "band_4", "band_5", "band_6"]
    label: str
    range_usd: str  # "<$25,000"
    aliases: List[str] = ["low_income", "high_income"]

GENERATIONS = {
    "gen_z": Generation(id="gen_z", label="Gen Z", birth_years="1997-2024", aliases=["z", "zoomers", "young people"]),
    "millennial": Generation(id="millennial", label="Millennial", birth_years="1981-1996", aliases=["millennials", "y"]),
    "gen_x": Generation(id="gen_x", label="Gen X", birth_years="1965-1980", aliases=["gen_x", "x"]),
    "boomer": Generation(id="boomer", label="Boomer", birth_years="1946-1964", aliases=["boomers", "baby_boomers"]),
    "silent": Generation(id="silent", label="Silent", birth_years="before 1946", aliases=["silent_generation"]),
}

INCOME_BANDS = {
    "band_1": IncomeBand(id="band_1", label="Band 1", range_usd="<$25,000", aliases=["low"]),
    "band_2": IncomeBand(id="band_2", label="Band 2", range_usd="$25,000-$49,999", aliases=["lower_middle"]),
    "band_3": IncomeBand(id="band_3", label="Band 3", range_usd="$50,000-$74,999", aliases=["middle"]),
    "band_4": IncomeBand(id="band_4", label="Band 4", range_usd="$75,000-$99,999", aliases=["upper_middle"]),
    "band_5": IncomeBand(id="band_5", label="Band 5", range_usd="$100,000-$149,999", aliases=["high"]),
    "band_6": IncomeBand(id="band_6", label="Band 6", range_usd="$150,000+", aliases=["wealthy", "affluent"]),
}
```

### FR-3.2: Parallel Extraction Architecture

- The system **SHALL** execute dimension extraction nodes in parallel for independent dimensions
- Each dimension extraction prompt **SHALL** include only the relevant conversation turns and **SHALL NOT** exceed 2,000 tokens
- **Time Range Parser**: Deterministic logic for patterns like "last quarter," "Q3 2024," "YTD" -- target latency 10-50ms
- **Geography Normalizer**: State abbreviations, metro name resolution, zip-to-region mapping -- 50-150ms with cached lookups
- **Brand Matcher**: LLM + fuzzy matching for aliases, misspellings, parent company resolution -- 400-800ms
- **Category Lookup**: LLM + enum lookup against hierarchical category taxonomy -- 400-800ms
- **Generation/Income Parsing**: LLM with validation against enumerated values -- 400-800ms
- **Total parallel extraction budget: 600-1200ms**

#### Technical Implementation

**Dimension Extraction Node Interface:**
```python
# backend/src/agent/nodes.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DimensionExtractionInput(BaseModel):
    query: str
    conversation_history: List[Dict[str, Any]]  # Relevant turns only
    dimension_type: str  # "brand" | "geography" | "time_range" | etc.
    max_tokens: int = 2000

class DimensionExtractionResult(BaseModel):
    dimension_type: str
    values: List[Any]  # Extracted values
    confidence: float  # 0.0 - 1.0
    alternatives: List[Dict[str, Any]] = []  # For observability
    extraction_method: str  # "llm" | "deterministic" | "lookup"
    latency_ms: int
    validation_status: str  # "valid" | "needs_review" | "invalid"

class DimensionExtractor(ABC):
    @abstractmethod
    async def extract(self, input: DimensionExtractionInput) -> DimensionExtractionResult:
        pass

class BrandExtractor(DimensionExtractor):
    # Uses LLM + fuzzy matching
    # Target latency: 400-800ms
    pass

class TimeRangeExtractor(DimensionExtractor):
    # Deterministic parsing for "last quarter", "Q3 2024", "YTD"
    # Target latency: 10-50ms
    pass

class GeographyExtractor(DimensionExtractor):
    # State abbrev, metro resolution, zip-to-region
    # Target latency: 50-150ms (cached lookups)
    pass
```

**Parallel Execution:**
```python
# backend/src/agent/graph.py
from langgraph.graph import StateGraph
import asyncio

class DimensionExtractionGraph:
    def __init__(self):
        self.extractors: Dict[str, DimensionExtractor] = {
            "brand": BrandExtractor(),
            "geography": GeographyExtractor(),
            "time_range": TimeRangeExtractor(),
            "category": CategoryExtractor(),
            "generation": GenerationExtractor(),
            "income_band": IncomeBandExtractor(),
        }
        # Independent dimensions can run in parallel
        self.independent_dimensions = ["brand", "category", "generation", "income_band", "channel"]
        # Sequential dependencies
        self.dependencies = {
            "category": ["brand"],  # Category inference depends on brand context
            "geography": [],       # Fully independent
            "time_range": [],      # Fully independent
        }

    async def extract_all(self, query: str, conversation_history: List[Dict]) -> Dict[str, DimensionExtractionResult]:
        # Execute independent dimensions in parallel
        independent_tasks = [
            self.extractors[dim].extract(DimensionExtractionInput(
                query=query,
                conversation_history=conversation_history,
                dimension_type=dim
            ))
            for dim in self.independent_dimensions
        ]

        independent_results = await asyncio.gather(*independent_tasks)

        # Execute sequential with dependencies
        sequential_results = {}
        for dim, deps in self.dependencies.items():
            if deps and all(d in sequential_results for d in deps):
                sequential_results[dim] = await self.extractors[dim].extract(...)

        return {**dict(zip(self.independent_dimensions, independent_results)), **sequential_results}
```

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

#### Technical Implementation

**Time Range Parsing Logic:**
```python
# backend/src/agent/nodes.py
from datetime import datetime, timedelta
from typing import Optional, Tuple

class TimeRangeParser:
    QUERY_PATTERNS = {
        r"last\s+quarter": lambda: ("last_quarter", "rolling"),
        r"Q([1-4])\s*(\d{4})": lambda m: (f"Q{m.group(1)} {m.group(2)}", "calendar"),
        r"YTD": lambda: ("ytd", "calendar"),
        r"last\s+year": lambda: ("last_year", "rolling"),
        r"last\s+(\d+)\s+days": lambda m: (int(m.group(1)), "rolling"),
    }

    AGGREGATION_RULES = {
        (1, 14): "daily",
        (15, 90): "weekly",
        (91, 365): "monthly",
        (366, 730): "quarterly",
        (731, float("inf")): "annual",
    }

    def parse(self, query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Returns (time_range_description, period_type, aggregation_level)"""
        # Implementation uses regex + deterministic rules
        # Returns None if no time range detected
        pass

    def infer_aggregation(self, days: int, query_intent: str = None) -> str:
        """Returns aggregation level based on day count and intent."""
        if query_intent:
            if "trend" in query_intent.lower() or "over time" in query_intent.lower():
                # Prefer finer granularity
                return "daily" if days <= 90 else "weekly"

        for (min_days, max_days), level in sorted(self.AGGREGATION_RULES.items()):
            if min_days <= days <= max_days:
                return level
        return "monthly"  # Default
```

### FR-3.4: Synonym and Layman Term Handling

- The system **SHALL** use LLM + lookup table hybrid for dimension value mapping
- Examples:
  - "young people" -> Gen Z (confidence 0.7) with Millennial as alternative (confidence below 0.70 should be surfaced in observability, not silently resolved)
  - "credit card" -> credit (confidence 0.8) with debit as alternative
  - "fancy" -> premium tier (confidence 0.8)
- Brand aliases **SHALL** be resolved via fuzzy matching (e.g., "Walmart" -> Walmart)

#### Technical Implementation

**Synonym Resolution:**
```python
# backend/src/api/lookup.py
from fuzzywuzzy import fuzz

class SynonymResolver:
    def __init__(self):
        self.dimension_aliases = {
            "brand": {},  # Loaded from brand_aliases table
            "generation": {
                "young people": [("gen_z", 0.7), ("millennial", 0.6)],
                "old": [("boomer", 0.8), ("silent", 0.5)],
            },
            "income_band": {
                "wealthy": [("band_6", 0.9), ("band_5", 0.6)],
                "affluent": [("band_6", 0.8), ("band_5", 0.7)],
            },
            "card_type": {
                "credit card": [("credit", 0.8), ("debit", 0.3)],
            },
        }

    def resolve(self, dimension: str, value: str) -> List[Tuple[str, float]]:
        """Returns list of (canonical_value, confidence) sorted by confidence."""
        # First check lookup table
        if dimension in self.dimension_aliases:
            aliases = self.dimension_aliases[dimension]
            if value.lower() in aliases:
                return aliases[value.lower()]

        # Fall back to fuzzy matching against enumeration
        return self.fuzzy_match(dimension, value)
```

### FR-3.5: Dimension Validation

- The system **SHALL** validate extracted dimensions against the API's dimension enumeration endpoint before constructing queries
- If an extracted value is not found in enumeration, the system **SHALL** provide suggestions based on string similarity
- The system **SHALL** reject queries missing required dimensions for the selected tool with a clarification request

#### Technical Implementation

**Validation Schema:**
```python
# backend/src/api/models/dimensions.py
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional

class DimensionValidationResult(BaseModel):
    is_valid: bool
    dimension: str
    value: str
    canonical_value: Optional[str] = None
    suggestions: List[str] = []  # Similar values if not valid

class ExtractedDimensions(BaseModel):
    brand: List[str] = []
    merchant_category: List[str] = []
    geography: List[str] = []
    time_range: Optional[Dict[str, Any]] = None
    generation: List[str] = []
    income_band: List[str] = []
    card_type: List[str] = []
    payment_network: List[str] = []
    channel: List[str] = []
    day_of_week: List[str] = []
    aggregation_level: Optional[str] = None

    def validate_for_tool(self, tool_id: str) -> Tuple[bool, List[str]]:
        """Returns (is_valid, missing_required_dimensions)."""
        required = TOOL_REQUIRED_DIMENSIONS[tool_id]
        missing = [dim for dim in required if not getattr(self, dim, [])]
        return len(missing) == 0, missing
```

### FR-3.6: Conflict Resolution

- When dimension conflicts are detected (e.g., "Target sales in TX and CA last month and last year"), the system **SHALL** surface structured disambiguation
- The system **SHALL NOT** silently generate multiple API calls or make best-effort interpretations
- Disambiguation options **SHALL** be limited to 2-3 maximum

#### Technical Implementation

**Conflict Detection and Resolution:**
```python
# backend/src/agent/nodes.py
class DimensionConflict(BaseModel):
    dimension: str
    conflicting_values: List[Any]
    conflict_type: str  # "temporal_overlap" | "geographic_overlap" | etc.
    options: List[DisambiguationOption]  # 2-3 max

class DisambiguationOption(BaseModel):
    id: str
    label: str
    resolved_dimensions: Dict[str, Any]
    reasoning: str

def detect_conflicts(extracted: ExtractedDimensions) -> List[DimensionConflict]:
    """Detects temporal and spatial conflicts."""
    conflicts = []

    # Temporal conflict: "last month and last year"
    if extracted.time_range:
        periods = extracted.time_range.get("periods", [])
        if len(periods) > 1:
            conflicts.append(DimensionConflict(
                dimension="time_range",
                conflicting_values=periods,
                conflict_type="temporal_overlap",
                options=generate_temporal_options(periods)  # 2-3 max
            ))

    return conflicts
```

### FR-3.7: Extraction Output Schema

- Dimension extraction output **SHALL** conform to a defined JSON Schema
- The system **SHALL** validate LLM outputs against the schema before proceeding
- Invalid outputs **SHALL** trigger retry with explicit system prompt correction

#### Technical Implementation

**Extraction Output Schema (Pydantic):**
```python
# backend/src/agent/nodes.py
class DimensionExtractionOutput(BaseModel):
    extracted_dimensions: ExtractedDimensions
    conflicts: List[DimensionConflict] = []
    validation_errors: List[str] = []
    retry_count: int = 0
    schema_version: str = "1.0"

class LLMExtractionValidator:
    """Validates LLM JSON output against schema."""
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema

    def validate(self, raw_output: str) -> Tuple[bool, Optional[DimensionExtractionOutput], Optional[str]]:
        """
        Returns (is_valid, parsed_output, error_message).
        Invalid outputs trigger retry with corrected prompt.
        """
        try:
            parsed = json.loads(raw_output)
            output = DimensionExtractionOutput(**parsed)
            return True, output, None
        except (json.JSONDecodeError, ValidationError) as e:
            return False, None, str(e)
```

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

#### Technical Implementation

**Request/Response Models (C#):**
```csharp
// api/Models/QueryModels.cs
using System.Text.Json.Serialization;

public class QueryRequest
{
    [JsonPropertyName("tool")]
    public string Tool { get; set; } = string.Empty;

    [JsonPropertyName("dimensions")]
    public Dimensions Dimensions { get; set; } = new();

    [JsonPropertyName("aggregation")]
    public AggregationConfig Aggregation { get; set; } = new();

    [JsonPropertyName("pagination")]
    public PaginationConfig Pagination { get; set; } = new();
}

public class Dimensions
{
    [JsonPropertyName("brand")]
    public List<string>? Brand { get; set; }

    [JsonPropertyName("category")]
    public List<string>? Category { get; set; }

    [JsonPropertyName("geo")]
    public string? Geo { get; set; }

    [JsonPropertyName("period")]
    public PeriodConfig? Period { get; set; }

    [JsonPropertyName("generation")]
    public List<string>? Generation { get; set; }

    [JsonPropertyName("income_band")]
    public List<string>? IncomeBand { get; set; }

    [JsonPropertyName("card_type")]
    public List<string>? CardType { get; set; }

    [JsonPropertyName("payment_network")]
    public List<string>? PaymentNetwork { get; set; }

    [JsonPropertyName("channel")]
    public List<string>? Channel { get; set; }

    [JsonPropertyName("day_of_week")]
    public List<string>? DayOfWeek { get; set; }
}

public class PeriodConfig
{
    [JsonPropertyName("start")]
    public string Start { get; set; } = string.Empty;

    [JsonPropertyName("end")]
    public string End { get; set; } = string.Empty;

    [JsonPropertyName("period_type")]
    public string? PeriodType { get; set; } // "calendar", "rolling", "event_based"
}

public class AggregationConfig
{
    [JsonPropertyName("level")]
    public string Level { get; set; } = "auto"; // hourly, daily, weekly, monthly, quarterly, annual, auto

    [JsonPropertyName("metric")]
    public string Metric { get; set; } = "sum"; // sum, avg, count, min, max, median
}

public class PaginationConfig
{
    [JsonPropertyName("limit")]
    public int Limit { get; set; } = 100;

    [JsonPropertyName("cursor")]
    public string? Cursor { get; set; }
}

public class QueryResponse
{
    [JsonPropertyName("data")]
    public List<Dictionary<string, object>> Data { get; set; } = new();

    [JsonPropertyName("metadata")]
    public QueryMetadata Metadata { get; set; } = new();
}

public class QueryMetadata
{
    [JsonPropertyName("tool")]
    public string Tool { get; set; } = string.Empty;

    [JsonPropertyName("row_count")]
    public int RowCount { get; set; }

    [JsonPropertyName("execution_time_ms")]
    public long ExecutionTimeMs { get; set; }

    [JsonPropertyName("pagination")]
    public PaginationResult Pagination { get; set; } = new();

    [JsonPropertyName("aggregation_level")]
    public string AggregationLevel { get; set; } = string.Empty;
}

public class PaginationResult
{
    [JsonPropertyName("next_cursor")]
    public string? NextCursor { get; set; }

    [JsonPropertyName("has_more")]
    public bool HasMore { get; set; }
}
```

### FR-4.2: Batch Endpoint for Multi-Tool Queries

- The API **SHALL** expose `POST /api/query/batch` for parallel multi-tool execution
- The batch endpoint **SHALL** execute queries against TimescaleDB in parallel
- The response **SHALL** include latency per constituent query
- Results **SHALL** be returned as a JSON object keyed by tool name, plus a `synthesized_summary` field for multi-tool queries

#### Technical Implementation

**Batch Endpoint:**
```csharp
// api/Endpoints/BatchQueryEndpoint.cs
public class BatchQueryRequest
{
    public List<QueryRequest> Queries { get; set; } = new();
}

public class BatchQueryResponse
{
    public Dictionary<string, QueryResponse> Results { get; set; } = new();
    public Dictionary<string, long> LatencyPerQuery { get; set; } = new();
    public long TotalExecutionTimeMs { get; set; }
    public string? SynthesizedSummary { get; set; }
}

// POST /api/query/batch
app.MapPost("/api/query/batch", async (BatchQueryRequest request, TimescaleRepository repo) =>
{
    var tasks = request.Queries.Select(async q =>
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var result = await ExecuteQuery(q, repo);
        sw.Stop();
        return (q.Tool, Result: result, LatencyMs: sw.ElapsedMilliseconds);
    });

    var results = await Task.WhenAll(tasks);
    var response = new BatchQueryResponse
    {
        Results = results.ToDictionary(r => r.Tool, r => r.Result),
        LatencyPerQuery = results.ToDictionary(r => r.Tool, r => r.LatencyMs),
        TotalExecutionTimeMs = results.Max(r => r.LatencyMs) // Parallel execution
    };

    return Results.Ok(response);
});
```

### FR-4.3: Query Guardrails

- The API **SHALL** require at least one high-cardinality dimension filter (brand, category, or geography) to prevent full-table scans
- A query is considered sufficiently filtered if it includes at least one of:
  - (a) 1-50 specific brands
  - (b) 1-10 categories
  - (c) 1-20 state/CBSA values
  - (d) a time range of 90+ days
- Queries without sufficient filters **SHALL** return 400 with `INSUFFICIENT_FILTERS` error code
- Raw queries **SHALL** require a `limit` parameter with maximum of 1,000 rows

#### Technical Implementation

**Guardrail Validation:**
```csharp
// api/Validators/QueryGuardrails.cs
public class QueryGuardrailValidator
{
    public (bool IsValid, string? ErrorCode, string? ErrorMessage) Validate(QueryRequest request)
    {
        // Check high-cardinality filters
        var hasBrands = request.Dimensions.Brand?.Count > 0 && request.Dimensions.Brand.Count <= 50;
        var hasCategories = request.Dimensions.Category?.Count > 0 && request.Dimensions.Category.Count <= 10;
        var hasGeo = !string.IsNullOrEmpty(request.Dimensions.Geo) ||
                     (request.Dimensions.Geo?.Count > 0 && request.Dimensions.Geo.Count <= 20);

        // Check time range (90+ days)
        var hasLargeTimeRange = false;
        if (request.Dimensions.Period != null)
        {
            var days = (DateTime.Parse(request.Dimensions.Period.End) -
                       DateTime.Parse(request.Dimensions.Period.Start)).Days;
            hasLargeTimeRange = days >= 90;
        }

        var hasFilter = hasBrands || hasCategories || hasGeo || hasLargeTimeRange;

        if (!hasFilter)
        {
            return (false, "INSUFFICIENT_FILTERS",
                "Query must include at least one of: 1-50 brands, 1-10 categories, 1-20 geographies, or 90+ day time range");
        }

        // Check limit
        if (request.Pagination.Limit > 1000)
        {
            return (false, "LIMIT_EXCEEDED", "Maximum limit is 1000 rows");
        }

        return (true, null, null);
    }
}
```

### FR-4.4: Aggregation Level Handling

- The API **SHALL** auto-select aggregation level based on time range when `level: "auto"` is specified, per the authoritative rules in FR-3.3:
  - 1-14 days -> daily
  - 15-90 days -> weekly
  - 91-365 days -> monthly
  - 1-2 years -> quarterly
  - 2+ years -> annual
- Explicit aggregation levels **SHALL** override auto-selection

#### Technical Implementation

**Aggregation Level Resolver:**
```csharp
// api/Services/AggregationLevelResolver.cs
public class AggregationLevelResolver
{
    public string ResolveAggregationLevel(PeriodConfig? period, string requestedLevel)
    {
        if (requestedLevel != "auto")
            return requestedLevel;

        if (period == null)
            return "monthly"; // Default

        var start = DateTime.Parse(period.Start);
        var end = DateTime.Parse(period.End);
        var days = (end - start).Days;

        return days switch
        {
            <= 14 => "daily",
            <= 90 => "weekly",
            <= 365 => "monthly",
            <= 730 => "quarterly",
            _ => "annual"
        };
    }
}
```

### FR-4.5: Repository Pattern

- The API **SHALL** follow clean repository/adapter patterns allowing future database migration without contract changes
- The repository abstraction **SHALL** hide data access implementation details

#### Technical Implementation

**Repository Interface:**
```csharp
// api/Repositories/IQueryRepository.cs
public interface IQueryRepository
{
    Task<QueryResponse> ExecuteQueryAsync(QueryRequest request, CancellationToken ct = default);
    Task<BatchQueryResponse> ExecuteBatchQueryAsync(List<QueryRequest> requests, CancellationToken ct = default);
}

public class TimescaleQueryRepository : IQueryRepository
{
    private readonly TimescaleRepository _db;

    public async Task<QueryResponse> ExecuteQueryAsync(QueryRequest request, CancellationToken ct = default)
    {
        var sql = BuildQuery(request);
        var results = await _db.QueryAsync<dynamic>(sql.Sql, sql.Parameters);
        return MapToResponse(results, request);
    }
}
```

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

#### Technical Implementation

**Dimension Endpoints:**
```csharp
// api/Endpoints/DimensionEndpoints.cs
public class DimensionValue
{
    public string Id { get; set; } = string.Empty;
    public string CanonicalName { get; set; } = string.Empty;
    public List<string> Aliases { get; set; } = new();
}

// GET /api/dimensions/{dimension}
app.MapGet("/api/dimensions/{dimension}", async (string dimension, DimensionCache cache) =>
{
    var values = cache.Get(dimension);
    if (values == null)
        return Results.NotFound(new { error = "INVALID_DIMENSION", message = $"Unknown dimension: {dimension}" });

    return Results.Ok(new { data = values });
});

public class DimensionCache
{
    private readonly Dictionary<string, List<DimensionValue>> _cache = new();
    private readonly DateTime _expiresAt;
    private readonly string _cacheDir = "./config/dimensions";

    public DimensionCache()
    {
        // Load all dimension files at startup
        LoadDimension("brands");
        LoadDimension("categories");
        LoadDimension("states");
        LoadDimension("generations");
        LoadDimension("income-bands");
        LoadDimension("channels");
        LoadDimension("day-of-week");
        LoadDimension("payment-networks");
    }
}
```

**Dimension Configuration Files:**
```yaml
# api/config/dimensions/brands.yaml
- id: walmart
  canonical_name: Walmart
  aliases:
    - walmart
    - wm
    - wal-mart
- id: target
  canonical_name: Target
  aliases:
    - target
    - tgt
```

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

#### Technical Implementation

**Error Response Model:**
```csharp
// api/Models/ErrorResponse.cs
public class ErrorResponse
{
    [JsonPropertyName("error")]
    public string Error { get; set; } = string.Empty;

    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("request_id")]
    public string RequestId { get; set; } = string.Empty;

    [JsonPropertyName("suggestions")]
    public List<string>? Suggestions { get; set; }

    [JsonPropertyName("retry_after")]
    public int? RetryAfter { get; set; } // Seconds, for 429 only
}
```

**Error Handling Middleware:**
```csharp
// api/Middleware/ErrorHandlingMiddleware.cs
public class ErrorHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ErrorHandlingMiddleware> _logger;

    public async Task InvokeAsync(HttpContext context)
    {
        var requestId = context.Request.Headers["X-Request-ID"].FirstOrDefault()
                       ?? Guid.NewGuid().ToString();
        context.Items["RequestId"] = requestId;

        try
        {
            await _next(context);
        }
        catch (QueryTimeoutException ex)
        {
            _logger.LogError(ex, "Query timeout for request {RequestId}", requestId);
            await WriteError(context, 504, "QUERY_TIMEOUT", "Query execution timed out", requestId);
        }
        catch (InsufficientFiltersException ex)
        {
            await WriteError(context, 400, "INSUFFICIENT_FILTERS", ex.Message, requestId);
        }
        // ... other exceptions
    }
}
```

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

#### Technical Implementation

**Chart Type Selection Decision Matrix:**
```typescript
// frontend/src/lib/chart-selection.ts
interface ChartSelectionInput {
  query: string;
  toolId: string;
  resultShape: {
    rowCount: number;
    hasTimeDimension: boolean;
    hasMultipleSeries: boolean;
    metricType: 'kpi' | 'time_series' | 'breakdown' | 'ranking';
  };
}

type ChartType = 'kpi' | 'line' | 'bar' | 'horizontal_bar' | 'pie' | 'donut' |
                  'stacked_bar' | 'scatter' | 'heatmap' | 'choropleth' |
                  'stacked_area' | 'waterfall' | 'bump' | 'table';

const CHART_SELECTION_RULES: Array<{
  condition: (input: ChartSelectionInput) => boolean;
  chartType: ChartType;
  confidence: number;
}> = [
  // KPI Card
  {
    condition: (i) => i.query.match(/average|total|sum/) && i.resultShape.rowCount === 1,
    chartType: 'kpi',
    confidence: 0.95,
  },

  // Line Chart (time series)
  {
    condition: (i) => i.query.match(/over time|trend|history/) && i.resultShape.hasTimeDimension,
    chartType: 'line',
    confidence: 0.90,
  },

  // Bar Chart (comparison)
  {
    condition: (i) => i.query.match(/compare|vs|versus/) && i.resultShape.rowCount >= 2 && i.resultShape.rowCount <= 5,
    chartType: 'bar',
    confidence: 0.85,
  },

  // Pie/Donut (proportion)
  {
    condition: (i) => i.query.match(/share|percentage|proportion/),
    chartType: 'donut',
    confidence: 0.85,
  },

  // Stacked Bar (segmented)
  {
    condition: (i) => i.query.match(/across|by|segmented/) && i.resultShape.hasMultipleSeries,
    chartType: 'stacked_bar',
    confidence: 0.80,
  },

  // Scatter Plot
  {
    condition: (i) => i.query.match(/correlation|relationship|scatter/),
    chartType: 'scatter',
    confidence: 0.90,
  },

  // Horizontal Bar (ranking)
  {
    condition: (i) => i.query.match(/ranking|top|bottom/),
    chartType: 'horizontal_bar',
    confidence: 0.90,
  },

  // Choropleth Map
  {
    condition: (i) => i.query.match(/geography|state|region/),
    chartType: 'choropleth',
    confidence: 0.85,
  },

  // Stacked Area (share trend over time)
  {
    condition: (i) => i.query.match(/share trend/) && i.resultShape.hasTimeDimension,
    chartType: 'stacked_area',
    confidence: 0.90,
  },

  // Waterfall (decomposition)
  {
    condition: (i) => i.query.match(/decomposition|driver|contribution/),
    chartType: 'waterfall',
    confidence: 0.85,
  },

  // Bump Chart (ranking change)
  {
    condition: (i) => i.query.match(/ranking change|how did ranking evolve/),
    chartType: 'bump',
    confidence: 0.85,
  },
];

export function selectChartType(input: ChartSelectionInput): { chartType: ChartType; confidence: number } {
  for (const rule of CHART_SELECTION_RULES) {
    if (rule.condition(input)) {
      return { chartType: rule.chartType, confidence: rule.confidence };
    }
  }

  // Default fallback
  if (input.resultShape.hasTimeDimension) {
    return { chartType: 'line', confidence: 0.6 };
  }
  return { chartType: 'bar', confidence: 0.6 };
}
```

### FR-5.2: Manual Override

- The system **SHALL** provide a manual chart type override control
- The override dropdown **SHALL** appear in a floating toolbar above the chart, aligned to the right
- Available options **SHALL** include: Auto, Table, Line, Bar (Vertical), Bar (Horizontal), Pie, Donut, Scatter
- When override differs from auto-selection, the system **SHALL** show a tooltip explaining the auto-selection reasoning

#### Technical Implementation

**Chart Toolbar Component:**
```typescript
// frontend/src/components/visualization/ChartToolbar.tsx
interface ChartToolbarProps {
  autoChartType: ChartType;
  selectedChartType: ChartType;
  onChartTypeChange: (type: ChartType) => void;
  showReasoning?: boolean;
}

const CHART_TYPE_OPTIONS: Array<{ value: ChartType; label: string; icon: string }> = [
  { value: 'auto', label: 'Auto', icon: 'sparkles' },
  { value: 'table', label: 'Table', icon: 'table' },
  { value: 'line', label: 'Line', icon: 'trending-up' },
  { value: 'bar', label: 'Bar (Vertical)', icon: 'bar-chart' },
  { value: 'horizontal_bar', label: 'Bar (Horizontal)', icon: 'bar-chart-horizontal' },
  { value: 'pie', label: 'Pie', icon: 'pie-chart' },
  { value: 'donut', label: 'Donut', icon: 'circle' },
  { value: 'scatter', label: 'Scatter', icon: 'scatter-chart' },
];
```

### FR-5.3: KPI Card Display

- For single aggregate values (e.g., "average Target spend"), the system **SHALL** render a KPI card instead of a chart
- The KPI card **SHALL** display: metric name, primary value, comparison to prior period, comparison to category average, year-over-year change %, and growth rate indicator
- KPI comparison to prior period **SHALL** be calculated as: ((current - prior) / prior) * 100
- Prior period selection logic: if query specifies a quarter, use same quarter prior year (YoY); if query specifies a month, use prior month (MoM)
- Category average comparison **SHALL** use unweighted average of all brands in the queried category
- The KPI card **SHALL** include a "View as table" toggle

#### Technical Implementation

**KPI Card Component:**
```typescript
// frontend/src/components/visualization/KPICard.tsx
interface KPIData {
  metricName: string;
  value: number;
  unit: string; // '%' | '$' | 'count'
  priorPeriodValue?: number;
  categoryAverage?: number;
  yoyChange?: number;
  momChange?: number;
}

interface KPICardProps {
  data: KPIData;
  periodType: 'quarter' | 'month' | 'year';
  onViewAsTable?: () => void;
}

// KPI Calculation Logic
function calculateKPIMetrics(result: QueryResponse, periodType: string): KPIData {
  const currentValue = result.data[0]?.value ?? 0;
  const priorValue = result.data[0]?.prior_period_value ?? 0;
  const categoryAvg = result.data[0]?.category_average ?? 0;

  return {
    metricName: result.metadata?.metric_name ?? 'Metric',
    value: currentValue,
    unit: result.metadata?.unit ?? '$',
    priorPeriodValue: priorValue,
    categoryAverage: categoryAvg,
    yoyChange: periodType === 'quarter' || periodType === 'year'
      ? ((currentValue - priorValue) / priorValue) * 100
      : undefined,
    momChange: periodType === 'month'
      ? ((currentValue - priorValue) / priorValue) * 100
      : undefined,
  };
}
```

### FR-5.4: Table Toggle

- The system **SHALL** provide a toggle between chart and table views
- Toggle states **SHALL** be: Chart only, Table only, Both (split view)
- For queries returning only tabular data, the system **SHALL** show table as primary

#### Technical Implementation

**View Mode Toggle:**
```typescript
// frontend/src/components/visualization/ViewModeToggle.tsx
type ViewMode = 'chart' | 'table' | 'both';

const VIEW_MODE_STORAGE_KEY = 'proteus_view_mode';

interface VisualizationContainerProps {
  data: QueryResponse;
  selectedChartType: ChartType;
  defaultViewMode?: ViewMode;
}
```

### FR-5.5: Chart Interactivity (Required)

- Charts **SHALL** support hover tooltips showing exact values
- Charts **SHALL** support legend toggling for multi-series data
- Charts **SHALL** support responsive resize

#### Technical Implementation

**ECharts Configuration:**
```typescript
// frontend/src/lib/echarts-config.ts
import * as echarts from 'echarts';

const BASE_CHART_OPTIONS = {
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#0F172A',
    borderColor: 'transparent',
    textStyle: { color: '#FFFFFF' },
    rounded: '8px',
  },
  legend: {
    bottom: 0,
    textStyle: { color: '#475569', fontSize: 12 },
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    containLabel: true,
  },
};

export function configureLineChart(data: any): echarts.EChartsOption {
  return {
    ...BASE_CHART_OPTIONS,
    xAxis: {
      type: 'category',
      axisLine: { lineStyle: { color: '#CBD5E1' } },
      axisLabel: { color: '#94A3B8' },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' } },
      axisLabel: { color: '#94A3B8' },
    },
    series: data.series.map((s: any) => ({
      type: 'line',
      data: s.data,
      smooth: true,
      itemStyle: { color: s.color },
    })),
  };
}
```

### FR-5.6: Chart Interactivity (Required)

- Charts **SHALL** support data zoom (slider) for time-series with 8+ data points
- Charts **SHALL** support click-to-highlight for legend items or bars
- Data zoom **SHALL** display a reset button when zoom is active

#### Technical Implementation

**Zoom Configuration:**
```typescript
// Time series with dataZoom
const ZOOM_CONFIG = {
  dataZoom: [
    {
      type: 'inside',
      start: 0,
      end: 100,
      minSpan: 10, // Minimum 10% of data visible
    },
    {
      type: 'slider',
      start: 0,
      end: 100,
      height: 20,
      bottom: 40,
      borderColor: 'transparent',
      backgroundColor: '#F1F5F9',
      fillerColor: '#E2E8F0',
      handleStyle: { color: '#2563EB' },
    },
  ],
};

interface ChartComponentProps {
  data: any;
  chartType: ChartType;
  enableZoom?: boolean; // True if time series with 8+ points
  onZoomReset?: () => void;
}
```

### FR-5.7: Result Set Handling

- For 1-100 rows: Full table display
- For 101-1,000 rows: Paginated (50 rows/page) or virtual scrolling
- For 1,001-10,000 rows: Aggregated view shown by default; raw data on demand
- For 10,000+ rows: Aggregation mandatory; raw data requires explicit query parameter

#### Technical Implementation

**Result Set Handler:**
```typescript
// frontend/src/lib/result-set-handler.ts
interface ResultSetConfig {
  rowCount: number;
  defaultView: 'full' | 'paginated' | 'aggregated';
  showRawDataOption: boolean;
}

function getResultSetConfig(rowCount: number): ResultSetConfig {
  if (rowCount <= 100) {
    return { rowCount, defaultView: 'full', showRawDataOption: false };
  }
  if (rowCount <= 1000) {
    return { rowCount, defaultView: 'paginated', showRawDataOption: true };
  }
  if (rowCount <= 10000) {
    return { rowCount, defaultView: 'aggregated', showRawDataOption: true };
  }
  return { rowCount, defaultView: 'aggregated', showRawDataOption: false };
}
```

### FR-5.8: Visualization Updates

- The canvas **SHALL** update with each new query result
- Prior visualizations **SHALL** be accessible via conversation history
- The chat sidebar **SHALL** display conversation history with thumbnail previews
- Thumbnails **SHALL** be 64x48px with 4:3 aspect ratio
- Thumbnails **SHALL** show a scaled-down rendering of the actual chart (SVG or canvas snapshot)
- Hover **SHALL** show a tooltip with the full query text and timestamp
- Click **SHALL** smooth-scroll to that message and re-render the visualization in the canvas

#### Technical Implementation

**Thumbnail Generation:**
```typescript
// frontend/src/hooks/use-visualization-history.ts
interface VisualizationHistoryItem {
  id: string;
  query: string;
  chartType: ChartType;
  thumbnailDataUrl: string; // SVG or canvas snapshot
  timestamp: Date;
  data: QueryResponse;
}

// Generate thumbnail using canvas snapshot
async function generateThumbnail(chartInstance: echarts.ECharts): Promise<string> {
  return chartInstance.getDataURL({
    type: 'png',
    pixelRatio: 0.5, // Smaller for thumbnail
    backgroundColor: '#FFFFFF',
  });
}
```

### FR-5.9: Chart Interaction Details

- Clicking a bar/segment **SHALL** show a detailed tooltip with the value AND offer a drill-down option via "Click to explore" prompt
- Chart header **SHALL** include an export dropdown (PNG, CSV) using native ECharts export methods
- Charts returning empty data **SHALL** display a centered empty state with "No data matches your query" message

#### Technical Implementation

**Drill-Down Handler:**
```typescript
// frontend/src/components/visualization/ChartComponent.tsx
const CHART_EVENT_HANDLERS = {
  click: (params: any, chartInstance: echarts.ECharts) => {
    if (params.componentType === 'series') {
      const drillDownOption = {
        ...params,
        drillDownPrompt: 'Click to explore',
        onDrillDown: () => handleDrillDown(params),
      };
      showDetailedTooltip(drillDownOption);
    }
  },
};

// Export functionality
const EXPORT_OPTIONS = [
  { format: 'png', label: 'Export as PNG' },
  { format: 'csv', label: 'Export as CSV' },
];
```

**Empty State:**
```typescript
// frontend/src/components/visualization/EmptyChart.tsx
const EmptyChart: React.FC = () => (
  <div className="flex items-center justify-center h-64 text-slate-400">
    <div className="text-center">
      <ChartBarIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
      <p className="text-sm">No data matches your query</p>
    </div>
  </div>
);
```

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

#### Technical Implementation

**TimescaleDB Schema:**
```sql
-- api/scripts/init-timescale.sql

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create dimensions tables (loaded from static config)
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    tier VARCHAR(20) NOT NULL, -- luxury, premium, mid-market, value
    archetype VARCHAR(50) NOT NULL, -- fast_casual, discount_retailer, department_store, subscription
    parent_company_id INTEGER REFERENCES brands(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    level1 VARCHAR(50) NOT NULL, -- Discretionary, Consumer Staples, Services, Transportation
    level2 VARCHAR(100) NOT NULL, -- Grocery, Restaurant, Apparel, Travel, etc.
    level3 VARCHAR(100) NOT NULL, -- Subcategory
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE geography (
    id SERIAL PRIMARY KEY,
    state_code CHAR(2) NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    cbsa_code VARCHAR(10),
    cbsa_name VARCHAR(200),
    urban_class VARCHAR(20), -- urban, suburban, rural
    zip3 CHAR(3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE generations (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    birth_year_start INTEGER NOT NULL,
    birth_year_end INTEGER NOT NULL
);

CREATE TABLE income_bands (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    min_income INTEGER NOT NULL,
    max_income INTEGER
);

-- Main transactions table (hypertable)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_timestamp TIMESTAMPTZ NOT NULL,
    panelist_id UUID NOT NULL,

    -- Foreign keys
    brand_id INTEGER NOT NULL REFERENCES brands(id),
    category_id INTEGER NOT NULL REFERENCES categories(id),
    geography_id INTEGER NOT NULL REFERENCES geography(id),

    -- Panelist demographics (denormalized for query performance)
    generation_id VARCHAR(20) NOT NULL REFERENCES generations(id),
    income_band_id VARCHAR(20) NOT NULL REFERENCES income_bands(id),

    -- Transaction details
    transaction_amount DECIMAL(10, 2) NOT NULL,
    card_type VARCHAR(20) NOT NULL, -- credit, debit, prepaid, corporate
    payment_network VARCHAR(20) NOT NULL, -- visa, mastercard, amex, discover
    channel VARCHAR(20) NOT NULL, -- online, in-store, mobile

    -- Time dimensions (for efficient aggregation)
    day_of_week VARCHAR(10) NOT NULL,
    hour_of_day INTEGER NOT NULL,

    -- Tenant for future multi-tenancy
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001',

    -- Composite index for filtering
    INDEX idx_transactions_timestamp_brand (transaction_timestamp, brand_id),
    INDEX idx_transactions_timestamp_category (transaction_timestamp, category_id),
    INDEX idx_transactions_timestamp_geo (transaction_timestamp, geography_id)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('transactions', 'transaction_timestamp',
    chunk_interval => INTERVAL '1 day',
    migrate_data => true
);

-- Enable compression after 30 days
ALTER TABLE transactions SET (
    timescaledb.compression,
    timescaledb.compression_segmentby = 'brand_id'
);

-- Compression policy: compress chunks older than 30 days
SELECT add_compression_policy('transactions', INTERVAL '30 days');

-- Retention policy: drop chunks older than 7 years
SELECT add_retention_policy('transactions', INTERVAL '7 years');

-- Create continuous aggregates

-- Daily rollup (90-day retention)
CREATE MATERIALIZED VIEW transactions_daily
WITH (timescaledb.continuous, timescaledb.refresh_lag = '1 day')
AS
SELECT
    time_bucket('1 day', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    geography_id,
    generation_id,
    income_band_id,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_spend,
    AVG(transaction_amount) AS avg_spend,
    COUNT(DISTINCT panelist_id) AS unique_panelists
FROM transactions
GROUP BY 1, 2, 3, 4, 5, 6;

SELECT add_continuous_aggregate_policy('transactions_daily',
    start_offset => INTERVAL '90 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour'
);

-- Weekly rollup (2-year retention)
CREATE MATERIALIZED VIEW transactions_weekly
WITH (timescaledb.continuous, timescaledb.refresh_lag = '7 days')
AS
SELECT
    time_bucket('7 days', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    geography_id,
    generation_id,
    income_band_id,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_spend,
    AVG(transaction_amount) AS avg_spend,
    COUNT(DISTINCT panelist_id) AS unique_panelists
FROM transactions
GROUP BY 1, 2, 3, 4, 5, 6;

-- Monthly rollup (7-year retention)
CREATE MATERIALIZED VIEW transactions_monthly
WITH (timescaledb.continuous, timescaledb.refresh_lag = '1 month')
AS
SELECT
    time_bucket('1 month', transaction_timestamp) AS bucket,
    brand_id,
    category_id,
    geography_id,
    generation_id,
    income_band_id,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_spend,
    AVG(transaction_amount) AS avg_spend,
    COUNT(DISTINCT panelist_id) AS unique_panelists
FROM transactions
GROUP BY 1, 2, 3, 4, 5, 6;

-- Market share continuous aggregate
CREATE MATERIALIZED VIEW market_share_daily
WITH (timescaledb.continuous, timescaledb.refresh_lag = '1 day')
AS
SELECT
    time_bucket('1 day', transaction_timestamp) AS bucket,
    category_id,
    brand_id,
    SUM(transaction_amount) AS brand_spend,
    SUM(SUM(transaction_amount)) OVER (PARTITION BY time_bucket('1 day', transaction_timestamp), category_id) AS category_total_spend,
    SUM(transaction_amount)::DECIMAL / NULLIF(SUM(SUM(transaction_amount)) OVER (PARTITION BY time_bucket('1 day', transaction_timestamp), category_id), 0) * 100 AS market_share_pct
FROM transactions
GROUP BY 1, 2, 3;
```

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

#### Technical Implementation

**Panelist Schema:**
```sql
-- Panelist table
CREATE TABLE panelists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    income_band_id VARCHAR(20) NOT NULL REFERENCES income_bands(id),
    generation_id VARCHAR(20) NOT NULL REFERENCES generations(id),
    geography_id INTEGER NOT NULL REFERENCES geography(id),
    panel_start_date DATE NOT NULL,
    panel_weight DECIMAL(10, 4) NOT NULL, -- Calibrated to represent US population
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Panel weights indexed for fast lookup
CREATE INDEX idx_panelists_weight ON panelists(panel_weight);
```

### FR-6.10: Data Quality Metrics

The following quality metrics **SHALL** be measured and reported during data generation validation:
- Coefficient of variation for daily transaction volumes: target 0.3-0.6
- Gini coefficient for brand market share: target 0.55-0.70
- Mean absolute deviation for category proportions vs. BEA consumer expenditure data: <5%
- Weekend-to-weekday ratio by category: within 10% of survey benchmarks
- Transaction count distribution **SHALL** follow expected frequency patterns per panelist
- Zero-inflation **SHALL** be modeled appropriately for panelists with sparse transaction history

#### Technical Implementation

**Faker Seed Strategy for Reproducibility:**
```python
# backend/src/data/generate_synthetic_data.py
from faker import Faker
import numpy as np

class SyntheticDataGenerator:
    DEFAULT_SEED = 42  # Documented for eval consistency

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed
        self.faker = Faker(seed)
        np.random.seed(seed)

    def generate_transaction_amount(
        self,
        category_tier: str,
        income_band_multiplier: float
    ) -> float:
        """
        Generate log-normal transaction amount.
        Category-specific mu/sigma from FR-6.6
        """
        params = {
            'essential': (3.0, 0.8),
            'mid_tier': (3.5, 1.0),
            'premium': (4.2, 1.2),
            'dining': (3.2, 0.9),
            'fast_food': (2.2, 0.6),
        }
        mu, sigma = params.get(category_tier, (3.0, 0.8))
        base_amount = np.random.lognormal(mu, sigma)
        return round(base_amount * income_band_multiplier, 2)

    def apply_seasonal_adjustment(
        self,
        base_amount: float,
        date: datetime,
        category: str
    ) -> float:
        """Apply Q4 spike, January normalization, back-to-school, weekend patterns."""
        month = date.month
        day_of_week = date.strftime('%A')

        # Q4 holiday spike (Nov-Dec)
        if month in [11, 12]:
            spike = np.random.uniform(0.25, 0.40)
            base_amount *= (1 + spike)
            # December peak (15-24)
            if month == 12 and 15 <= date.day <= 24:
                base_amount *= np.random.uniform(1.0, 1.4)  # Additional +60-100% vs prior week

        # January normalization
        if month == 1:
            base_amount *= np.random.uniform(0.75, 0.85)

        # Back-to-school (Aug-Sep for school categories)
        if month in [8, 9] and 'school' in category.lower():
            base_amount *= np.random.uniform(1.2, 1.35)

        # Weekend retail boost (Saturday)
        if day_of_week == 'Saturday' and 'retail' in category.lower():
            base_amount *= np.random.uniform(1.30, 1.35)

        return base_amount
```

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

#### Technical Implementation

**Test Fixture Schema:**
```python
# backend/src/eval/models.py
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
from enum import Enum

class ComplexityLevel(str, Enum):
    LEVEL_1_SIMPLE = "level_1_simple"
    LEVEL_2_MODERATE = "level_2_moderate"
    LEVEL_3_COMPLEX = "level_3_complex"
    LEVEL_4_MULTI_TOOL = "level_4_multi_tool"
    LEVEL_5_AMBIGUOUS = "level_5_ambiguous"

class ExpectedParameter(BaseModel):
    dimension: str
    values: List[str]
    tolerance: Optional[float] = None  # For numeric values

class TestFixture(BaseModel):
    id: str
    description: str
    natural_language_input: str
    expected_tools: List[str]  # Tool IDs
    expected_parameters: List[ExpectedParameter]
    expected_result_characteristics: Dict[str, any]
    complexity_level: ComplexityLevel
    synonym_variations: List[str] = []  # Alternative phrasings
    category: str  # For grouping analysis

class EvalResult(BaseModel):
    fixture_id: str
    trial_number: int
    temperature: float = 0.0
    actual_tools: List[str]
    actual_parameters: Dict[str, List[str]]
    tool_selection_correct: bool
    dimension_extraction_correct: bool
    visualization_correct: Optional[bool] = None
    end_to_end_correct: bool
    latency_ms: int
    error: Optional[str] = None

class EvalRun(BaseModel):
    run_id: str
    timestamp: datetime
    fixture_results: List[EvalResult]
    aggregate_metrics: Dict[str, float]
```

### FR-7.5: Anomaly Injection for Eval

- The eval framework **SHALL** include known anomalies for detection testing:
  - Seasonal patterns (holiday spikes, back-to-school)
  - One-time events (COVID-style channel shift)
  - Secular trends (online channel growth 2019-2024)

#### Technical Implementation

**Anomaly Test Cases:**
```python
# backend/src/eval/anomalies.py
class AnomalyTestCase(BaseModel):
    name: str
    description: str
    query: str
    expected_impact: str  # e.g., "Increased Q4 volume for retail brands"
    injected_anomaly: Dict[str, Any]

ANOMALY_TEST_CASES = [
    AnomalyTestCase(
        name="holiday_spike_2024",
        query="Show retail market share trends Q4 2024",
        expected_impact="Visible spike in December for retail categories",
        injected_anomaly={"type": "seasonal", "months": [11, 12], "magnitude": 1.35}
    ),
    AnomalyTestCase(
        name="covid_channel_shift",
        query="Compare online vs in-store spending 2020 vs 2023",
        expected_impact="Dramatic online increase in 2020, normalizing by 2023",
        injected_anomaly={"type": "channel_shift", "year": 2020, "online_multiplier": 2.5}
    ),
]
```

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

#### Technical Implementation

**Internal Model Configuration:**
```python
# backend/src/config.py
from pydantic_settings import BaseSettings
from typing import Dict

class ModelConfig(BaseSettings):
    # Internal pipeline models (not user-configurable)
    TOOL_SELECTION_MODEL: str = "minimax/text-01"
    DIMENSION_EXTRACTION_MODEL: str = "moonshot/kimi-k2"
    PLANNER_MODEL: str = "google/gemini-2.0-flash"
    EMBEDDING_MODEL: str = "openai/text-embedding-3-small"

    # Response generation model (user-configurable)
    RESPONSE_GENERATION_MODEL: str = "openai/gpt-4o"

    class Config:
        env_prefix = "MODEL_"

INTERNAL_MODELS = {
    "tool_selection": ModelConfig().TOOL_SELECTION_MODEL,
    "dimension_extraction": ModelConfig().DIMENSION_EXTRACTION_MODEL,
    "planner": ModelConfig().PLANNER_MODEL,
    "embedding": ModelConfig().EMBEDDING_MODEL,
}

USER_CONFIGURABLE_MODELS = {
    "openai/gpt-4o": {"provider": "openai", "supports_function_calling": True},
    "google/gemini-2.0-flash": {"provider": "google", "supports_function_calling": True},
    "anthropic/claude-3.5-sonnet": {"provider": "anthropic", "supports_function_calling": True},
    "moonshot/kimi-k2": {"provider": "kimi", "supports_function_calling": True},
    "minimax/text-01": {"provider": "minimax", "supports_function_calling": True},
    "google/gemini-2.5-pro": {"provider": "glm", "supports_function_calling": True},
}
```

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

#### Technical Implementation

**Provider Normalization Layer:**
```python
# backend/src/api/normalizers.py
from abc import ABC, abstractmethod
import json

class ProviderResponseNormalizer(ABC):
    @abstractmethod
    def parse_function_calls(self, raw_response: any) -> List[Dict[str, Any]]:
        """Extract function calls from provider-specific response format."""
        pass

    @abstractmethod
    def normalize_json_mode(self, raw_response: str) -> Dict[str, Any]:
        """Normalize JSON mode response to consistent format."""
        pass

class OpenAINormalizer(ProviderResponseNormalizer):
    def parse_function_calls(self, raw_response: any) -> List[Dict[str, Any]]:
        # OpenAI uses tool_calls in message
        return [
            {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}
            for tc in raw_response.choices[0].message.tool_calls or []
        ]

class AnthropicNormalizer(ProviderResponseNormalizer):
    def parse_function_calls(self, raw_response: any) -> List[Dict[str, Any]]:
        # Anthropic uses Claude tool use format
        return [
            {"name": tc.name, "input": tc.input}
            for tc in raw_response.content if tc.type == "tool_use"
        ]

class GoogleNormalizer(ProviderResponseNormalizer):
    def parse_function_calls(self, raw_response: any) -> List[Dict[str, Any]]:
        # Google uses function_call in candidate
        candidate = raw_response.candidates[0]
        if hasattr(candidate, 'function_calls'):
            return [
                {"name": fc.name, "arguments": fc.args}
                for fc in candidate.function_calls
            ]
        return []

class NormalizerRegistry:
    _normalizers: Dict[str, ProviderResponseNormalizer] = {
        "openai": OpenAINormalizer(),
        "anthropic": AnthropicNormalizer(),
        "google": GoogleNormalizer(),
        "kimi": OpenAINormalizer(),  # Compatible with OpenAI format
        "minimax": OpenAINormalizer(),
        "glm": GoogleNormalizer(),  # Compatible with Google format
    }

    @classmethod
    def get_normalizer(cls, provider: str) -> ProviderResponseNormalizer:
        return cls._normalizers.get(provider.lower(), OpenAINormalizer())
```

### FR-8.5: Provider Normalization

- The system **SHALL** normalize structured output across providers
- JSON mode / function calling consistency **SHALL** be achieved via adapter layer
- Parse failures **SHALL** trigger retry once with same model before returning user-friendly error
- After retry exhaustion, the system **SHALL** return a user-friendly error with request ID

#### Technical Implementation

**Retry Logic with Normalization:**
```python
# backend/src/api/openrouter.py
class OpenRouterClient:
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1.0  # seconds

    def call_with_retry(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        provider = self._get_provider(model)
        normalizer = NormalizerRegistry.get_normalizer(provider)

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._make_request(model, messages, temperature, max_tokens)
                return normalizer.parse_function_calls(response)
            except (json.JSONDecodeError, ValidationError) as parse_error:
                if attempt == self.MAX_RETRIES - 1:
                    raise UserFriendlyError(
                        code="PARSE_FAILURE",
                        message="Unable to process model response. Please try again.",
                        request_id=self._request_id
                    )
                # Exponential backoff with jitter
                await asyncio.sleep(self.RETRY_DELAY_BASE * (2 ** attempt) + random.random())
```

### FR-8.6: LLM Failure Handling

- The pipeline **SHALL** implement exponential backoff with jitter for transient failures (max 3 retries)
- After retry exhaustion, the system **SHALL** return a user-friendly error with request ID
- Circuit breaker pattern **SHALL** be implemented to prevent cascade failures during provider outages
- Critical paths (tool selection, dimension extraction) **SHALL** have fallback to conservative defaults

#### Technical Implementation

**Circuit Breaker and Fallback:**
```python
# backend/src/api/circuit_breaker.py
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject immediately
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.last_failure_time = None

    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_attempt(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN

# Fallback for critical paths
class CriticalPathFallback:
    TOOL_SELECTION_FALLBACK = ["market_share_trend"]  # Most generic tool
    DIMENSION_EXTRACTION_FALLBACK = {"brand": [], "period": "last_quarter"}

    @staticmethod
    def get_fallback_tool() -> str:
        return CriticalPathFallback.TOOL_SELECTION_FALLBACK[0]
```

### FR-8.7: Prompt Management

- Prompt templates **SHALL** be versioned and stored in configuration
- Each API request **SHALL** log the prompt version used for reproducibility
- The observability panel **SHALL** display the rendered prompt for debugging

#### Technical Implementation

**Prompt Versioning:**
```python
# backend/src/agent/prompts.py
from datetime import datetime
from pydantic import BaseModel

class PromptVersion(BaseModel):
    version: str  # e.g., "v1.0.0"
    template_name: str
    template_content: str
    variables: List[str]
    created_at: datetime
    created_by: str
    changelog: Optional[str] = None

class PromptManager:
    def __init__(self, prompt_dir: str = "./config/prompts"):
        self.prompts = self._load_prompts(prompt_dir)

    def get_prompt(self, name: str, version: str = "latest") -> str:
        prompt = self.prompts.get(name, {}).get(version)
        if not prompt:
            raise ValueError(f"Prompt {name} version {version} not found")
        return prompt.template_content

    def render_prompt(self, name: str, variables: Dict[str, Any]) -> Tuple[str, PromptVersion]:
        """Returns (rendered_prompt, version_info)."""
        version = self._get_latest_version(name)
        template = version.template_content
        rendered = template.format(**variables)
        return rendered, version

# Prompt storage structure
# backend/config/prompts/
#   tool_selection/
#     v1.0.0.yaml
#     v1.1.0.yaml
#   dimension_extraction/
#     v1.0.0.yaml
#   planner/
#     v1.0.0.yaml
```

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

## Appendix: Architecture Overview

### Component Tree

```
proteus/
├── docker-compose.yml
├── frontend/                          # Next.js + CopilotKit
│   ├── src/
│   │   ├── app/
│   │   │   ├── chat/page.tsx        # Main chat interface
│   │   │   ├── api/copilotkit/      # CopilotKit proxy endpoint
│   │   │   └── api/auth/            # Better Auth endpoints
│   │   ├── components/
│   │   │   ├── chat/                # Chat UI components
│   │   │   ├── visualization/        # ECharts components
│   │   │   └── observability/       # Debug/observability UI
│   │   ├── hooks/                   # Custom React hooks
│   │   └── lib/
│   │       ├── chart-selection.ts   # Auto chart-type selection
│   │       └── echarts-config.ts    # ECharts configuration
│   └── __tests__/
│
├── backend/                          # FastAPI + LangGraph
│   ├── src/
│   │   ├── main.py                  # FastAPI entry + CopilotKit endpoint
│   │   ├── agent/
│   │   │   ├── graph.py             # LangGraph pipeline
│   │   │   ├── state.py             # Agent state schema
│   │   │   ├── nodes.py             # Pipeline nodes
│   │   │   └── prompts.py           # Prompt templates
│   │   ├── api/
│   │   │   ├── router.py            # API routes
│   │   │   ├── models/              # Pydantic models
│   │   │   └── openrouter.py        # OpenRouter client
│   │   └── config.py                # Settings
│   └── tests/
│
├── api/                              # ASP.NET Core Data API
│   ├── Repositories/
│   │   ├── IQueryRepository.cs      # Repository interface
│   │   └── TimescaleRepository.cs   # TimescaleDB implementation
│   ├── Models/
│   │   ├── QueryModels.cs            # Request/response DTOs
│   │   └── ErrorResponse.cs          # Error DTOs
│   ├── Endpoints/
│   │   ├── QueryEndpoint.cs         # POST /api/query
│   │   ├── BatchQueryEndpoint.cs     # POST /api/query/batch
│   │   └── DimensionEndpoints.cs     # GET /api/dimensions/*
│   ├── Services/
│   │   ├── AggregationLevelResolver.cs
│   │   └── QueryGuardrails.cs
│   ├── Validators/
│   │   └── QueryGuardrails.cs
│   ├── Middleware/
│   │   └── ErrorHandlingMiddleware.cs
│   ├── config/dimensions/            # Static dimension enumerations
│   └── scripts/
│       └── init-timescale.sql        # TimescaleDB setup
│
└── scripts/
    └── init-db.sql                   # Database initialization
```

### Data Flow Diagram

```
User Query (Natural Language)
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                               │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ CopilotKit ChatSidebar                                     │   │
│  │ - Receives user input                                      │   │
│  │ - Streams response via SSE                                 │   │
│  │ - Renders visualizations                                    │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
         │ HTTP /api/copilotkit
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI + LangGraph)                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ Planner     │───▶│ Tool        │───▶│ Dimension            │  │
│  │ Node        │    │ Selection   │    │ Extraction           │  │
│  │ (GLM-4-Air) │    │ (MiniMax-01) │    │ (Kimi-K2, parallel)  │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                  │                 │
│                                                  ▼                 │
│                         ┌─────────────────────────────────────┐   │
│                         │ HITL Clarification (if needed)       │   │
│                         └─────────────────────────────────────┘   │
│                                                  │                 │
│                                                  ▼                 │
│                         ┌─────────────────────────────────────┐   │
│                         │ Response Generation                 │   │
│                         │ (User-selected model, streaming)     │   │
│                         └─────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
         │ HTTP POST /api/query or /api/query/batch
         │ X-Request-ID header
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Data API (ASP.NET Core)                                          │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Repository Pattern                                         │   │
│  │ - Validates query guardrails                               │   │
│  │ - Resolves aggregation level                               │   │
│  │ - Queries TimescaleDB via continuous aggregates            │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  TimescaleDB                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ transactions │  │ transactions_│  │ transactions_monthly  │   │
│  │ (hypertable)│  │ weekly       │  │ (continuous aggregate)│   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### API Contract Summary

| Endpoint | Method | Purpose | Key Features |
|----------|--------|---------|---------------|
| `/api/query` | POST | Single tool query | Guardrails, aggregation level auto-resolve, pagination |
| `/api/query/batch` | POST | Multi-tool query | Parallel execution, per-query latency |
| `/api/dimensions/{dim}` | GET | Dimension enumeration | 24hr in-memory cache, no DB hit |
| `/health` | GET | Health check | - |

### Security Considerations

- **Input Validation**: All API inputs validated via Zod (frontend) and Pydantic (backend)
- **SQL Injection**: Parameterized queries via Dapper; no raw SQL concatenation
- **Rate Limiting**: 429 responses with Retry-After header for rate limit errors
- **Request Tracing**: UUID request_id propagated via X-Request-ID header
- **Error Messages**: User-friendly, no stack traces or raw exception messages
- **Multi-tenancy**: tenant_id column ready for RLS (Phase 2)

### Observability Data Flow

```
Pipeline Stage
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ ObservabilityMetadata                                        │
│ - request_id                                                 │
│ - pipeline_stages: [{name, latency_ms, status}]            │
│ - total_latency_ms                                          │
│ - model_used                                                 │
│ - prompt_version                                             │
│ - rag_candidates: [{tool_id, similarity}]                  │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Level 1: Summary in chat header                              │
│ Level 2: JSON viewer with RAG candidates                     │
│ Level 3: Full raw request/response                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Schema Cross-References

| Schema | Location | Used By |
|--------|----------|---------|
| `QueryRequest` | FR-4.1 | `POST /api/query`, Batch Endpoint |
| `QueryResponse` | FR-4.1 | All query endpoints |
| `ErrorResponse` | FR-4.7 | All error responses |
| `ToolDefinition` | FR-2.1 | Tool Registry, RAG Retrieval |
| `ToolSelectionResult` | FR-2.4 | Tool Selection Node |
| `ExecutionPlan` | FR-2.6 | Planner Node |
| `ExtractedDimensions` | FR-3.1 | Dimension Extraction |
| `DimensionValidationResult` | FR-3.5 | Dimension Validation |
| `DimensionConflict` | FR-3.6 | Conflict Resolution |
| `ChartSelectionInput` | FR-5.1 | Auto Chart-Type Selection |
| `TestFixture` | FR-7.4 | Eval Framework |
| `ProviderResponseNormalizer` | FR-8.5 | Provider Normalization |

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
