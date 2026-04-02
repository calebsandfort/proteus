# Unit 7: LangGraph Agent Graph

> **Status:** Implemented
> **FR Coverage:** FR-2.4, FR-2.5, FR-2.6
> **Dependencies:** IU-4 (Tool Registry & RAG), IU-5 (Dimension Extraction), IU-6 (OpenRouter Integration)

## Overview

Unit 7 implements the core LangGraph-based agent graph that orchestrates tool selection, HITL clarification, and multi-tool query planning for the Proteus consumer analytics system. The agent receives natural language queries, retrieves relevant tools via RAG (IU-4), extracts dimensions (IU-5), selects the optimal tool(s) using a weighted confidence scoring system, and executes either single or multi-tool queries with parallel dimension extraction. The agent uses MiniMax-Text-01 for tool selection and GLM-4-Air for planning decisions, both accessed via OpenRouter (IU-6).

The graph architecture follows a directed flow: init → retrieval → dimension_extraction → tool_selection → [planner] → [execution] → response → done. When confidence falls below 0.70, the graph branches to a clarification subgraph for human-in-the-loop resolution before continuing execution.

## Functionality Implemented

- **Tool Selection with Weighted Confidence Scoring** (FR-2.4) — Uses MiniMax-Text-01 to select tools from top-8 RAG candidates. Confidence is a weighted combination: 25% RAG similarity + 35% LLM selection + 40% dimension match score. Thresholds: >=0.85 proceed, 0.70-0.84 proceed with competing candidates shown, <0.70 route to HITL clarification.
- **HITL Clarification Handling** (FR-2.5) — When confidence is low, generates structured clarification responses with 2-3 options including interpreted parameters, labels, and reasoning. Supports ambiguity types: tool_selection, dimension_value, and conflicting_dimensions.
- **Multi-Tool Query Planning** (FR-2.6) — Dedicated planner node using GLM-4-Air determines whether a query requires single or multi-tool execution. For multi-tool queries, outputs a structured ExecutionPlan with tool ordering, dimension dependencies, estimated latency, and execution mode (parallel/sequential).
- **Parallel Dimension Extraction** (FR-2.6) — Independent dimension extractions execute in parallel. Dependent extractions (e.g., brand resolution affecting category inference) execute sequentially per the planner's dependency graph.
- **Agent State Management** — AgentState TypedDict tracks all fields throughout the graph execution. SessionContext provides session-level tracking. State is persisted via LangGraph's MemorySaver checkpointer.

## Implementation Details

**Technology Stack:**
- LangGraph 1.x via `langgraph` package for graph orchestration and state management
- `langchain_core.messages` for message handling
- Pydantic v2 for all state and output models
- OpenRouter client (IU-6) for LLM calls

**Key Architectural Patterns:**
- **State Graph Pattern**: All agent state flows through a LangGraph StateGraph with typed state dict. Nodes are async functions that read from and write to state.
- **Conditional Edge Routing**: Graph uses conditional edges to branch based on confidence thresholds and query complexity (single-tool vs. multi-tool).
- **Dependency Injection**: ToolRetriever (IU-4), DimensionExtractionGraph (IU-5), and OpenRouterClient (IU-6) are injected into node functions rather than imported directly.
- **Checkpointer**: MemorySaver provides conversational memory across turns within a session.

**Graph Node Architecture:**
| Node | Purpose |
|------|---------|
| `retrieve_node` | RAG retrieval of top-8 candidate tools |
| `dimension_extraction_node` | Parallel dimension extraction from query |
| `tool_selection_node` | LLM-based tool selection with confidence scoring |
| `planner_node` | GLM-4-Air planning for multi-tool queries |
| `execution_node` | Execute selected tool(s) with parameter resolution |
| `clarification_node` | Generate HITL clarification options |
| `response_node` | Generate natural language response |
| `done_node` | Finalize and return AgentOutput |

