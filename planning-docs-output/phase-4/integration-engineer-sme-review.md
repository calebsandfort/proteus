# Integration Engineer SME Review: Requirements Draft

**Document:** `/home/caleb/source/repos/proteus/planning-docs-output/phase-3/requirements-draft.md`
**SME Domain:** Multi-tenancy, data source connectors, database architecture, API design, authentication, data pipelines
**Review Date:** 2026-03-27

---

## Gaps Found

### 1. Tool Name Mismatch Between FR-2 and FR-4

**Location:** FR-2.2 vs FR-4.1
- FR-2.2 lists tool as `market_share_trend`
- FR-4.1 API contract example uses `market_share_comparison`

**Impact:** API contract example will not route correctly. Either the tool registry or the API contract example is wrong.

**Recommended Change:** Standardize on `market_share_trend` as the canonical tool name (per FR-2.2) and update FR-4.1 example to use a tool from the defined list.

---

### 2. Aggregation Level Gap in FR-4.4

**Location:** FR-4.4
- Auto-selection rules state:
  - 1-7 days → daily
  - 8-90 days → daily (duplicate of above)
  - 91-365 days → weekly
  - 1+ years → monthly

**Impact:** The 1-7 days and 8-90 days both map to daily with no differentiation. This is a specification gap, not a bug — it suggests the rules should probably be:
- 1-7 days → daily
- 8-90 days → weekly (distinct from the FR-3.3 rules which may differ)

**Recommended Change:** Clarify that 1-7 days → daily, 8-90 days → weekly. Ensure alignment with FR-3.3 time range parsing or explicitly state that FR-4.4 overrides FR-3.3 for API-level auto-selection.

---

### 3. Missing Cache Invalidation Strategy for Dimension Enumeration

**Location:** FR-4.6
- Endpoints are "cached in-memory" but no cache invalidation strategy is defined
- No TTL specified
- No mechanism for cache refresh documented

**Impact:** Stale dimension enumerations could cause validation failures if new brands/categories are added to the synthetic dataset.

**Recommended Change:** Add specification for cache TTL (e.g., "24-hour TTL with manual invalidation endpoint for admin use") or specify that dimension enumerations are static for Phase 1 (no dynamic updates expected).

---

### 4. Missing Dimension Enumeration Population Mechanism

**Location:** FR-4.6
- States endpoints "SHALL NOT query TimescaleDB directly"
- Does not specify how in-memory cache is populated

**Impact:** Implementation team has no guidance on initial data load or cache bootstrapping.

**Recommended Change:** Add: "Dimension enumeration values SHALL be loaded from static configuration files at API startup" or specify a seed data mechanism.

---

### 5. Result Synthesizer Not Specified

**Location:** FR-2.6 / FR-4.2
- FR-2.6 mentions multi-tool queries execute in parallel with results "synthesized by a result synthesizer"
- FR-4.2 batch endpoint mentions returning "latency per constituent query"
- No component, interface, or behavior defined for the result synthesizer

**Impact:** Unclear where result synthesis happens (FastAPI pipeline vs. ASP.NET Core batch endpoint) and what synthesis logic looks like (merging, union, comparison?).

**Recommended Change:** Define result synthesizer behavior — e.g., "Results SHALL be returned as a JSON object with each tool's response keyed by tool name, plus a synthesized_summary field for multi-tool queries."

---

### 6. Metric Enumeration Missing from API Contract

**Location:** FR-4.1
- Contract shows `"metric": "sum"` but no enumeration of valid metric values
- What are valid values? `sum`, `avg`, `count`, `min`, `max`, `median`?

**Recommended Change:** Add metric enumeration to FR-4.1 or reference a separate enumeration section. Example: `"metric": "sum" // enum: sum, avg, count, min, max`

---

### 7. High-Cardinality Dimension Filter Definition Incomplete

