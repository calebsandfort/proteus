# Unit 6: OpenRouter Integration

> **Status:** Implemented
> **FR Coverage:** FR-8.1-8.7
> **Dependencies:** IU-3 (ASP.NET Core Data API)

## Overview

Unit 6 implements the OpenRouter integration layer for the Proteus analytics platform. OpenRouter serves as a unified LLM gateway that routes all AI pipeline calls through a single interface, supporting multiple providers (OpenAI, Google, Anthropic, Kimi, MiniMax, GLM) without direct provider integrations. This abstraction enables model-agnostic pipeline architecture where swapping models requires only configuration changes, not code modifications.

The implementation provides circuit breaker patterns for fault tolerance, exponential backoff retry logic for transient failures, provider-specific response normalization for consistent structured outputs, and versioned prompt management for reproducibility. Unit 6 is a critical dependency for Unit 5 (Dimension Extraction Pipeline) and Unit 7 (LangGraph Agent Graph), both of which rely on the OpenRouter client for LLM calls.

## Functionality Implemented

- **OpenRouter Gateway** (FR-8.1) — All LLM calls route through OpenRouter with no direct provider integrations
- **Internal Pipeline Models** (FR-8.2) — Tool selection (MiniMax-Text-01), dimension extraction (Kimi-K2), planner (GLM-4-Air), embedding (text-embedding-3-small)
- **Response Generation Model** (FR-8.3) — User-configurable model selection exposed via config
- **Model-Agnostic Pipeline** (FR-8.4) — Provider-agnostic normalization layer enabling model swapping via configuration only
- **Provider Normalization** (FR-8.5) — Provider-specific response normalizers for OpenAI, Anthropic, Google, Kimi, MiniMax, GLM with retry on parse failure
- **Circuit Breaker & Retry** (FR-8.6) — Exponential backoff with jitter (3 retries max), circuit breaker pattern for cascade failure prevention, critical path fallback defaults
- **Versioned Prompt Management** (FR-8.7) — PromptManager with version tracking, logged prompt version per request, support for observability panel display

## Implementation Details

### Technology Stack and Frameworks

- **Python 3.11+** with asyncio for concurrent operations
- **httpx** for async HTTP requests to OpenRouter API
- **pydantic** for data validation and configuration models
- **pytest** and **pytest-asyncio** for unit testing

### Key Architectural Patterns

**Provider Normalization Pattern:**
Each supported provider (OpenAI, Anthropic, Google, Kimi, MiniMax, GLM) has a dedicated normalizer class that standardizes response formats to a common interface. The `NormalizerRegistry` dispatches to the appropriate normalizer based on provider string, with `OpenAINormalizer` as the default fallback.

**Circuit Breaker Pattern:**
The `CircuitBreaker` class implements the circuit breaker pattern with three states (CLOSED, OPEN, HALF_OPEN). When failure threshold is exceeded, the circuit opens and fast-fails requests without calling the provider. After a recovery timeout, it enters half-open state to test if the provider has recovered.

**Exponential Backoff with Jitter:**
Retry logic uses exponential backoff formula: `delay = RETRY_DELAY_BASE * (2 ** attempt) + random.random()`, capped at 3 retries. This prevents thundering herd issues while providing eventual success for transient failures.

**Prompt Versioning:**
`PromptManager` maintains a registry of versioned prompt templates. Each request logs the prompt version for reproducibility, and the observability panel can display the rendered prompt for debugging.

### Design Decisions

**Why unified gateway over direct integrations?**
Direct provider integrations would require code changes when swapping models. OpenRouter provides a unified API surface with consistent response handling, reducing integration maintenance burden and enabling runtime model configuration.

**Why provider-specific normalizers?**
Different providers return structured outputs differently (OpenAI uses function calling JSON, Anthropic uses XML-like tags, Google uses JSON schema). Each normalizer handles provider-specific parsing quirks and returns a standardized response dict.

**Why circuit breaker?**
During provider outages, without circuit breakers, the system would accumulate pending requests and exhaust resources. Circuit breakers fail fast and allow graceful degradation with fallback defaults.

### Key Configuration Structures

