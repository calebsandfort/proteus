# Unit 4: Tool Registry & RAG Retrieval

> **Status:** Implemented
> **FR Coverage:** FR-2.1, FR-2.2, FR-2.3
> **Dependencies:** IU-3 (ASP.NET Core Data API)

## Overview

Unit 4 implements the Tool Registry and RAG-based retrieval system for the Proteus analytics platform. This unit is responsible for maintaining a registry of 14 core data retrieval tools, storing their embeddings for semantic search, and providing a retrieval interface that returns the top-8 most relevant tools given a natural language query. The system uses OpenAI's `text-embedding-3-small` model via the OpenRouter proxy to generate tool embeddings, enabling semantic matching between user queries and tool capabilities.

This unit sits at the heart of the AI pipeline — it receives queries from the LangGraph agent (Unit 7), retrieves candidate tools based on semantic similarity, and passes those candidates back for tool selection. The tool registry is YAML-driven, meaning tools can be added, modified, or deprecated without requiring pipeline code changes.

## Functionality Implemented

- **Tool Registry Management** (FR-2.1) — `ToolRegistry` class with `register()`, `get()`, `list_active()`, and `search_by_embedding()` methods; Pydantic `ToolDefinition`, `ToolParameter`, and `ToolOutputSchema` models; versioning and deprecation support
- **14 Core Tool Definitions** (FR-2.2) — 6 P0 tools (market_share_trend, brand_comparison, yoy_growth_analysis, same_store_sales, category_trends, wallet_share), 4 P1 tools (cross_shopping_overlap, demographic_breakdown, geographic_breakdown, customer_retention), 4 P2 tools (top_n_rankings, channel_analysis, basket_analysis, promotional_sensitivity)
- **RAG-Based Semantic Retrieval** (FR-2.3) — `EmbeddingRetriever` implementation of abstract `ToolRetriever`; cosine similarity with 0.70 threshold; top-8 retrieval; HITL routing when no candidate exceeds threshold; brand aliases separated into lookup table (not in tool definition)
- **OpenRouter Integration** (FR-2.3) — `OpenRouterClient` with `embed_texts()` using `openai/text-embedding-3-small`; shared between Unit 4 and Unit 6

## Implementation Details

**Technology Stack:** Python 3.11+, Pydantic v2 for data models, NumPy for vector operations, OpenAI SDK via OpenRouter proxy, PyYAML for tool definition files.

**Key Architectural Patterns:**
- **Repository Pattern** — `ToolRegistry` acts as an in-memory repository of `ToolDefinition` objects with embedding-backed search
- **Abstract Base Class** — `ToolRetriever` ABC defines the retrieval interface, with `EmbeddingRetriever` as the concrete implementation
- **YAML-Driven Configuration** — All 14 tool definitions live in `backend/src/config/tools/*.yaml`, loaded at startup; no code changes needed to add/modify tools
- **Shared Client** — `OpenRouterClient` in `backend/src/api/openrouter.py` is co-owned by Unit 4 and Unit 6, providing both embedding generation and LLM chat completion

**Design Decisions:**
- Tool definitions store **only high-level capability descriptions** — dimension value enumerations (brand names, state codes) are explicitly excluded as they dilute the retrieval signal
- Brand aliases are stored separately in a lookup structure rather than in the tool YAML, keeping tool definitions focused on semantic capability matching
- The cosine similarity function explicitly casts the return value to `float` (was previously returning `np.float32` which violated the declared return type annotation)
- Mock embeddings (`mock_embeddings.json`) are provided for parallel development — downstream units can test against pre-computed embeddings without calling the OpenRouter API

