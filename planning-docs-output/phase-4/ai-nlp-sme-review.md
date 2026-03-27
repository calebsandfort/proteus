# AI/NLP SME Review: Requirements Draft

**Review Date:** 2026-03-27
**SME Domain:** AI/NLP Architecture, Prompt Engineering, Agent Workflows, LLM Inference
**Document Reviewed:** `/home/caleb/source/repos/proteus/planning-docs-output/phase-3/requirements-draft.md`

---

## Summary

Overall the AI/NLP requirements are well-structured and demonstrate solid understanding of modern LLM pipeline architecture. However, there are several gaps, conflicts, and accuracy issues that need to be addressed before finalization.

---

## Gaps Found

### G1: No Fallback Mechanism for LLM Failures

**Affected Sections:** FR-2, FR-3, FR-8

The requirements specify primary model selections but do not address:
- What happens when OpenRouter is unavailable or returns errors
- No circuit breaker pattern or fallback to cached results
- No degradation strategy when LLM APIs are rate-limited
- No retry exhaustion path — the spec mentions "retry once" (FR-8.5) but no maximum retry budget

**Recommended Change:** Add a new section under FR-8 or as a new NFR:

> **FR-8.6: LLM Failure Handling**
> - The pipeline SHALL implement exponential backoff with jitter for transient failures (max 3 retries)
> - After retry exhaustion, the system SHALL return a user-friendly error with request ID
> - Circuit breaker pattern SHALL be implemented to prevent cascade failures during provider outages
> - Critical paths (tool selection, dimension extraction) SHALL have fallback to conservative defaults

### G2: Missing Prompt Versioning and Audit Trail

**Affected Sections:** FR-2, FR-3, FR-8

No mention of:
- Prompt templates being versioned
- A/B testing capability for prompt variants
- Audit logging of which prompt version was used for each query
- Observability for prompt performance drift over time

**Recommended Change:** Add observability requirement:

> **FR-8.7: Prompt Management**
> - Prompt templates SHALL be versioned and stored in configuration
> - Each API request SHALL log the prompt version used for reproducibility
> - The observability panel SHALL display the rendered prompt for debugging

### G3: No Model Output Validation Schema

**Affected Sections:** FR-2.4, FR-3

The spec mentions structured output but does not define:
- JSON Schema for tool selection output
- JSON Schema for dimension extraction output
- How parse failures are handled beyond "retry once"
- No validation that extracted dimensions conform to API's expected format

**Recommended Change:** Add explicit schema requirements:

> **FR-3.7: Extraction Output Schema**
> - Dimension extraction output SHALL conform to a defined JSON Schema
> - The system SHALL validate LLM outputs against the schema before proceeding
> - Invalid outputs SHALL trigger retry with explicit system prompt correction

### G4: Missing Context Management Strategy for Long Conversations

**Affected Sections:** FR-1.2

The spec says "6-8 conversation turns as primary context window" but:
- Does not specify what happens when a conversation exceeds this
- No message summarization or compression strategy
- No explicit truncation policy (e.g., keep first + last N messages)
- "Session anchor" concept is mentioned but no implementation detail

**Recommended Change:** Clarify context management:

> **FR-1.2.1: Context Window Management**
> - The system SHALL maintain the most recent 6-8 turns plus the session anchor
> - When context approaches 80% of model token limit, older messages SHALL be summarized or compressed
> - Summarization SHALL preserve key extracted dimensions and tool selections for reference

### G5: No Explicit Handling of LLM Non-Determinism

**Affected Sections:** FR-2, FR-3, FR-7

Critical gaps:
- No temperature/settings specification for each model role
- No mention of seed parameters for reproducibility in evals
- Eval framework (FR-7) has no mention of running multiple trials for statistical significance
- No strategy for handling hallucinated dimension values that "look valid"

---

## Conflicts Identified

### C1: Embedding Model Conflict

**FR-2.3 vs FR-8.1/FR-8.2:**

- FR-2.3 specifies: "text-embedding-3-small or ember embedding model via OpenRouter"
- FR-8.2 specifies internal pipeline models: MiniMax-Text-01, Kimi-Open-Assistant, GLM-4-Air
- FR-8.1 lists supported providers: OpenAI, Google, Anthropic, Kimi, MiniMax, GLM

