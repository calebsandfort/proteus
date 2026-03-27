# UX Designer SME Review

**Review Date:** 2026-03-27
**Document Reviewed:** `/planning-docs-output/phase-3/requirements-draft.md`
**Design System Reference:** `AGENTS.md` (ShadCN/ui + Tailwind CSS + ECharts + CopilotKit)

---

## Gaps Found

### G-1: Missing Mobile/Responsive Considerations

**Location:** FR-1.1 (Layout and Structure)

The requirement specifies a 380-420px CopilotKit ChatSidebar, but there is no mention of responsive behavior for tablet or mobile viewports. Professional dashboard tools are desktop-first, but analysts may occasionally use tablets.

**Recommendation:** Add requirement for minimum viewport width of 1024px before showing the fixed sidebar layout. Below 1024px, the sidebar should collapse into a slide-out drawer triggered by a floating action button. This ensures the core desktop experience is prioritized while tablet use is gracefully degraded.

---

### G-2: Empty State Design Absent

**Location:** General UX

No requirements specify what first-time users see when they open the dashboard. An empty state is critical for setting expectations and guiding users toward their first query.

**Recommendation:** Add FR-1.8 (Empty State):
- The system SHALL display a centered empty state message on initial load with a sample analytical question prompt (e.g., "Try: What was Walmart's market share in grocery last quarter?")
- The empty state SHALL show a subtle animated visualization placeholder to indicate where charts will appear
- The empty state SHALL NOT block the input field from being immediately usable

---

### G-3: Missing Session Timeout UX

**Location:** FR-1 (General)

When a session expires or needs re-authentication, there is no specification for how this is communicated or handled within the chat interface.

**Recommendation:** Add to FR-1.7 or create FR-1.9 (Session Management):
- Session timeout SHALL display an inline banner above the chat input (NOT a modal)
- The banner SHALL allow re-authentication without losing the current conversation context
- Conversation context SHALL be preserved for 30 minutes after timeout to allow resumption

---

### G-4: Missing Chart Interaction Behaviors

**Location:** FR-5.5, FR-5.6

FR-5.5 (Required) specifies hover tooltips, legend toggling, and responsive resize. FR-5.6 (Recommended) adds data zoom and click-to-highlight. However, several critical interaction behaviors are missing:

**Missing specifications:**
- Click behavior on chart elements (drill-down? tooltip? no action?)
- Zoom reset button (when data zoom is active)
- Chart export capability (PNG, CSV)
- Axis label truncation behavior for long labels
- Empty data state for charts

**Recommendation:** Add FR-5.9 (Chart Interaction Details):
- Clicking a bar/segment SHALL show a detailed tooltip with the value AND offer a drill-down option via "Click to explore" prompt
- Data zoom SHALL display a reset button when zoom is active
- Chart header SHALL include an export dropdown (PNG, CSV) using native ECharts export methods
- Charts returning empty data SHALL display a centered empty state with "No data matches your query" message

---

### G-5: Multi-Tool Partial Results UX Missing

**Location:** FR-1.6, FR-2.6

When a multi-tool query is executing, partial results from completed tools should be displayed. There is no specification for how this streaming/partial display works in the chat interface.

**Recommendation:** Add to FR-1.6 or FR-2.6:
- For multi-tool queries, the system SHALL display a "Waiting for results..." indicator per pending tool while others complete
- Completed tool results SHALL render inline as they become available, with a subtle animation to draw attention
- A summary message SHALL appear only after all tools complete, synthesizing the results

---

### G-6: Observability Panel JSON Viewer Underspecified

**Location:** FR-1.3, FR-1.4

The requirement mentions an "inline JSON viewer with syntax highlighting" but provides no specifications for:
- Font (should use `font-mono` per AGENTS.md: JetBrains Mono)
- Font size (AGENTS.md specifies `text-xs` for code/technical)
- Color scheme for syntax highlighting
- Collapsible tree view vs. raw JSON
- Maximum height and scroll behavior

