# AI/NLP Architecture SME Analysis: Proteus

## Executive Summary

Proteus is a natural-language chat interface for querying consumer transaction data. The system translates plain-English queries into structured tool calls against a parameterized REST API. This analysis addresses all `[SME:AIWorkflow]` questions regarding conversation context management, tool selection, dimension extraction, eval framework design, model selection, and latency optimization.

---

## 1. Conversation Context Management

**Question:** How should conversation context be managed across multi-turn interactions? Should the full message history be passed to the tool selection node, or should a summarization step compress prior context to stay within token limits? What's the optimal context window strategy for maintaining coherence while keeping latency low?

### Recommended Approach: Tiered Context Strategy

**Primary Recommendation: Sliding Window with Summary Anchoring**

Do not pass full message history to every pipeline stage. Instead, implement a tiered approach:

1. **Sliding Window (Recent Context):** Pass the last 5-8 conversation turns directly. This covers ~2,000-3,000 tokens and handles immediate follow-ups like "drill down on Q3" or "compare to last year."

2. **Semantic Compression (Distant Context):** For sessions exceeding the sliding window, generate a compressed semantic summary of earlier turns. Use a dedicated lightweight model call (e.g., Haiku-class) to produce a 200-300 token abstract of prior query intent and key results.

3. **Tool Selection Node Context:** Pass only:
   - Compressed session summary (if >5 turns)
   - Current query
   - Previously selected tool(s) and their results (critical for follow-ups)

This avoids contaminating tool selection with verbose historical text while preserving intent coherence.

### Token Budget Allocation Per Stage

| Stage | Context Budget | Rationale |
|-------|---------------|-----------|
| Tool Selection | 4,000 tokens | Needs room for tool definitions + query + context |
| Dimension Extraction | 2,000 tokens | Parallel nodes only need current query + their dimension category |
| Response Generation | 6,000 tokens | Needs full result context + explanation space |

### Latency Consideration

- Summary generation adds ~200-400ms latency. Cache summaries and regenerate only when the conversation drifts to a new topic (detected via tool change).
- For Phase 1, simpler approach acceptable: pass last 6 turns with explicit section markers separating "Prior Context" from "Current Query."

---

## 2. Tool Definition Retrieval

**Question:** What embedding model and similarity threshold work best for tool definition retrieval? How many candidate tools should be passed to the LLM for final selection — is there a sweet spot between too few (missed matches) and too many (decision fatigue / token waste)?

### Embedding Model Recommendation

**Use:** `text-embedding-3-small` (OpenAI) or `ember` (Meta) via OpenRouter

Rationale:
- 256-512 dimensional embeddings sufficient for 10-50 tool definitions
- Both models offer good reranking performance for retrieval tasks
- Avoid larger models (e.g., `text-embedding-3-large`) — marginal accuracy gain does not justify 4x cost increase for small corpus

### Similarity Threshold Strategy

| Threshold | Behavior | Risk |
|-----------|----------|------|
| >0.85 | High precision, may miss relevant tools | Missing valid matches |
| 0.70-0.85 | Balanced precision/recall | Moderate noise |
| <0.70 | High recall, significant noise | LLM selection degraded |

**Recommendation:** Use **0.75 as initial threshold**, pass top-8 candidates to LLM selector. The LLM is the actual decision-maker; RAG narrows the haystack, it does not make the final call.

### Optimal Candidate Set Size

**Pass 5-8 candidates to the LLM tool selector.**

- Fewer than 5: Misses legitimate alternatives when query spans multiple tools
- More than 8: Token cost escalates without meaningful accuracy improvement
- 8 candidates with ~300 token definitions = ~2,400 tokens + system prompt + query = ~3,500 tokens total

### Tool Definition Structure for Optimal Retrieval

**Question:** How should tool definitions be structured for optimal retrieval?

### Recommended Tool Definition Schema