**Location:** FR-4.3
- "SHALL require at least one high-cardinality dimension filter (brand, category, or geography)"
- No definition of what constitutes "sufficient" filtering
- Is `brand=1` sufficient? Does it need `brand IN (5 brands)`? Is geography at state level granular enough?

**Recommended Change:** Define minimum filter requirements explicitly. Example: "A query is considered sufficiently filtered if it includes at least one of: (a) 1-50 specific brands, (b) 1-10 categories, (c) 1-20 state/CBSA values, or combinations thereof totaling >1 but <100 total dimension values."

---

### 8. Request ID Tracking Mechanism Not Specified

**Location:** FR-4.7
- Errors "SHALL include a `request_id` for debugging"
- No mechanism defined for how request_id is generated, propagated, and stored
- In distributed system (FastAPI → ASP.NET Core), request_id must flow through HTTP headers

**Recommended Change:** Add: "The API SHALL generate a UUID request_id on incoming requests and include it in all log entries and error responses. The FastAPI pipeline SHALL pass request_id via `X-Request-ID` header to the Data API."

---

## Conflicts Identified

### 1. API Latency SLA Conflict: NFR-1.2 vs NFR-1.3

**Location:** NFR-1.2 vs NFR-1.3
- NFR-1.2: "The ASP.NET Core API SHALL respond to parameterized queries in under 500ms (database query time, excluding AI pipeline)"
- NFR-1.3: "API call: 200-500ms" within total pipeline budget of 2,050-4,100ms

**Conflict:** If "database query time" per NFR-1.2 is 200-500ms per NFR-1.3, then the 500ms SLA seems achievable. However, the phrasing "excluding AI pipeline" in NFR-1.2 is ambiguous — it could mean the 500ms includes the full API processing (routing, validation, DB query, serialization) or just the DB query portion. This creates implementation ambiguity.

**Recommended Change:** Clarify NFR-1.2: "The ASP.NET Core API SHALL respond to parameterized queries in under 500ms total response time, measured from request receipt to response serialization, excluding network transit."

---

### 2. TimescaleDB Compression vs Retention Conflict

**Location:** FR-6.2
- Compression enabled after 30 days with gzip
- Retention policy drops chunks older than 7 years

**Conflict:** If chunks are compressed after 30 days but retained for 7 years, the system must maintain compressed chunks for 6+ years. This is operationally fine but the spec doesn't address what happens at the 7-year boundary — does compression help reduce storage before retention, or is retention the only mechanism?

**Recommended Change:** Add clarification: "Compression reduces storage for chunks between 30 days and 7 years. At the 7-year boundary, chunks are dropped per retention policy."

---

### 3. Aggregation Logic Duplication and Potential Conflict

**Location:** FR-3.3 vs FR-4.4
- FR-3.3: Time range size defaults:
  - ≤14 days → daily
  - 15-90 days → weekly
  - 91-365 days → monthly
  - >365 days → quarterly
- FR-4.4: Auto-selection:
  - 1-7 days → daily
  - 8-90 days → daily (should be weekly per above)
  - 91-365 days → weekly
  - 1+ years → monthly

**Conflict:** These rules are inconsistent. FR-3.3 says 15-90 days → weekly, but FR-4.4 says 8-90 days → daily. FR-4.4's range also starts at 1-7 days (not 0 or inclusive of 1).

**Recommended Change:** Consolidate into a single authoritative rule. FR-4.4 should be the API-level auto-selection rule. Align FR-3.3 dimension extraction defaults to match, or explicitly state that FR-3.3 applies to dimension extraction UI hints and FR-4.4 applies to API query execution.

---

## Accuracy Assessment

### FR-4 (Data Retrieval API)

**Overall Accuracy:** Good with gaps noted above

- API contract structure (FR-4.1) is well-designed with clear request/response shapes
- Batch endpoint concept (FR-4.2) is appropriate for multi-tool execution
- Query guardrails (FR-4.3) are a strong security measure
- Repository pattern abstraction (FR-4.5) is correct for future migration path
- Error response structure (FR-4.7) is comprehensive
- Response metadata (FR-4.8) is appropriate