```python
INTERNAL_MODELS = {
    "tool_selection": "minimax/text-01",
    "dimension_extraction": "moonshot/kimi-k2",
    "planner": "google/gemini-2.0-flash",
    "embedding": "openai/text-embedding-3-small",
}

RESPONSE_GENERATION_MODELS = [
    "openai/gpt-4o",
    "google/gemini-2.0-flash",
    "anthropic/claude-3-5-sonnet",
    "moonshot/kimi-k2",
    "minimax/text-01",
    "deepseek/deepseek-chat-v3",
]
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/api/openrouter.py` | OpenRouterClient with `call_with_retry` and `embed_texts` methods, provider routing, retry logic |
| `backend/src/api/normalizers.py` | NormalizerRegistry and provider-specific normalizers (OpenAI, Anthropic, Google, Kimi, MiniMax, GLM) |
| `backend/src/api/circuit_breaker.py` | CircuitBreaker class with state machine (CLOSED/OPEN/HALF_OPEN), failure tracking, recovery timeout |
| `backend/src/agent/prompts.py` | PromptManager for versioned prompt templates, prompt versioning and logging |
| `backend/src/config.py` | ModelConfig with internal and user-configurable model settings, model registry |
| `backend/tests/test_openrouter.py` | Unit tests for OpenRouterClient including retry behavior, embed_texts |
| `backend/tests/test_normalizers.py` | Unit tests for all provider normalizers with sample responses |
| `backend/tests/test_circuit_breaker.py` | Unit tests for circuit breaker state transitions and failure handling |
| `backend/tests/test_prompt_manager.py` | Unit tests for PromptManager versioning and template rendering |
| `backend/tests/test_config.py` | Unit tests for ModelConfig initialization and model lookup |

## Integration Points

### This Unit Provides

- **`OpenRouterClient`** class — Main client for LLM calls with `call_with_retry()` and `embed_texts()` methods
- **`NormalizerRegistry.get_normalizer(provider)`** — Returns appropriate `ProviderResponseNormalizer` for a provider
- **`CircuitBreaker`** — Fault tolerance component with `call()`, `open()`, `close()`, `get_fallback_tool()` methods
- **`PromptManager`** — Versioned prompt templates with `get_prompt()`, `list_versions()`, `render()` methods
- **`INTERNAL_MODELS`** dict — Pre-configured internal pipeline model assignments
- **`RESPONSE_GENERATION_MODELS`** list — User-selectable response generation models

### This Unit Depends On

- **IU-3 (ASP.NET Core Data API)** — Type definitions and API contracts
- **OPENAI_API_KEY** environment variable — OpenRouter API authentication
- **httpx** library for HTTP communication

## Usage Guide

### Making an LLM Call

```python
from backend.src.api.openrouter import OpenRouterClient

client = OpenRouterClient()

response = await client.call_with_retry(
    model="minimax/text-01",
    messages=[{"role": "user", "content": "Extract brands from: What was Walmart's Q4 revenue?"}],
    temperature=0.0,
    max_tokens=2048
)
```

### Getting Text Embeddings

```python
embeddings = await client.embed_texts(
    texts=["Walmart revenue", "Target sales growth"],
    model="openai/text-embedding-3-small"
)
```

### Using Provider Normalizers

```python
from backend.src.api.normalizers import NormalizerRegistry

normalizer = NormalizerRegistry.get_normalizer("anthropic")
normalized_response = normalizer.normalize(raw_response)
```

### Circuit Breaker Usage

```python
from backend.src.api.circuit_breaker import CircuitBreaker, CircuitState

cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
result = await cb.call(some_function, *args, **kwargs)

if cb.state == CircuitState.OPEN:
    fallback = CircuitBreaker.get_fallback_tool()
```

### Prompt Management

```python
from backend.src.agent.prompts import PromptManager

pm = PromptManager()
prompt = pm.get_prompt("tool_selection", version="1.0")
rendered = pm.render("tool_selection", context={"query": "What brands?"})
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenRouter API key (required) |
| `OPENROUTER_BASE_URL` | OpenRouter base URL (optional, defaults to `https://openrouter.ai/api/v1`) |
| `OPENROUTER_MAX_RETRIES` | Max retries per call (default: 3) |

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `7235828` | 2026-03-30 | feat: implement Unit 6 OpenRouter integration |
| `6fc8667` | 2026-03-30 | fix: cast cosine similarity return to Python float in ToolRegistry |