```json
{
  "id": "market_share_comparison",
  "name": "Market Share Comparison",
  "description": "Compares transaction volume or spend share between brands within a category",
  "capabilities": [
    "Brand-vs-brand market share",
    "Category-wide share breakdown",
    "Share trend over time"
  ],
  "dimensions": {
    "required": ["brands", "category", "time_range"],
    "optional": ["geography", "generation", "channel"]
  },
  "example_queries": [
    "What is Target's market share in grocery?",
    "How is Nike performing against Adidas in apparel?",
    "Show me the top 5 brands by transaction volume in electronics"
  ],
  "output_schema": {
    "type": "categorical_breakdown",
    "visualization_hint": "bar_chart | pie_chart"
  },
  "aliases": ["competitive share", "brand performance", "market position"]
}
```

**Key metadata that improves retrieval:**
1. **Example queries** — Highest impact. Include natural phrasing variations analysts use
2. **Capability statements** — Captures intent space beyond description
3. **Aliases** — Handles synonyms ("market share" vs "competitive position")
4. **Dimension enumeration** — Helps RAG match when query contains dimension keywords
5. **Output schema hint** — Useful for visualization auto-selection downstream

**Do NOT include:** Dimension value enumerations (e.g., list of all brands). These dilute retrieval signal.

---

## 3. Multi-Tool Query Strategy

**Question:** What's the best strategy for handling multi-tool queries where a single user question requires orchestrating calls to multiple tools (e.g., "Compare Target's market share to their customer demographics in Texas")? Should this be a planner node or handled by the tool selection LLM directly?

### Recommended Architecture: Planner Node

**Implement a dedicated planner/orchestrator node upstream of tool selection.**

```
User Query → Planner Node → [Tool A: market_share] + [Tool B: demographics]
                                        ↓
                              Parallel Execution
                                        ↓
                              Result Synthesizer → Response
```

### Why a Planner Node (Not Direct LLM Routing)

1. **Separation of concerns:** The planner reasons about query decomposition; the selector reasons about tool fitness. Mixing them reduces debuggability.

2. **Explicit multi-tool detection:** The planner outputs a structured `execution_plan`:
   ```json
   {
     "tools": [
       {"tool_id": "market_share", "parameters": {...}},
       {"tool_id": "demographics", "parameters": {...}}
     ],
     "synthesis_needed": true,
     "synthesis_instruction": "Compare the market share findings with demographic skew"
   }
   ```

3. **Streaming readiness:** Planner can output the execution plan first, then stream tool results as they complete. Improves perceived latency.

4. **Eval tractability:** Easier to evaluate "did planner correctly decompose?" vs. "did correct tools get called?" independently.

### Planner Node Implementation

- Use a **chain-of-thought prompt** that explicitly reasons: "Does this query require one or multiple tools? If multiple, what is the relationship between results?"
- Max tokens: 500 for plan output (structured JSON)
- Model: Use cost-effective model (MiniMax Haiku) for planning; correctness matters more than creativity here

### Fallback: Single-Tool with Clarification

If the planner identifies multiple plausible decompositions (ambiguous multi-tool), route to HITL clarification rather than guessing.

---

## 4. Dimension Extraction Specialization

**Question:** Which dimension categories benefit most from specialized extraction logic vs. general-purpose LLM extraction?

### Dimension Category Classification