**Concerns:**
- Tool name mismatch with FR-2.2 (gap #1)
- Missing aggregation metric enumeration (gap #6)
- Incomplete high-cardinality filter definition (gap #7)
- Missing request_id propagation mechanism (gap #8)

---

### FR-6 (Synthetic Data Layer / TimescaleDB)

**Overall Accuracy:** Accurate for TimescaleDB configuration

- Hypertable partitioning on `transaction_timestamp` with daily chunks is correct (FR-6.2)
- Compression after 30 days with gzip is standard practice (FR-6.2)
- Retention policy at 7 years is appropriate for longitudinal analysis (FR-6.2)
- Continuous aggregates (FR-6.8) cover the right rollup dimensions
- Hierarchical geography support is well-scoped (FR-6.3)
- Panel data structure (FR-6.9) is appropriate for consumer spending analysis

**Concerns:**
- Compression vs retention interaction needs clarification (conflict #2)
- FR-6.8 continuous aggregates specify retention but not refresh policies (continuous aggregates require periodic refresh)

---

### NFR-1 (Performance)

**Overall Accuracy:** Mostly accurate with the latency SLA conflict noted

- End-to-end latency target of 5 seconds (NFR-1.1) is realistic
- Streaming requirement (NFR-1.4) with 500ms first-token target is appropriate
- Query performance at scale requirements (NFR-1.5) correctly prohibits raw row queries at 10M scale

**Concerns:**
- Latency SLA ambiguity between NFR-1.2 and NFR-1.3 (conflict #1)
- Chunk exclusion requirement stated but implementation not guided

---

### NFR-2 (Architecture)

**Overall Accuracy:** Accurate

- Four-container architecture is well-defined (NFR-2.1)
- Network topology is clear (NFR-2.2)
- Technology stack alignment with HLRD is correct (NFR-2.3)
- CopilotKit integration points are specified (NFR-2.4)

**Concerns:**
- Multi-tenancy readiness (NFR-2.5) leaves Phase 1 behavior undefined — if tenant_id is nullable and RLS is not implemented, what prevents cross-tenant queries during single-tenant Phase 1 operation?
- Missing `tenant_id` filter in API contract examples

---

## Recommended Changes

### High Priority (Must Fix Before Phase 2)

1. **Fix tool name mismatch** between FR-2.2 and FR-4.1
2. **Clarify latency SLA** in NFR-1.2 to remove ambiguity
3. **Consolidate aggregation rules** between FR-3.3 and FR-4.4
4. **Add `request_id` propagation specification** to FR-4.7 or add new FR-4.X section
5. **Define high-cardinality filter threshold** in FR-4.3

### Medium Priority (Should Address)

6. **Add metric enumeration** to FR-4.1 API contract
7. **Specify dimension enumeration cache invalidation strategy** in FR-4.6
8. **Clarify dimension enumeration population mechanism** in FR-4.6
9. **Define result synthesizer behavior** in FR-2.6 or FR-4.2
10. **Clarify compression vs retention interaction** in FR-6.2

### Low Priority (Nice to Have)

11. **Specify continuous aggregate refresh policies** in FR-6.8
12. **Define Phase 1 single-tenant behavior** in NFR-2.5 (e.g., all queries implicitly scoped to tenant_id = 1, even without RLS enforcement)

---

## Questions for Other SMEs

**For AI/NLP Architecture SME:**
- FR-2.6 mentions a "planner node" for multi-tool queries using GLM-4-Air. Where does result synthesis happen — in the planner node or a separate synthesis stage? What is the output contract when multiple tools return results?

**For Product Manager:**
- The dimension enumeration endpoints (FR-4.6) are cached in-memory. Are dimension values truly static for Phase 1, or should we expect dynamic additions to brands/categories that would require cache invalidation?