**Issue:** "ember" is not a standard OpenRouter model. OpenRouter's embedding support varies. The requirements should specify a concrete embedding model that is available on OpenRouter (e.g., "text-embedding-3-small" from OpenAI provider, or a native OpenRouter embedding model).

**Recommended Fix:** Clarify embedding model with provider prefix:
> "The system SHALL use OpenAI's text-embedding-3-small via OpenRouter"

### C2: Dimension Extraction Parallelism vs. Sequential Dependencies

**FR-3.2 says:**
- "The system SHALL execute dimension extraction nodes in parallel"

**FR-3.4 example shows:**
- "young people" → Gen Z (confidence 0.7) with Millennial as alternative

**Conflict:** If dimension extraction is purely parallel, how are cross-dimensional dependencies resolved? For example, if "young professional in NYC" is parsed, the generation and geography extraction might need to coordinate. Pure parallelism may not handle contextual dependencies.

**Recommended Fix:** Clarify the architecture:
> - Dimension extraction nodes SHALL execute in parallel for independent dimensions
> - Dependent extractions (e.g., brand resolution that affects category inference) SHALL execute sequentially with the dependency graph defined by the planner

### C3: Planner Node Timing Ambiguity

**FR-2.6 says:**
- "Planner node upstream of tool selection"
- "Planner SHALL use GLM-4-Air via OpenRouter"

**FR-2.4 says:**
- Tool selection confidence is "25% RAG similarity + 35% LLM selection + 40% dimension match"

**FR-3.1 specifies:**
- "Parallel, category-specialized extraction nodes"

**Conflict:** If the planner is upstream of tool selection, and tool selection requires dimension matching (40% of confidence), there is a chicken-and-egg problem. The dimension extraction happens before or after tool selection? The spec doesn't clearly define the data flow order.

**Recommended Fix:** Add explicit pipeline flow diagram or section:

> **Pipeline Order (Single-Tool Query):**
> 1. RAG retrieval (tool candidates)
> 2. Planner determines if single or multi-tool (optional for single-tool)
> 3. Tool selection LLM (with current context)
> 4. Parallel dimension extraction
> 5. Confidence scoring with dimension match component
> 6. Proceed or HITL clarification

### C4: RAG Similarity Threshold Inconsistency

**FR-2.3 says:**
- RAG threshold: 0.75 (below this triggers HITL)
- Candidates below 0.70 similarity trigger HITL clarification

**But FR-2.4 says:**
- Confidence < 0.70 triggers HITL

**Conflict:** These thresholds are redundant and potentially contradictory. The 0.70 "candidates below 0.70" threshold and the 0.70 "confidence below threshold" are likely measuring different things (raw similarity vs. composite confidence), but this is not clearly explained. If a candidate has 0.72 similarity but overall confidence is 0.68, what happens?

**Recommended Fix:** Clarify the two thresholds:
> - RAG retrieval: Retrieve top-8 candidates; if top candidate < 0.70 similarity, trigger HITL before tool selection
> - Final confidence: ≥0.85 proceed, 0.70-0.84 show candidates in observability, <0.70 HITL

---

## Accuracy Assessment

### Generally Accurate

**FR-2 (Tool Selection):** The RAG + LLM selection hybrid approach is sound. The weighted confidence scoring (RAG + LLM + dimension match) is a reasonable architecture. The 90% tool selection accuracy target is achievable with this architecture.

**FR-3 (Dimension Extraction):** The parallel extraction architecture with specialized nodes is correct. Time range parser as deterministic logic (10-50ms target) is reasonable. LLM + lookup table hybrid for synonyms is a proven pattern.

**FR-7 (Eval Framework):** The 5-level complexity distribution is well thought out. The human-rated clarification appropriateness rubric (0-2 scale) is appropriate. The 200 test case minimum provides statistical significance.

**FR-8 (Model Configuration):** OpenRouter as unified gateway is correct. Model-agnostic pipeline at integration layer is good architecture. Provider normalization via adapter layer is standard practice.

### Needs Clarification

**FR-1.2:** "6-8 conversation turns as primary context window" — This conflates message count with token count. Different LLMs have different context windows (4K, 16K, 128K, 200K). The requirement should be token-based, not turn-based.

**FR-2.3:** "Tools SHALL NOT include dimension value enumerations" — This is a good insight (avoid diluting retrieval signal), but what about aliases? The spec later mentions brand aliases. This needs nuance.