**Confidence Scoring Formula:**
```
confidence = 0.25 * rag_similarity + 0.35 * llm_selection + 0.40 * dimension_match
```
- Dimension match score: full match (all required dims) = 1.0, partial = (matched_required / total_required) * 0.8 + optional bonus

**Conditional Edge Routing:**
- `tool_selection` → `planner` when confidence >= 0.70 AND is_multi_tool
- `tool_selection` → `execution` when confidence >= 0.70 AND NOT is_multi_tool
- `tool_selection` → `clarification` when confidence < 0.70
- `clarification` → `awaiting_clarification` → `tool_selection` after user responds

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/agent/state.py` (333 lines) | AgentState TypedDict, SessionContext, and all Pydantic models (ClarificationOption, HITLClarification, ToolSelectionResult, PlannedTool, ExecutionPlan, AgentOutput). Includes `compute_dimension_match_score` function. |
| `backend/src/agent/graph.py` (425 lines) | AgentGraph class with `run_agent_graph` async function. Defines all nodes, conditional edges, and graph compilation. |
| `backend/src/agent/nodes.py` (1423 lines) | All node implementations: retrieve_node, dimension_extraction_node, tool_selection_node, planner_node, execution_node, clarification_node, response_node, done_node. Includes node-specific Pydantic models. |
| `backend/src/agent/prompts.py` (263 lines) | PLANNER_PROMPT (GLM-4-Air), TOOL_SELECTION_PROMPT (MiniMax-Text-01), EXTRACTION_PROMPT, CLARIFICATION_PROMPT |
| `backend/tests/test_agent_graph.py` (357 lines) | Integration tests for the full graph flow |
| `backend/tests/test_agent_nodes.py` (1259 lines) | Unit tests for each node function |
| `backend/tests/test_agent_state.py` (737 lines) | Tests for state models and compute_dimension_match_score |
| `backend/tests/test_agent_prompts.py` (182 lines) | Tests for prompt templates |

## Integration Points

### This Unit Provides
- `AgentGraph` class with `run_agent_graph(query, session_id, conversation_history)` async function
- `AgentOutput` Pydantic model as the final output
- `ToolSelectionResult`, `HITLClarification`, `ExecutionPlan` for downstream consumption (IU-8)
- Confidence scoring with competing candidates exposed for observability

### This Unit Depends On
- **IU-4 (Tool Registry & RAG)**: `ToolRetriever` class for RAG-based tool retrieval. Receives `RetrievedTool` objects as input.
- **IU-5 (Dimension Extraction)**: `DimensionExtractionGraph` for extracting dimensions from natural language queries. Produces `ExtractedDimensions` dict.
- **IU-6 (OpenRouter Integration)**: `OpenRouterClient` for LLM calls to MiniMax-Text-01 (tool selection) and GLM-4-Air (planning).

## Usage Guide

**Running the Agent:**
```python
from src.agent.graph import AgentGraph
from src.agent.state import AgentOutput

graph = AgentGraph()
result: AgentOutput = await graph.run_agent_graph(
    query="Show spending trends for Kroger and Walmart",
    session_id="user-123-session-1",
    conversation_history=[{"role": "user", "content": "..."}]
)
```

**Key Configuration:**
- `OPENROUTER_API_KEY` environment variable required for LLM calls
- Dimension extraction and tool selection models configurable via OpenRouter client
- Confidence thresholds configurable in `tool_selection_node`

**Verification:**
```bash
cd backend && pytest tests/test_agent_graph.py tests/test_agent_nodes.py -v
```

The agent returns an `AgentOutput` containing:
- `final_response`: Natural language response string
- `tool_results`: Dict of tool_id → result (for multi-tool)
- `selected_tools`: List of selected tool IDs
- `clarification`: HITLClarification if confidence was low
- `execution_plan`: ExecutionPlan if multi-tool

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `e58fb3c` | 2026-04-01 | feat: implement Unit 7 LangGraph Agent Graph (FR-2.4-2.6) |
| `823a153` | 2026-03-26 | fix: update dependencies and resolve copilotkit/langgraph conflict |