**Recommendation:** Revise FR-1.4 to specify:
- JSON viewer SHALL use `font-mono text-xs` styling (per design system)
- JSON SHALL be formatted with collapsible tree nodes for objects/arrays beyond 3 levels
- Maximum initial display of 20 lines with "Show more" expansion
- Syntax highlighting SHALL use the design system's code colors (slate palette for keys, blue for strings, amber for numbers)

---

### G-7: Conversation History Thumbnails Underspecified

**Location:** FR-5.8

"Thumbnail previews" is mentioned but no specifications exist for:
- Thumbnail dimensions (px or aspect ratio)
- Content: actual mini chart? generic chart icon? KPI summary?
- Hover behavior: enlarge? show full query text?
- Click behavior: scroll to that point in conversation? reload that result?

**Recommendation:** Revise FR-5.8 to specify:
- Thumbnails SHALL be 64x48px with 4:3 aspect ratio
- Thumbnails SHALL show a scaled-down rendering of the actual chart (SVG or canvas snapshot)
- Hover SHALL show a tooltip with the full query text and timestamp
- Click SHALL smooth-scroll to that message and re-render the visualization in the canvas

---

### G-8: Error State UX Absent

**Location:** FR-1.7 (Error Handling), FR-4.7

FR-4.7 specifies error codes (MISSING_REQUIRED_DIMENSION, INSUFFICIENT_FILTERS, etc.) but there is no UX specification for how these errors appear to users. FR-1.7 covers ambiguous query handling but not API errors.

**Missing specifications:**
- Visual treatment of errors in chat (red border? error icon? badge?)
- Retry affordance
- "View corrected query" option when dimensions need adjustment
- Distinction between recoverable errors (retry) vs. fatal errors (must modify query)

**Recommendation:** Add FR-1.10 (API Error Handling in Chat):
- API errors SHALL appear as inline error messages within the chat stream with `text-red-600` coloring and an error icon
- Each error SHALL include a "Try adjusting: [specific dimension]" suggestion when applicable
- Rate limit errors (429) SHALL show countdown timer until retry is available
- All error messages SHALL use user-friendly language, not raw error codes

---

## Conflicts Identified

### C-1: Observability Panel Level Nomenclature Conflict

**Location:** FR-1.4 vs. FR-1.3

FR-1.3 states: "When toggled ON, chat messages SHALL gain subtle expand icons in the corner"

FR-1.4 describes a 3-Level system where:
- Level 1 = Toggle ON (shows tool selection, dimensions, latency)
- Level 2 = Expanded Message (JSON viewer with RAG candidates)
- Level 3 = Raw Response ("Show raw" action)

**Conflict:** The specification calls this "3-Level" progressive disclosure, but there are actually 4 distinct UI states (default, toggled-on header active, expanded message, raw response). The "toggle" and "expand icons" are separate controls that should not be conflated into the same "level."

**Resolution Needed:** Clarify that Level 0 = default (hidden), Level 1 = toggle ON (shows per-message expand icons), Level 2 = expanded message (JSON viewer), Level 3 = raw response. Alternatively, separate the toggle from the "levels" concept entirely.

---

### C-2: Model Selector Header Integration Conflict

**Location:** FR-1.5 vs. CopilotKit Header

FR-1.5 requires the model selector to be "in the header bar." The CopilotKit ChatSidebar has a built-in header area. However, the observability panel toggle also claims the "chat interface header area" (FR-1.3).

**Conflict:** Both the model selector and observability toggle need header space. With CopilotKit's limited header real estate, these two controls may compete for the same location.

