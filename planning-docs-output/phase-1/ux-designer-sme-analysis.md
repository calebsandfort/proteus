# UX/UI Design SME Analysis: Proteus

## SME Analysis Overview

**SME Domain:** UX/UI Design, Dashboard Layouts, Approval Workflow UX, Information Architecture, Professional Tool Interfaces
**Target Users:** Analysts and investors who need to query consumer transaction data through natural language
**Usage Pattern:** "Check it 5 times a day" triage pattern — users scanning between other tasks, not staring at the interface all day

---

## Question 1: Observability Panel Default State

**Question:** What's the right default state for the observability panel? Should it be a persistent sidebar toggle, a per-message expandable section, or a separate debug view? How do we keep it useful for power users without cluttering the analyst experience?

### Direct Answer

The observability panel should default to **hidden** (off by default) with a **persistent toggle control** in the chat interface header area. This is the optimal balance for the stated user profile: analysts checking data between other tasks who need quick decisions, and power users who want deep inspection on demand.

### Recommended Implementation

**Layout Structure:**
```
+--------------------------------------------------+
|  [Logo] Proteus          [Observability Toggle]   |  <- Header with toggle
+------------------------+-------------------------+
|                        |                         |
|   Main Visualization   |    CopilotKit           |
|   Canvas (ECharts)     |    ChatSidebar           |
|                        |    (pinned right)        |
|                        |                         |
|                        |    [Message 1]           |
|                        |    [Message 2]           |
|                        |    [Message 3]           |
|                        |                         |
+------------------------+-------------------------+
```

**Observability Toggle Design:**
- Toggle button in the header bar, next to the model selector
- Icon: magnifying glass with "eye" symbol (standard for inspection modes)
- Label: "Inspect" or "Debug" (keep it short)
- Badge indicator when messages have inspectable data
- State persists across sessions via localStorage

**Per-Message Expandable Section (Secondary Pattern):**
Within the chat sidebar, each message with tool invocation data should have a subtle "..." or expand icon that reveals an inline detail view:

```
[Message bubble]
  └── "Used: merchant_analysis_by_generation"
      └── [Expand chevron]
          └── Tool selection reasoning (collapsed by default)
              └── Extracted parameters
              └── Raw API response (user must explicitly expand)
```

**Why This Approach Works:**

| Pattern | Pros | Cons |
|---------|------|------|
| Persistent sidebar | Always visible for power users | Clutters analyst experience; takes 20-30% of screen |
| Per-message expandable | Keeps messages clean; progressive disclosure | Requires clicking; can be tedious for rapid analysis |
| Separate debug view | Full separation; clean main UI | Context switching; can't see viz + debug simultaneously |
| Header toggle + inline expand | Best of both worlds; minimal footprint | Slightly more complex implementation |

**Progressive Disclosure Strategy:**

1. **Level 0 (Default):** Clean chat + visualization. No instrumentation visible.
2. **Level 1 (Toggle On):** Chat messages gain "..." expand icons; header shows active state.
3. **Level 2 (Expanded Message):** Inline JSON viewer with syntax highlighting for params + responses.
4. **Level 3 (Raw Response):** Separate scrollable panel at bottom of message for full API dumps.

**For Power Users:**
- Add a keyboard shortcut (`Cmd/Ctrl + Shift + D`) to toggle
- Show tooltip on hover in toggle: "Toggle inspection mode (Cmd+Shift+D)"
- Auto-expand last N messages when toggling on (so user sees recent context)

**Information Hierarchy:**
- Primary: The visualization and chat response (always dominant)
- Secondary: Which tool was selected (shown inline, collapsed)
- Tertiary: Full parameter extraction and reasoning (on expand)
- Deep: Raw API responses (deepest level, requires deliberate action)

---

## Question 2: Chart Type Selection and Manual Override

**Question:** What chart types map to which analytical query patterns? Should the system offer a manual override for chart type, or is automatic selection sufficient for Phase 1?

### Direct Answer

Automatic chart selection based on query and result shape is **sufficient for Phase 1**, but a **manual override control must be included** even if it requires additional implementation effort. Power users and analysts doing comparative analysis will need to override the default to match their mental model, not the system's.

### Recommended Chart Type Mapping