| Category | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| **Time Range** | Specialized parser | Deterministic logic handles "last quarter," "Q3 2024," "YTD" reliably |
| **Geography** | Specialized normalizer | State abbreviations, metro name resolution, zip-to-region mapping |
| **Brand/Merchant** | LLM + fuzzy matching | Aliases, misspellings, parent company resolution (Walmart vs. Sam's Club) |
| **Category** | LLM + enum lookup | Hierarchical category taxonomy |
| **Generation** | LLM + enum lookup | Gen Z, Millennial, etc. are well-defined |
| **Income Band** | LLM with validation | Ranges like "$50K-75K" need parsing |
| **Card Type** | Simple enum match | credit, debit — limited options |
| **Channel** | Simple enum match | online, in-store |
| **Aggregation Level** | LLM | daily, weekly, monthly, quarterly, annual |

### Parallel Execution Architecture

```
                    ┌─ Time Range Parser
                    ├─ Geography Normalizer
Query ──→ Splitter ──┼─ Brand Matcher (LLM + fuzzy)
                    ├─ Category Lookup
                    └─ ... (dimension-specific nodes)
                           │
                           ▼
                    Parameter Assembler ──→ API Call
```

**Key benefits:**
- Time/geo parsing is fast (~10-50ms) and deterministic
- LLM extraction runs in parallel, reducing wall-clock time
- Failures are isolated — one bad dimension extraction doesn't block others

### Time Range Parser Specifics

Implement a deterministic parser for common patterns:
- Relative: "last quarter," "YTD," "last 6 months," "past year"
- Absolute: "Q3 2024," "January 2025," "2023-2024"
- Hybrid: "last quarter of 2024" → `{start: "2024-10-01", end: "2024-12-31"}`

Use a lightweight date utility library (e.g., `date-fns`) + regex for known patterns. Only route to LLM for genuinely ambiguous cases.

---

## 5. Dimension Conflict Handling

**Question:** How should we handle dimension conflicts or contradictions within a single query (e.g., "Target sales in Texas and California last month and last year")?

### Conflict Resolution Strategy: Structured Disambiguation

**Do NOT silently generate multiple API calls or make best-effort guesses.**

The system should explicitly surface the conflict to the user:

```
┌─────────────────────────────────────────────────────────┐
│  I see two possible interpretations of your query:      │
│                                                         │
│  A) Target sales in TX + CA combined, comparing          │
│     last month vs. last year                            │
│     → 1 API call with geo=[TX,CA], time=LY+LM          │
│                                                         │
│  B) Separate results for TX and CA, each showing        │
│     last month vs. last year                            │
│     → 2 API calls, results presented side-by-side       │
│                                                         │
│  Which would you like, or would you like both?           │
└─────────────────────────────────────────────────────────┘
```

### Implementation Approach

1. **Conflict Detection:** When the dimension assembler detects mutually incompatible constraints on the same dimension (multiple values for mutually exclusive temporal/geographic scopes), flag a conflict.

2. **Structured Clarification:** Return a HITL turn with a formatted disambiguation prompt showing the alternative interpretations.

3. **Clarification Options:** Limit to 2-3 options; if more plausible interpretations exist, pick the 2 most reasonable and offer "Other..."

### What NOT To Do

- Do not pick interpretation A arbitrarily (user may have meant B)
- Do not silently generate multiple calls and merge results (unexpected behavior)
- Do not discard one constraint without告知 (data loss)

---

## 6. Evaluation Framework Design

**Question:** What's the minimum eval suite size to produce statistically meaningful accuracy metrics? How should test cases be distributed across query complexity levels?

### Minimum Eval Suite Size

**Minimum: 200 test cases** for meaningful accuracy differentiation.

Statistical reasoning:
- To detect a 5% difference in accuracy between models (90% vs 85%), with 80% power: ~n=350 per arm
- For Phase 1 with relative comparison (pass/fail on eval suite): 200 cases provides ±7% confidence interval
- Start with 100 cases if timeline constrained, but recognize limited statistical power

### Distribution Across Query Complexity

| Complexity Level | % of Suite | Count | Rationale |
|-----------------|------------|-------|-----------|
| Simple single-tool, single-dimension | 30% | 60 | Baseline correctness |
| Moderate single-tool, 2-4 dimensions | 35% | 70 | Typical analyst queries |
| Complex single-tool, 5+ dimensions | 15% | 30 | Advanced queries |
| Multi-tool queries | 10% | 20 | Planner correctness |
| Ambiguous / clarification cases | 10% | 20 | HITL appropriateness |

### Eval Dimensions and Metrics

| Dimension | Metric | Target |
|-----------|--------|--------|
| Tool selection accuracy | % correct tool(s) selected | ≥90% |
| Dimension extraction accuracy | % correct parameter values | ≥85% |
| End-to-end result correctness | Pass/fail on structured assertions | ≥80% |
| Clarification appropriateness | Human-rated (0-2 scale) | Mean ≥1.5 |

### Clarification Pathway Evaluation

**Question:** How should we handle eval for the clarification pathway? What constitutes a "correct" clarification?

### Clarification Correctness Criteria

Do NOT evaluate clarification as purely pass/fail. Use a rubric:

| Score | Definition |
|-------|------------|
| 2 - Correct | System asked for clarification when appropriate; question was semantically relevant and specific |
| 1 - Partially Correct | System asked, but question was vague or missed a key ambiguity |
| 0 - Incorrect | System should not have asked (could have resolved) OR asked for obviously wrong reason |

**Eval process:**
- Human raters evaluate clarification turns
- Weight: 2-point answers count as "system behaved correctly"
- Report mean score, not just pass rate

**Examples:**
- Query: "Show me Target sales" → Score 2 if asks "Which time period?"
- Query: "Target vs Walmart in Texas last quarter" → Score 0 if asks about time period (obvious)

---

## 7. Model Selection for Tool Selection and Extraction

**Question:** Which specific models from Kimi, MiniMax, and GLM perform best for structured tool selection and parameter extraction tasks? What evaluation criteria should be used to benchmark them?

### Recommended Models by Task

| Task | Recommended Model | Context Length | Structured Output |
|------|------------------|----------------|-------------------|
| Tool Selection | MiniMax-Text-01 | 256K | Strong JSON mode |
| Dimension Extraction | Kimi-Open-Assistant | 128K | Excellent function calling |
| Planner (Multi-tool) | GLM-4-Air | 128K | Good with structured prompts |

### Benchmarking Criteria (Priority Order)

1. **Structured Output Reliability (40%)**
   - JSON mode / function calling consistency
   - Does output parse correctly >95% of the time?
   - Evaluation: Run 100 test prompts, count parse failures

2. **Task Accuracy (30%)**
   - Tool selection: % correct on eval suite
   - Dimension extraction: % correct parameters
   - Measure against human-annotated ground truth

3. **Latency (20%)**
   - p50 and p95 response time for structured output
   - Target: p95 <2s for tool selection, <1.5s for dimension extraction

4. **Cost per Query (10%)**
   - Normalize to cost per successful structured output
   - Important for scale, secondary for Phase 1

### Normalization Across Providers

**Question:** Are there meaningful differences in how these models handle structured output (JSON mode, function calling)? Should the pipeline normalize across different providers' function-calling conventions?

### Yes — Normalize at the Pipeline Level

Provider differences in function calling are significant:

| Provider | Mechanism | Schema Strictness |
|----------|-----------|-------------------|
| OpenAI | `tools` + `tool_calls` | Strict |
| Anthropic | `tools` + `stop_reason` | Strict |
| Kimi | Custom function calling | Moderate |
| GLM | `tools` parameter | Moderate |
| MiniMax | JSON mode fallback | Loose |

**Recommendation:** Implement a **provider-agnostic normalization layer:**

```
┌─────────────┐
│ Tool Selection Node
└──────┬──────┘
       │ provider_call(model, prompt, output_schema)
              │
              ▼
       ┌──────────────────┐
       │ Normalizer Layer │ ← Unified interface
       └────────┬─────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
OpenAI      Kimi        MiniMax
Adapter    Adapter       Adapter
```

**Benefits:**
- Swap models without changing pipeline logic
- Handle parse failures uniformly (retry with same model)
- Add new providers by implementing adapter interface

---

## 8. Latency Breakdown and Bottleneck Analysis

**Question:** What's the expected latency breakdown across pipeline stages? Where are the bottlenecks, and should we implement streaming at the response generation stage to improve perceived performance?

### Expected Latency Budget (Single-Tool Query)

| Stage | Expected Latency | Notes |
|-------|-----------------|-------|
| RAG retrieval (embedding + search) | 50-100ms | 50 tool definitions, vector search |
| Tool selection LLM call | 400-800ms | Network + model inference |
| Dimension extraction (parallel) | 600-1200ms | 3-5 dimension nodes, LLM calls |
| API call (ASP.NET Core) | 200-500ms | Database query |
| Response generation | 800-1500ms | Final LLM call |
| **Total (non-streaming)** | **2,050-4,100ms** | |

**Bottleneck:** Response generation and dimension extraction (LLM calls)

### Streaming Architecture Recommendation

**Implement streaming for response generation only.**

```
Query → Pipeline (non-streaming) → API Call → Result
                                            ↓
                                    Streaming Response
                                            ↓
                              "Based on the data, Target's market
                               share in grocery was..."
                               [streamed tokens appear]
```

**Why streaming only response generation:**
- Earlier stages (tool selection, extraction) must complete before results exist
- Streaming partial tool calls is not useful — need full parameter set
- Response generation is the largest latency component and most visually impactful

**Implementation:**
- Use Server-Sent Events (SSE) for streaming
- First token should appear within 500ms of pipeline completion
- Show "Analyzing..." state during non-streamed stages

### 5-Second SLA Achievement

For the 5-second end-to-end target:
- Non-streaming path must complete in <4s (reserving 1s for network variance)
- Current estimate: 2-4s — achievable with model optimization
- Multi-tool queries: Stream results per tool as they complete, partial results visible

---

## 9. Additional AI/NLP Architecture Considerations

### Error Handling and Graceful Degradation

1. **LLM Parse Failure:** If structured output fails to parse, retry once with same model. On second failure, log error and return user-friendly "I had trouble understanding that query" message.

2. **API Timeout:** If ASP.NET Core API exceeds 500ms, return partial result with "Results may be incomplete" warning. Do not block entire response.

3. **RAG Miss:** If top candidate similarity is very low (<0.5), surface HITL: "I'm not sure which analysis fits your question. Could you rephrase?"

### Observability Implementation

The observability toggle should expose:
- Selected tool(s) and confidence scores
- Extracted dimensions with confidence
- Raw API request/response
- Latency per stage

This is valuable for power users and essential for debugging eval failures.

---

## Questions for Other SMEs

### For UXDesigner (UX/UI Design):

1. **Observability panel default state:** You have a question about this in the HLRD. From an AI pipeline perspective, I recommend a **collapsed sidebar toggle** (not per-message expansion). Per-message expansion would interrupt conversation flow and complicate streaming implementation. The toggle should show a slide-out panel that doesn't reflow the main canvas.

2. **Chart type override:** Should users be able to manually override the auto-selected chart type? From an AI perspective, this is low-cost to implement — just expose a dropdown after visualization renders. Recommend adding this for power users.

### For DataScientist (Data Analytics):

1. **Dimension completeness:** The HLRD mentions dimensions like "generation," "income band," "card type" — what statistical distributions should be embedded for these to produce analytically plausible results? Specifically: should income band show expected correlation with transaction amount and brand preferences?

2. **Aggregation level detection:** When a user asks about "spending trends," how does the system decide between daily, weekly, or monthly granularity? Is there a domain rule (e.g., "queries spanning >3 months default to monthly") or should this be inferred from query wording?

3. **Result validation:** What basic sanity checks should the AI pipeline perform on API results before rendering? For example: detecting negative values where none expected, or results that are statistical outliers given the query dimensions.

### For IntegrationEngineer (Multi-Tenancy & API Design):

1. **API contract for multi-tool queries:** If the planner node generates multiple API calls, should these be parallelized by the frontend (fire-and-forget) or should the ASP.NET Core API expose a batch endpoint that handles parallelization internally? Parallel execution in the frontend may violate the 500ms API SLA.

2. **Dimension enumeration endpoint:** Should the API expose an endpoint that lists valid values for each dimension (e.g., GET /dimensions/brands, GET /dimensions/states)? This would allow the AI pipeline to validate extracted dimensions against allowed values before constructing the query.

3. **Result pagination:** For queries that return large result sets (e.g., daily transactions for 2 years across 100 brands), should the API handle aggregation or return raw data? From AI perspective, raw data is harder to visualize; prefer pre-aggregated results.

### For MarketAnalyst (Market Research):

1. **Tool prioritization:** Given the 10-50 tool range, which analytical capabilities are most valuable for investor/analyst audiences? I need this to prioritize which tools to implement first for the eval suite. Common analyst questions suggest: market share, cross-shopping, customer demographics, and transaction volume trends.

2. **Eval query examples:** You have a question about this. From AI perspective, I need 20-30 representative queries across complexity levels for the eval suite. Please provide these with the natural language phrasing analysts actually use.

3. **Clarification language:** When the system asks for clarification, what phrasing do analysts expect? For example, "Which time period?" vs. "Did you mean last quarter or the past 3 months?" Domain-appropriate phrasing improves user trust.

### For ConsumerSpending (Consumer Behavior):

1. **Synthetic data correlations:** What real-world correlations are most recognizable? For example: (a) holiday season retail spike, (b) back-to-school category shifts, (c) generational preference for online channel, (d) income-brand correlation. These need to be embedded for the dataset to be analytically credible.

2. **Dimension cardinality:** What is realistic cardinality for each dimension in the synthetic dataset? Specifically: how many distinct brands (100+ mentioned in HLRD), merchant categories (10? 20?), geographic granularities (states only, or metro areas too?). This affects both data generation and tool design.

3. **Query pattern expectations:** What follow-up queries do analysts typically make after initial results? For example, after seeing market share, do they typically ask "why is that?" (attribution) or "how has that changed?" (trend). This informs multi-turn conversation design.

---

## Assumptions and Risks

### Assumptions

1. OpenRouter provides reliable structured output (JSON mode, function calling) across all target providers. This may vary by provider and model version.

2. The 10-50 tool range is manageable with the RAG + LLM selection approach. If tools are highly heterogeneous, retrieval may degrade.

3. Analysts are comfortable with HITL clarification. If users find frequent clarification annoying, adoption may suffer.

4. The synthetic dataset can be generated with sufficient statistical fidelity to produce plausible analytical results. If correlations are too obvious or missing, the demo loses credibility.

### Risks

1. **LLM hallucination in dimension extraction:** Models may extract dimensions that don't exist in the query or hallucinate brand names. Mitigation: validate extracted dimensions against API dimension enumerations.

2. **Tool selection failure modes:** When RAG retrieval misses the correct tool, the LLM cannot recover. Regular evaluation and tool definition updates are necessary.

3. **Latency stacking:** If multiple dimension extraction nodes all call the LLM, latency compounds. Mitigate by: (a) limiting parallel nodes, (b) using faster models for extraction, (c) caching repeated dimensions.

4. **Eval suite construction bias:** If test cases are written by the development team, they may not reflect real analyst query patterns. Consider involving actual analysts or market research SMEs in eval case authorship.

---

## Summary of Recommendations

| Area | Recommendation |
|------|----------------|
| Context Management | Sliding window + semantic summary for sessions >5 turns |
| Tool Retrieval | text-embedding-3-small, threshold 0.75, top-8 candidates |
| Tool Definitions | Include example queries, capabilities, aliases; exclude value enumerations |
| Multi-Tool Queries | Dedicated planner node upstream of tool selection |
| Dimension Extraction | Parallel specialized nodes; time/geo deterministic, brand/category LLM |
| Conflict Handling | Structured disambiguation via HITL, never silently resolve |
| Eval Suite | 200+ cases, 30/35/15/10/10 distribution across complexity levels |
| Clarification Eval | 0-2 rubric with human rating; mean ≥1.5 target |
| Model Selection | MiniMax-Text-01 (tool selection), Kimi (extraction), GLM-4-Air (planner) |
| Provider Normalization | Adapter layer for structured output abstraction |
| Streaming | Response generation only, via SSE |
| Latency Target | <4s non-streaming; 5s with variance buffer |