**Resolution:** Specify explicit placement:
- Observability toggle: Far left of header (or as part of CopilotKit's built-in controls if available)
- Model selector: Right side of header, after observability toggle
- If space is insufficient, model selector SHOULD appear in a settings dropdown accessible via gear icon

---

### C-3: KPI Card Toggle vs. Chart/Table Toggle Overlap

**Location:** FR-5.3 vs. FR-5.4

FR-5.3 specifies KPI cards have a "View as chart" toggle.
FR-5.4 specifies the system provides "Chart only, Table only, Both" toggle.

**Conflict:** These are two separate toggle mechanisms that could conflict. If a user is viewing a KPI card and switches to "Table only" mode, does the "View as chart" toggle still appear? The interaction between these two toggles is undefined.

**Resolution:** Specify that for KPI card views, the chart/table toggle defaults to "Chart" and shows "View as table" option. The "View as chart" toggle in FR-5.3 is redundant and should be replaced with "View as table" to maintain consistency with FR-5.4's terminology.

---

### C-4: Terminology Inconsistency — "brand" vs. "merchant"

**Location:** FR-3.1 vs. FR-2.2

FR-3.1 (Dimension Categories) lists: "brand/merchant"
FR-2.2 (Core Tool Set) references only "brand" (e.g., "Brand-vs-brand market share")

**Conflict:** The dimension extraction pipeline references "brand/merchant" as a single category, but the tool set and other requirements use "brand" exclusively. This could cause confusion in implementation.

**Resolution:** Standardize on "brand" throughout. If merchant-level analysis is intended to be distinct, clarify the difference between brand (e.g., Chipotle) and merchant (e.g., individual restaurant location) and ensure both concepts are consistently named.

---

## Accuracy Assessment

### A-1: Layout Specifications Are Appropriate

**FR-1.1, FR-1.2:** The CopilotKit ChatSidebar at 380-420px is appropriate for the desktop-first use case. The sidebar pinned to the right (rather than left) is correct for data analytics workflows where the primary visualization canvas should have visual priority. Conversation history persistence is correctly specified as a session-level concern.

**Assessment:** ACCURATE

---

### A-2: Loading States Appropriately Tiered

**FR-1.6:** The three-tier approach (no feedback <2s, stage indicator 2-5s, timeout warning >5s) aligns with Nielsen's response time guidelines and professional dashboard conventions. The skeleton loaders with shimmer animation requirement is correct.

**Minor Issue:** "Skeleton loaders" should specify that they show a chart-shaped placeholder (axis lines, some bar outlines) rather than generic loading text, to set proper expectations.

**Assessment:** MOSTLY ACCURATE with minor clarification needed

---

### A-3: HITL Clarification UX Correct

**FR-1.7, FR-2.5:** Inline clarification cards (not modals) is the correct pattern for conversational interfaces. Limiting to 3 options maximum is appropriate. Keeping the input active and original query visible are correct decisions.

**Assessment:** ACCURATE

---

### A-4: Observability Progressive Disclosure Pattern Correct

**FR-1.3, FR-1.4:** The concept of hidden-by-default observability with toggle, progressive disclosure via expand icons, and explicit raw view access is the correct pattern for professional tools. This matches the design pattern used in Stripe's dashboard and other sophisticated analytical tools.

**Assessment:** CONCEPTUALLY ACCURATE but requires clarification on control separation (see C-1)

---

### A-5: Chart Type Auto-Selection Logic Sound

**FR-5.1:** The mapping of query patterns to chart types is correct and comprehensive:
- Line for time trends
- Bar for comparisons
- Pie for proportions
- Horizontal bar for rankings
- Choropleth for geography

**Assessment:** ACCURATE

---

### A-6: Chart Manual Override Placement Vague

**FR-5.2:** "Top-right corner of the visualization canvas" is insufficiently specific. In a dashboard layout, "top-right" could mean:
- Overlapping the chart (floating)
- In a toolbar above the chart
- In the header area shared with other controls

**Assessment:** NEEDS CLARIFICATION

---

### A-7: ECharts Implementation Details Absent

**FR-5:** While the requirement specifies ECharts, it does not reference the AGENTS.md design system's chart styling guidelines (color sequence, grid styling, tooltip design, container specs). These should be incorporated by reference to avoid duplication and ensure consistency.

**Assessment:** NEEDS REFERENCE TO DESIGN SYSTEM SPECS

---

## Recommended Changes

### RC-1: Add FR-1.8 (Empty State)

Add new section after FR-1.7:

> **FR-1.8: Empty State**
> - The system SHALL display a centered placeholder visualization area on initial load
> - The placeholder SHALL include a sample query prompt in muted text
> - The input field SHALL be immediately accessible and usable
> - The empty state SHALL disappear upon submission of the first query

### RC-2: Clarify Observability Panel Controls

Revise FR-1.4 to separate the toggle from the expansion levels:

> **FR-1.4: Observability Controls**
> - **Default (OFF):** Clean chat + visualization. No instrumentation visible
> - **Toggle ON:** Header shows active state; chat messages gain expand icons
>   - Level 1 display: Selected tool(s), extracted dimensions, latency per stage
> - **Expanded Message:** Click expand icon → inline JSON viewer showing top-3 RAG candidates with similarity scores
>   - JSON viewer uses `font-mono text-xs` with collapsible tree nodes
> - **Raw Response:** Explicit "Show raw" action → full API request/response

### RC-3: Standardize "brand" Terminology

Revise FR-3.1 to use "brand" only (not "brand/merchant"):

> **FR-3.1: Dimension Categories**
> - **brand**: Brand names with fuzzy matching and alias resolution

If merchant-level granularity is required, add a separate dimension category.

### RC-4: Add FR-5.9 (Chart Interaction Details)

Add new section after FR-5.8:

> **FR-5.9: Chart Interaction Details**
> - Charts SHALL support data zoom (slider) for time-series with 8+ data points
> - Data zoom SHALL display a reset button when zoom is active
> - Charts SHALL support click-to-highlight for legend items or bars
> - Charts SHALL support PNG export via download button in chart header
> - Charts returning empty data SHALL display a centered empty state message

### RC-5: Remove Redundant KPI Toggle

Revise FR-5.3 to align terminology with FR-5.4:

> **FR-5.3: KPI Card Display**
> - For single aggregate values, the system SHALL render a KPI card
> - The KPI card SHALL display: metric name, primary value, comparison to prior period, comparison to category average
> - The KPI card SHALL include a "View as table" toggle to switch to tabular view

### RC-6: Add Model Selector Placement Specifics

Revise FR-1.5 to clarify header integration:

> **FR-1.5: Model Selector**
> - The system SHALL display a model selector dropdown in the header bar
> - The selector SHALL appear to the right of the observability toggle
> - If header space is insufficient, the selector SHALL appear in a settings popover
> - The dropdown SHALL display model names and provider logos
> - The selector SHALL show the current selection prominently
> - Changes SHALL apply to subsequent queries within the session

### RC-7: Add Chart Override Positioning Specifics

Revise FR-5.2:

> **FR-5.2: Manual Override**
> - The system SHALL provide a manual chart type override control
> - The override dropdown SHALL appear in a floating toolbar above the chart, aligned to the right
> - Available options SHALL include: Auto, Table, Line, Bar (Vertical), Bar (Horizontal), Pie, Donut, Scatter
> - When override differs from auto-selection, a tooltip SHALL explain the auto-selection reasoning

### RC-8: Add Responsive Behavior Spec

Add to FR-1.1:

> **FR-1.1: Layout and Structure**
> - At viewports below 1024px width, the chat sidebar SHALL collapse into a slide-out drawer
> - A floating action button in the bottom-right corner SHALL trigger the drawer
> - The main visualization canvas SHALL fill the full width when sidebar is collapsed

---

## Summary

The requirements draft demonstrates a solid understanding of conversational interface patterns and data visualization best practices. The core UX decisions (inline clarification, progressive disclosure, auto chart selection) are well-founded.

**Critical issues to resolve:**
1. C-1: Observability panel control hierarchy needs clarification
2. C-2: Model selector and observability toggle placement conflict
3. G-1: Mobile/responsive behavior missing
4. G-8: Error state UX completely absent

**Recommended priority:**
1. Resolve C-1 and C-2 (implementation will be affected)
2. Add G-8 (error UX is a critical gap)
3. Add responsive behavior spec
4. Incorporate remaining gap fills (empty state, chart interactions, thumbnails)

All recommended changes work within the established design system (ShadCN + Tailwind + ECharts + CopilotKit) and do not introduce new component libraries or patterns.
