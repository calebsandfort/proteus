# Unit 8: Response Generation & Streaming

> **Status:** Implemented
> **FR Coverage:** FR-1.2, FR-8.3, NFR-1.4
> **Dependencies:** IU-7 (LangGraph Agent Graph)

## Overview

Unit 8 implements the response generation and streaming layer of the Proteus agent pipeline. It bridges the gap between the LangGraph agent execution (IU-7) and the frontend chat interface (IU-9) by providing SSE-based streaming responses, multi-turn conversation context management, natural language synthesis, and user-configurable model selection.

The unit sits at the critical user-facing boundary of the AI pipeline, handling three key concerns: streaming real-time tokens to the frontend via Server-Sent Events (NFR-1.4), maintaining session context for multi-turn conversations with reference resolution (FR-1.2), and synthesizing natural language answers with visualization recommendations using a user-selected model (FR-8.3).

## Functionality Implemented

- **Multi-Turn Conversation Context** (FR-1.2) — Session context management with sliding window maintaining 75% of model's context limit, minimum 4 turns preserved, session anchor (first query) always retained, tool result reference ID tagging for "that"/"those" resolution, topic change detection, and summarization at 80% threshold
- **Response Synthesis** (FR-8.3) — ResponseSynthesizer with natural language generation from tool results, ModelSelector with provider fallback logic for non-function-calling models, VisualizationRecommender for chart type decisions based on data patterns
- **SSE Streaming** (NFR-1.4) — Server-Sent Events streaming with ObservabilityMetadata tracking pipeline stage timing, SSEEventFormatter for proper event formatting, first-token latency tracking to verify 500ms requirement

## Implementation Details

### Technology Stack and Frameworks
- **FastAPI** — Web framework for the `/api/copilotkit` endpoint and StreamingResponse
- **Pydantic** — Data validation for streaming models (ObservabilityMetadata, SSEToolResult, SSEClarification, SSEStreamChunk, SSEDone)
- **asyncio** — Async generator pattern for SSE streaming

### Key Architectural Patterns

**Streaming Pipeline Pattern:**
```
AgentGraph (IU-7) → stream_agent_response → StreamingResponse → SSE → Frontend
```

The `stream_agent_response` async generator yields SSE-formatted events as they become available, enabling the frontend to display tokens progressively rather than waiting for complete responses.

**Session Context Sliding Window:**
- `MAX_CONTEXT_RATIO = 0.75` — Maintains messages up to 75% of context window
- `MIN_TURNS_TO_KEEP = 4` — Minimum turns preserved regardless of size
- `SUMMARIZATION_THRESHOLD = 0.80` — Triggers summarization compression
- Session anchor (first query) is always preserved even if older than window

**Model Selector with Fallback:**
The `ModelSelector` class handles the FR-8.3 requirement that users can select from six providers. When a selected model doesn't support function calling, it falls back to `text-embedding-3-small` for embeddings + strongest available model for generation, with a user warning.

### Design Decisions

**Reference ID Tagging:** Tool results are tagged with internal reference IDs (`referenceId`) to support natural language references like "show me more about that" or "compare those brands." This enables the frontend to build interactive elements that resolve these references.

**Observability Metadata:** The `done` SSE event includes `ObservabilityMetadata` with `pipeline_stages` timing and `first_token_latency_ms` to verify the NFR-1.4 requirement that first token appears within 500ms of pipeline completion.

**SSE Event Types:**
| Event Type | Event Name | Purpose |
|------------|------------|---------|
| `tool_result` | SSEToolResult | Tool execution result |
| `clarification` | SSEClarification | HITL clarification request |
| `stream` | SSEStreamChunk | Token stream chunk |
| `done` | SSEDone | Final metadata and completion |

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/agent/context.py` | Session context management with sliding window, ConversationTurn, SessionContext, ToolResult models |
| `backend/src/agent/response.py` | ResponseSynthesizer, ModelSelector, VisualizationRecommender for FR-8.3 |
| `backend/src/agent/streaming.py` | SSE streaming handler with ObservabilityMetadata, SSEEventFormatter, stream_agent_response |
| `backend/src/api/router.py` | FastAPI router with `/api/copilotkit` POST endpoint |

## Integration Points

### This Unit Provides

**To Frontend (IU-9):**
- `POST /api/copilotkit` — SSE endpoint accepting `{ messages, session_id, selected_model }`
- SSE events: `tool_result`, `clarification`, `stream`, `done`, `error`
- `ObservabilityMetadata` with pipeline stage timing

**To IU-7 (Agent Graph):**
- Imports `run_agent_graph` and `HITLClarification` from IU-7

**To IU-6 (OpenRouter):**
- Imports `OpenRouterClient` for response synthesis
- Imports `model_config` and `USER_CONFIGURABLE_MODELS` for model selection

### This Unit Depends On

**From IU-7:**
- `run_agent_graph(query, session_id, conversation_history)` — Agent execution
- `HITLClarification` model for clarification events

**From IU-6:**
- `OpenRouterClient` for LLM calls in response synthesis
- Model configuration for user-configurable models

**From Frontend (IU-9) — Reverse Dependency:**
- Sends SSE events consumed by CopilotKit ChatSidebar

## Usage Guide

### SSE Endpoint

```python
# POST /api/copilotkit
# Request:
{
    "messages": [{"role": "user", "content": "Show me Nike vs Adidas"}],
    "session_id": "abc-123",
    "selected_model": "openai/gpt-4o"
}

# Response: SSE stream of events
event: tool_result
data: {"referenceId": "ref-1", "toolName": "brand_comparison", "data": {...}}

event: stream
data: "Nike has gained"

event: done
data: {"total_latency_ms": 1234, "first_token_latency_ms": 456, ...}
```

### Session Context Management

```python
from src.agent.context import SessionContext, ConversationTurn, ToolResult

# Create session context
session = SessionContext(session_id="abc-123")

# Add user turn
session.add_turn(role="user", content="Show me Nike vs Adidas")

# Add assistant turn with tool results
session.add_turn(
    role="assistant",
    content="Here are the results:",
    tool_results=[ToolResult(referenceId="ref-1", tool_name="brand_comparison", data={})]
)

# Check if summarization needed (80% threshold)
if session.needs_summarization():
    session.summarize()
```

### Model Selection

```python
from src.agent.response import ModelSelector

selector = ModelSelector()

# Select a model
model_info = selector.select_model("openai/gpt-4o")

# Check if fallback was used
if model_info.used_fallback:
    print(f"Warning: {model_info.warning}")
```

### Verifying First Token Latency

The `ObservabilityMetadata.first_token_latency_ms` tracks time from pipeline completion to first token, enabling verification of the NFR-1.4 500ms requirement:

```python
# In streaming.py
first_token_time = time.perf_counter()
# ... after first token yielded
first_token_latency_ms = int((time.perf_counter() - first_token_time) * 1000)
```

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `44fb07a` | 2026-04-03 | feat: implement Unit 8 Response Generation & Streaming |
| `138200f` | 2026-04-03 | test: add Unit 8 contract tests for Response Generation & Streaming |