**Configuration Contracts:**
- `OPENROUTER_API_KEY` environment variable required
- Embedding model: `openai/text-embedding-3-small`
- Similarity threshold: `0.70`
- Retrieval top-k: `8`

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/api/models/tool.py` | Pydantic models: `ToolDefinition`, `ToolParameter`, `ToolOutputSchema` |
| `backend/src/agent/registry.py` | `ToolRegistry` class with register/get/list_active/search_by_embedding and `_cosine_similarity` |
| `backend/src/agent/retrieval.py` | `ToolRetriever` ABC and `EmbeddingRetriever` implementation |
| `backend/src/api/openrouter.py` | `OpenRouterClient` with `embed_texts()` and `call_with_retry()` (shared with Unit 6) |
| `backend/src/config/tools/*.yaml` | 14 YAML files (one per tool): market_share_trend, brand_comparison, yoy_growth_analysis, same_store_sales, category_trends, wallet_share, cross_shopping_overlap, demographic_breakdown, geographic_breakdown, customer_retention, top_n_rankings, channel_analysis, basket_analysis, promotional_sensitivity |
| `backend/src/config/tools/mock_embeddings.json` | Pre-computed embeddings for parallel development without API calls |
| `backend/.env.example` | Documents `OPENROUTER_API_KEY` requirement |
| `backend/tests/test_tool_models.py` | Unit tests for Pydantic model validation |
| `backend/tests/test_registry.py` | Unit tests for ToolRegistry class |
| `backend/tests/test_retrieval.py` | Unit tests for EmbeddingRetriever |
| `backend/tests/test_openrouter_client.py` | Unit tests for OpenRouterClient |
| `backend/tests/integration/test_contract_unit4_unit6.py` | Contract tests verifying Unit 4 / Unit 6 integration seams |

## Integration Points

### This Unit Provides
- `ToolRegistry` — callable Python object holding all registered tool definitions and their embeddings; accessible via `registry.get(tool_id)`, `registry.list_active()`, `registry.search_by_embedding(query_embedding, top_k, threshold)`
- `EmbeddingRetriever` — returns `List[RetrievedTool]` with `tool_id`, `tool_definition`, `similarity`, `rank`; used by Unit 7's tool selection node
- `OpenRouterClient.embed_texts()` — shared embedding generation used by both Unit 4 (tool retrieval) and Unit 6 (prompt management)
- 14 tool YAML definitions — loaded at startup, can be hot-reloaded

### This Unit Depends On
- **IU-3 (ASP.NET Core Data API)** — FR-2.1 notes this as a dependency; the tool definitions reference dimension types (brand, period, geo, category, generation, income_band) that match the dimension enumerations from IU-3's API contracts
- **OpenRouter API** — requires valid `OPENROUTER_API_KEY` environment variable for live embedding generation

## Usage Guide

**Loading the Tool Registry:**
```python
from backend.src.agent.registry import ToolRegistry
from backend.src.agent.retrieval import EmbeddingRetriever
from backend.src.api.openrouter import OpenRouterClient

# Initialize
client = OpenRouterClient(api_key=os.environ["OPENROUTER_API_KEY"])
registry = ToolRegistry()
retriever = EmbeddingRetriever(registry=registry, openrouter_client=client)

# List active tools
tools = registry.list_active()

# Search by embedding
query_embedding = client.embed_texts(["show me brand market share trends"])[0]
results = retriever.retrieve(query="show me brand market share trends", query_embedding=query_embedding, top_k=8, similarity_threshold=0.70)
```

**Adding a New Tool:**
1. Create a new YAML file in `backend/src/config/tools/your_tool.yaml` following the schema pattern
2. Register it with the registry (done automatically at startup via the YAML loader)
3. The tool becomes available in `list_active()` and is indexed for retrieval

**Verifying the Unit is Working:**
```bash
# Run unit tests
cd backend && python -m pytest tests/test_registry.py tests/test_retrieval.py tests/test_tool_models.py -v

# Run integration contract tests
python -m pytest tests/integration/test_contract_unit4_unit6.py -v
```

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `4fd64eb` | 2026-03-30 | feat: add Unit 4 Tool Registry and RAG retrieval system |
| `9f2ffa6` | 2026-03-30 | Merge branch 'unit-4' |
| `6fc8667` | 2026-03-30 | fix: cast cosine similarity return to Python float in ToolRegistry |