**FR-3.3:** Time range parsing rules — The deterministic rules are good, but the "query intent inference" for granularity preference ("trend" → finer) is underspecified. How is this inferred?

---

## Recommended Changes

### RC-1: Make Context Window Token-Based (FR-1.2)

**Current:**
> "The system SHALL maintain 6-8 conversation turns as the primary context window"

**Change To:**
> "The system SHALL maintain the most recent messages whose total token count does not exceed 75% of the current model's context window limit, with a minimum of the 4 most recent turns plus session anchor"

### RC-2: Explicitly Define RAG Retrieval Threshold (FR-2.3)

**Current:**
> "RAG similarity threshold SHALL be set at 0.75. Candidates below 0.70 similarity SHALL trigger HITL clarification"

**Change To:**
> "The RAG retrieval similarity threshold SHALL be 0.70. If the top candidate's similarity is below 0.70, the system SHALL route to HITL clarification with available candidates displayed. The 0.75 threshold appears to be a target for high-quality retrieval, not a hard cutoff."

### RC-3: Add Token Budget for Extraction Prompts (FR-3)

**Current:**
> (No mention of token limits)

**Change To:**
> "Each dimension extraction prompt SHALL include only the relevant conversation turns and SHALL not exceed 2,000 tokens to maintain low latency. Prompts SHALL be structured with: instruction, schema definition, examples, and current query."

### RC-4: Define Dimension Extraction Latency Target (FR-3)

**Current:**
> "Time Range Parser: target latency 10-50ms"

**Change To (expand to all extractors):**
> - Time Range Parser: 10-50ms (deterministic)
> - Geography Normalizer: 50-150ms (with cached lookups)
> - Brand Matcher: 400-800ms (LLM call)
> - Category Lookup: 400-800ms (LLM call)
> - Generation/Income Parsing: 400-800ms (LLM call)
> - **Total parallel extraction budget: 600-1200ms**

### RC-5: Add Response Generation Model Constraints (FR-8.3)

**Current:**
> "Response generation stage SHALL be user-configurable"

**Change To:**
> "Response generation model SHALL support function calling / tool use for consistency with pipeline. If a selected model does not support function calling, the system SHALL fall back to text-embedding-3-small for embedding + the最强的 available model for generation, with a user warning."

### RC-6: Clarify Eval Pass Criteria (FR-7.2)

**Current:**
> "End-to-end result correctness: Pass/fail on structured assertions — target ≥80%"

**Change To:**
> "End-to-end result correctness: Each test case SHALL be run across 3 trials with temperature=0. A test case passes if 2 of 3 trials return structurally correct results. Target ≥80% of test cases passing."

---

## Minor Issues

1. **FR-2.1:** "12-15 core data retrieval tools" — The spec lists 8 P0 tools, not 12-15. Need to clarify if the remaining tools are future Phase 2 items.

2. **FR-2.4:** "MiniMax-Text-01 for tool selection" — This model should be verified as available on OpenRouter with function calling support. If not, an alternative should be specified.

3. **FR-8.5:** "Parse failures SHALL trigger retry once" — What if the retry also fails? Need an exhaustion path.

4. **NFR-1.3:** Pipeline latency budget shows "Total (non-streaming): 2,050-4,100ms" but success criteria says "under 5 seconds." These are inconsistent — 4,100ms is 4.1 seconds, within 5s, but the budget leaves no headroom.

---

## Questions for Other SMEs

**For Behavioral Psychology SME:**
- FR-3.4 examples ("young people" → Gen Z with 0.7 confidence, Millennial as alternative) — Is this mapping psychologically accurate? How should we handle generational self-identification ambiguity?

**For Data Analytics SME:**
- The eval framework (FR-7) tests "End-to-end result correctness" with structured assertions. What assertions would be appropriate for the synthetic data? Should we test against pre-computed aggregate values?

---

## Conclusion

The requirements are 85% complete and accurate for the AI/NLP domain. The primary gaps are:
1. Missing failure handling and fallback strategies
2. Ambiguous context management policy
3. Inconsistent/conflicting thresholds
4. Missing prompt management and observability

The conflicts identified are addressable with clearer definitions. The recommended changes above would bring the requirements to a deployable specification level.