| Query Pattern Keywords | Result Shape | Recommended Chart | Rationale |
|------------------------|--------------|-------------------|-----------|
| "average", "mean", "total", "sum", "aggregate" | Single value or small set of categories | **KPI Card / Number** | Immediate answer; no chart needed |
| "over time", "trend", "history", "quarter", "monthly" | Time series (date axis) | **Line Chart** | Standard for temporal trends |
| "compare", "vs", "versus", "distribution" | 2-5 categories | **Bar Chart** (horizontal for many categories, vertical for few) | Easy comparison of magnitudes |
| "share", "percentage", "proportion", "breakdown" | Categories with values summing to 100% | **Pie Chart / Donut** | Shows part-to-whole relationships |
| "across", "by", "segmented" + multiple dimensions | 2+ categorical axes | **Stacked Bar** or **Heatmap** | Shows composition across dimensions |
| "correlation", "relationship", "scatter" | X/Y numeric pairs | **Scatter Plot** | Reveals relationships and outliers |
| "ranking", "top", "bottom", "leaderboard" | Sorted categories | **Horizontal Bar Chart** | Natural ranking visualization |
| "geography", "state", "region", "location" | Geographic dimension present | **Choropleth Map** | Spatial patterns (if ECharts supports geo) |
| "multi-tier", "funnel", "pipeline" | Sequential stages | **Funnel Chart** | Shows drop-off or progression |

### Fallback Logic (When Pattern Detection Fails)

1. **1 row, 1-2 columns:** KPI Card
2. **2-10 rows, 2 numeric columns:** Scatter
3. **2-10 rows, 1 categorical + 1 numeric:** Bar
4. **>10 rows, 1 categorical:** Horizontal Bar
5. **Time-based data:** Line
6. **Default:** Table (safe fallback when uncertain)

### Manual Override UI

**Placement:** Small icon button on the top-right of the visualization canvas, next to the chart actions (if any).

```
+------------------------------------------+
|  [Chart Title]              [Table] [▾]  |  <- Override dropdown
|------------------------------------------|
|                                          |
|           [Visualization]                |
|                                          |
+------------------------------------------+
```

**Override Options:**
- Auto (default)
- Table
- Line
- Bar (Vertical)
- Bar (Horizontal)
- Pie
- Donut
- Scatter

**Design Considerations:**
- Override persists per-query (doesn't change the system prompt)
- Show a subtle "Auto" badge when using system-selected type
- When override differs from auto, briefly show why (tooltip): "Auto selected line because query contains 'trend'"

---

## Additional UX Design Recommendations

### 3.1 Chat Interface Layout

**Recommended: Right-aligned CopilotKit ChatSidebar**

The HLRD specifies the chat sidebar pinned to the right. This is correct for several reasons:

1. **F-pattern reading:** Users scan left-to-right, top-to-bottom. Visualization stays in primary visual field (left = first thing seen).
2. **Chat as secondary:** For data queries, the answer matters more than the conversation. Visualization dominates.
3. **Tool availability:** CopilotKit's ChatSidebar is designed for right-side pinning, making this a standard pattern.

**Width Recommendation:** 380-420px for the chat sidebar. This accommodates:
- Full message content without wrapping
- Comfortable input area
- Expandable inspect sections without breaking layout

**Minimum Width:** 320px (below this, collapse to icon-only mode with tap-to-expand)

### 3.2 Main Canvas Area

The main canvas should handle multiple visualization states:

| State | Design |
|-------|--------|
| **Empty** | Welcome message or quick-start examples; centered prompt |
| **Loading** | Skeleton chart with shimmer animation; "Analyzing query..." status |
| **Single Result** | Full-width chart with generous padding |
| **Multiple Results** | Tabbed interface above chart; tabs = query summaries |
| **Error** | Inline error message with retry button; don't destroy the previous valid visualization |

### 3.3 Multi-Turn Conversation UX

**Context Window Indicator:**
Show a subtle indicator of how much conversation context is being used:

```
[Model: GPT-4o ▾]     [Context: 3 messages ▾]
```

This helps users understand why older queries might not be remembered.

**Reference Patterns:**
When a user says "compare that to Walmart", the word "that" should be hoverable, showing a tooltip: "↗ merchant_analysis: Target (from message #2)"

### 3.4 Model Selector UX

**Placement:** Header bar, right side, before observability toggle.

**Behavior:**
- Dropdown with model names and provider logos
- Shows current selection prominently
- Tooltip on hover: "Response generation model (affects answer quality and speed)"
- No per-stage model selection in Phase 1 (as specified in Out of Scope)

### 3.5 Loading and Feedback States

**Query Submission:**
1. User submits → Input shows "Sending..." disabled state
2. Tool selection → Subtle indicator: "Selecting analysis method..."
3. Parameter extraction → "Extracting dimensions..."
4. API call → "Fetching data..."
5. Visualization → Chart skeleton with shimmer

**Timing Expectations:**
- Under 2s: No additional feedback needed beyond disabled input
- 2-5s: Show stage indicator
- Over 5s: Show timeout warning with option to cancel

### 3.6 Error States

**Ambiguous Query (HITL):**
```
┌─────────────────────────────────────┐
│ I found multiple tools that might   │
│ answer your question:               │
│                                     │
│ ○ Merchant Trends by Generation     │
│ ● Brand Comparison by Category      │
│ ○ Category Growth Over Time         │
│                                     │
│ [ Select one to proceed ]           │
└─────────────────────────────────────┘
```

**Missing Parameters:**
```
┌─────────────────────────────────────┐
│ To run "Average Target spend..."    │
│ I need:                             │
│                                     │
│ □ Time range (e.g., "last quarter") │
│ □ Demographic (generation, income)  │
│                                     │
│ [ Ask follow-up or type one above ] │
└─────────────────────────────────────┘
```

### 3.7 Empty States

**First Visit:**
Centered welcome with 3-4 example queries as clickable chips:
- "What's spending at Amazon by generation?"
- "Show me Target vs Walmart trends over time"
- "Compare grocery categories by income bracket"

**No Results:**
"Query returned no data. Try broadening your time range or selecting a different category."

---

## Information Architecture

### Navigation Structure

For a single-purpose tool (natural language queries), avoid complex navigation:

```
[Logo] Proteus    [Model ▾] [Observability] [Settings ⚙]
```

**No sidebar navigation needed** — this is not a multi-section app. All primary functionality lives on one page with the chat + canvas split.

### Content Organization

| Content Type | Where It Lives | How It's Organized |
|--------------|----------------|-------------------|
| Chat messages | Right sidebar | Chronological, newest at bottom |
| Visualizations | Main canvas | Tabbed by query (newest active) |
| Conversation history | Persisted, accessible via menu | Grouped by date |
| Model settings | Modal or dropdown | Single settings panel |

---

## Risks and Mitigation

### Risk 1: Chart Selection Mistakes Frustrate Users
**Impact:** Users lose trust in auto-selection
**Mitigation:** Provide override AND show reasoning for auto-selection on hover

### Risk 2: Observability Panel Creates Alert Fatigue
**Impact:** Power user features become noise for regular users
**Mitigation:** Default off; per-message expand requires deliberate action; no persistent sidebar

### Risk 3: Chat History Grows Unmanageably Long
**Impact:** Users can't find past insights; context degrades
**Mitigation:** Provide conversation search; limit context window with clear indicator; offer "start new conversation" prominently

### Risk 4: Loading States Kill Perceived Performance
**Impact:** 5-second latency feels unacceptable without good feedback
**Mitigation:** Skeleton loaders; stage indicators; optimistic UI where possible

---

## Questions for Other SMEs

**For AI/NLP Architecture SME:**
- How does the observability panel surface tool selection reasoning? Should it show RAG retrieval scores, LLM confidence scores, or just the final selected tool? What's the performance cost of surfacing this data per message?
- For ambiguous queries triggering HITL clarification, what's the expected format from the LLM? Can it provide confidence scores for each candidate, or just a list?

**For Integration Engineer SME:**
- The chat sidebar width (380-420px) affects how much of the main canvas is visible. Is there a minimum viewport width we should design for? Should we collapse the chat on smaller screens, or is this out of scope for Phase 1?
- How does the API return error states that map to user-friendly messages? Should 500 errors, timeout errors, and validation errors all surface differently in the UI?

**For Data Scientist SME:**
- For queries that return single aggregate values (e.g., "average Target spend"), should we skip chart rendering entirely and show a large KPI card? Or always render a visualization even for trivial results?
- What's the expected cardinality of result sets? If a query returns 10,000 rows (e.g., all transactions), how should we handle pagination or aggregation? The current spec mentions "basic interactivity" — does this include scroll/pagination for large tables?

---

## Summary

| Decision | Recommendation |
|----------|----------------|
| Observability default | Hidden by default; header toggle; per-message expand |
| Chart selection | Auto-based on query pattern; manual override required |
| Layout | Right-side chat (380-420px); left visualization canvas |
| Loading feedback | Skeleton + stage indicators for >2s queries |
| Error handling | Inline errors; HITL for ambiguity; graceful degradation |
| Model selector | Header dropdown; single-stage for Phase 1 |
| Multi-turn UX | Context indicator; referential hover tooltips |

---

*Analysis prepared for Proteus HLRD elaboration — Phase 1 UX/UI Design SME*