# UX Designer SME Answers: Phase 2 Cross-SME Consultation

## From AI/NLP SME (ai-nlp-sme)

---

**Question 1: Observability Panel Default State**

> From an AI pipeline perspective, a collapsed sidebar toggle (not per-message expansion) is recommended. Per-message expansion would interrupt conversation flow and complicate streaming implementation. The toggle should show a slide-out panel that doesn't reflow the main canvas. What are your thoughts on this implementation approach?

**Answer: Agreement with Hybrid Approach**

The AI/NLP SME's recommendation aligns with my Phase 1 analysis. A collapsed sidebar toggle is the correct default. My additional recommendation:

**Hybrid Pattern (Best of Both Worlds):**
- **Global Toggle** (header): Controls whether any observability is visible at all
- **Per-Message Expand** (inline within chat): When toggle is ON, each message gets a subtle expand chevron

This avoids streaming complications because:
1. The toggle state is a binary on/off, not state per message
2. Per-message expansion happens after streaming completes (no DOM reflow during streaming)
3. The slide-out panel concept should be abandoned - it reflows the main canvas and breaks the "doesn't interrupt flow" requirement

**Recommended Implementation:**
```
[Header Bar]
├── [Logo] Proteus
├── [Model Selector ▾]
├── [Observability Toggle] ← Icon button with badge indicator
└── [Settings ⚙]

When toggled ON:
- Chat messages gain subtle "..." expand icons in corner
- Clicking expand shows inline JSON viewer (syntax highlighted)
- Main canvas is NEVER reflowed - observability is contained within the chat sidebar
```

The "slide-out panel that doesn't reflow" is contradictory - any panel that slides out either reflows content or overlays it. Overlay (absolutely positioned) is acceptable but adds z-index complexity. The inline expand within the chat sidebar is simpler and sufficient.

---

**Question 2: Chart Type Override**

> Should users be able to manually override the auto-selected chart type? From an AI perspective, this is low-cost to implement - just expose a dropdown after visualization renders. The AI/NLP SME recommends adding this for power users. Do you agree with this prioritization?

**Answer: Yes, but with Clear UX**

Strong agreement. Manual override is essential for:
1. **Comparative analysis** - analysts may want a bar chart where the system chose pie
2. **Presentation context** - report format may require specific chart type
3. **Trust building** - showing users they can override builds confidence in auto-selection

**Priority: Include in Phase 1, not deferred**

**UI Placement:**
- Small dropdown button in the top-right corner of the visualization canvas
- Label: "Chart type: Auto" when using system selection
- When user overrides: "Chart type: Bar" with a clear indicator

**Recommended Chart Options (in dropdown):**
- Auto (default)
- Table
- Line
- Bar (Vertical)
- Bar (Horizontal)
- Pie
- Donut
- Scatter

**Key UX Requirement:**
When override differs from auto-selection, show a tooltip on hover explaining why the system chose what it did: "Auto selected line chart because query contains 'trend'"

---

## From Consumer Spending SME (consumer-spending-sme)

---

**Question 1: Market Share Visualization with Trajectory**

> When presenting market share results, what chart types effectively communicate both absolute share and share trajectory (gaining/losing)? Analysts typically want to see both at once.

**Answer: Grouped Bar Chart with Trend Sparklines**

For market share with trajectory, I recommend:

**Primary: Grouped Bar Chart (Horizontal)**
```
| Brand X    ████████████████  18.2%  ↗ +110bps |
| Brand Y    ████████████  14.8%  ↘ -50bps      |
| Brand Z    █████████  12.1%  →  +30bps        |
```

- Bar length = absolute share
- Color = trajectory (green=gaining, red=losing, gray=stable)
- Arrow indicator + bps change for precise reading

**Secondary: Dual-Axis Line Chart**
- Left axis: Absolute share percentage
- Right axis: Basis point change
- This shows trajectory as a line, making trend direction immediately visible

**NOT Recommended:**
- Pie charts for trajectory - cannot show change over time
- Single KPI cards - lose comparison context

**Consumer Spending Insight:** For cross-shopping data showing gaining/losing share, a **Sankey diagram** or **waterfall chart** effectively shows flow between brands.

---

**Question 2: Cross-Shopping Visualization for Many Brand Pairs**

> For cross-shopping analysis results (potentially many brand pairs), how should the UI handle visualization when there are 10+ significant cross-shopping relationships?

**Answer: Tiered Visualization with Filter/Sort**

When facing 10+ brand pairs:

**Tier 1: Top Relationships (Default View)**
- Show top 5-7 relationships as horizontal bar chart
- Sort by overlap percentage (highest first)
- Color intensity indicates strength

**Tier 2: Full Matrix (Explicit Action)**
- "View full matrix" button
- Opens a heatmap where:
  - Rows = source brand
  - Columns = cross-shopped brands
  - Cell color = overlap intensity

**Tier 3: Search/Filter**
- Search input: "Filter to brand X"
- Shows only relationships involving X

**Cardinality Handling:**
| Number of Pairs | Visualization Approach |
|-----------------|------------------------|
| 1-5 | Full matrix / heatmap |
| 6-10 | Horizontal bar chart, sorted |
| 11-20 | Top 10 bar + "View all" |
| 20+ | Filtered view required |

**DON'T:** Render a 20-brand Sankey - it's unreadable. Force filtering.

---

**Question 3: Ambiguous Query HITL Interaction Pattern**

> When a user query is ambiguous and requires HITL clarification, what interaction pattern keeps users engaged without breaking conversational flow?

**Answer: Inline Suggestion Cards within Chat Stream**

**Recommended Pattern: Inline Clarification Card**

```
[User query bubble]
  "Show me Nike's performance"

[System response card - inline, NOT modal]
┌─────────────────────────────────────────┐
│ I found multiple interpretations:       │
│                                         │
│ ○ Market share in [category]?           │
│ ● Sales trends over time?               │
│ ○ Customer demographics?                │
│                                         │
│ Select one or rephrase your question    │
└─────────────────────────────────────────┘

[Continue typing - input stays active]
```

**Key Principles:**

1. **NOT a modal dialog** - Modals break conversational flow and feel blocking
2. **Inline within chat** - Same visual treatment as messages, just a different bubble type
3. **Keep input active** - User can type follow-up or click an option
4. **Max 3 options** - If more interpretations exist, show top 2 and "Other..."
5. **Context preserved** - The original query remains visible above

**Avoid:**
- Toast notifications for clarification
- Full-page interruptions
- Rejection of the query without guidance

---

## From Market Analyst SME (market-analyst-sme)

---

**Question 1: Chart Interaction Priorities**

> What ECharts interaction patterns are most valuable? Should analysts prioritize hover tooltips and legend toggling, or are there more advanced interactions (brush select, data zoom) that analysts actually use?

**Answer: Prioritize Core, Add Advanced as Secondary**

**Must-Have (Core):**
1. **Hover tooltips** - Essential, shows exact values on hover
2. **Legend toggling** - Critical for multi-series charts (show/hide brands)
3. **Responsive resize** - Chart must adapt to container size

**Should-Have (High Value):**
4. **Data zoom (slider)** - For time-series with 8+ quarters; analysts do use this
5. **Click-to-highlight** - Click a legend item or bar to highlight related data

**Nice-to-Have (Lower Priority):**
6. **Brush select** - Useful for custom range selection but rarely used by non-power users
7. **Pan/Drag** - Secondary to zoom for time-series

**Priority Order:**
1. Tooltips (non-negotiable)
2. Legend toggle (non-negotiable)
3. Data zoom slider (highly recommended for trend analysis)
4. Click highlighting (moderate value)
5. Brush select (defer to Phase 2)

**Market Analyst Context:** Your eval query suite mentions analysts comparing "Brand X vs Brand Y" frequently. Legend toggle is essential here - analysts want to isolate one brand to see its trend clearly, then toggle another back in.

---

**Question 2: Clarification UX Presentation**

> How should ambiguous query clarifications be presented? Modal dialog? Inline suggestion? Chat follow-up?

**Answer: Inline Chat Follow-Up (Same as Consumer Spending Recommendation)**

Reiterating from above: **Inline suggestion cards within the chat stream**, not modals.

Pattern:
```
[User] "How's Nike doing?"

[System follows up inline]
┌──────────────────────────────────────┐
│ To help with "Nike's performance":   │
│                                      │
│ Did you mean:                        │
│ ○ Nike's market share?               │
│ ● Nike's sales trend over time?      │
│ ○ Nike vs competitors?               │
│                                      │
│ [Type another question anytime]      │
└──────────────────────────────────────┘
```

The input remains active and usable. User can either click an option OR type a more specific query.

---

**Question 3: Report Export Formats**

> What export formats do analysts actually use? CSV for data, PNG for charts, or PDF for full reports?

**Answer: CSV is King, PNG is Secondary, PDF is Rarely Used**

**Analyst Export Priority:**
| Format | Frequency | Use Case |
|--------|-----------|----------|
| **CSV** | Very High | Import into Excel, build custom models, share with colleagues |
| **PNG/SVG** | Medium | Insert into slides, reports |
| **PDF** | Low | Formal distribution; analysts usually screenshot or export anyway |
| **Excel** | Medium | Same as CSV but preserves formatting |

**Recommendation:**
1. **CSV Export** - Primary export, always available
2. **PNG Export** - For individual charts, available via chart toolbar
3. **Excel (XLSX)** - Nice-to-have, uses same data as CSV

**UI Placement:**
- Table view: "Export CSV" button in table header
- Chart: Download icon in chart toolbar (PNG)
- Dashboard: "Export all data" in header or overflow menu

**DON'T Over-Invest In:**
- PDF report generation - rarely used, complex to implement correctly
- Custom formatting options in exports - CSV should be raw data

---

**Question 4: Dashboard Aesthetic**

> Should this feel more like a Bloomberg terminal (dense, keyboard-driven) or a modern SaaS tool (cleaner, mouse-driven)? This affects information density decisions.

**Answer: Modern SaaS with Bloomberg's Analytical Depth**

**Target Aesthetic: Bloomberg's Information Density with Figma's Usability**

This is a tool for analysts who:
- Use Bloomberg for market data (familiar with density)
- Use modern SaaS tools like Notion, Linear (expect polish)
- Are checking "5 times a day" between other tasks (need speed)

**Design Direction:**
- **Clean visual hierarchy** - Whitespace, clear typography, modern font stack
- **High information density** - Don't waste space, but organize logically
- **Mouse-driven primary** - Keyboard shortcuts for power users only (e.g., Cmd+K for new query)
- **No terminal aesthetics** - Dark mode acceptable but no green-on-black

**Density Guidelines:**
- Bloomberg: ~80% content, 20% chrome
- Modern SaaS: ~60% content, 40% whitespace/chrome
- **Proteus Target: ~70% content, 30% breathing room**

**Why Not Full Bloomberg:**
- Bloomberg's density assumes dedicated screen real estate and keyboard mastery
- Our users are multitasking professionals, not terminal-native traders
- The "modern SaaS" feel lowers learning curve and increases adoption

**Minimum Spacing:**
- Chart padding: 24px
- Card gaps: 16px
- Section margins: 32px

---

## From Data Analytics SME (data-analytics-sme)

---

**Question 1: KPI Card vs. Visualization for Single Aggregate Values**

> For queries that return single aggregate values (e.g., "average Target spend"), should we skip chart rendering entirely and show a large KPI card? Or always render a visualization even for trivial results?

**Answer: KPI Card is Correct - Skip Chart Rendering**

**Strong recommendation: KPI card for single aggregates.**

When a query returns ONE number (average, total, count), a chart is meaningless - there's nothing to visualize. For example:

**KPI Card Design:**
```
┌─────────────────────────────────────────┐
│  Average Target Spend (Last Quarter)     │
│                                         │
│       $847.32                           │
│                                         │
│  ▲ 12.4% vs prior quarter              │
│  📊 vs category avg: +$142              │
└─────────────────────────────────────────┘
```

**Decision Tree:**
| Result Shape | Display |
|-------------|---------|
| Single value | KPI Card (large number + context) |
| 2-10 values (categories) | Chart (bar, pie, etc.) |
| Time series | Line chart |
| 2 numeric dimensions | Scatter plot |

**Key UX Requirement:** The KPI card should still have a "View as chart" toggle for users who want to see the trend leading to this number.

---

**Question 2: Result Set Cardinality and Pagination**

> What's the expected cardinality of result sets? If a query returns 10,000 rows (e.g., all transactions), how should we handle pagination or aggregation? The current spec mentions "basic interactivity" - does this include scroll/pagination for large tables?

**Answer: Pagination Required, Aggregation Recommended**

**For Large Result Sets:**

**Threshold Strategy:**
| Row Count | Approach |
|-----------|----------|
| 1-100 | Full table display |
| 101-1,000 | Paginated (50 rows/page) OR scroll with virtualization |
| 1,001-10,000 | Aggregated view suggested; raw data on demand |
| 10,000+ | Auto-aggregate with "View raw data" option |

**Table UX Requirements:**
- Virtual scrolling for 100+ rows (render only visible rows)
- Sticky header row
- Sort by any column (client-side for <1000 rows)
- Pagination controls: "Showing 1-50 of 847 | Page 1 of 17"

**For Transaction-Level Data:**
- Never return raw 10,000 transactions as a table
- Offer aggregation options: "Group by day/week/month"
- Show summary statistics first (trend line)

**Context:** Analysts asking for "all transactions" typically want to find outliers or export. Better UX: "Showing 847 transactions (sample). Try filtering or export as CSV for full dataset."

---

**Question 3: Visualization Comparison for Time Periods**

> How should users compare two different time periods' visualizations side-by-side? Tabbed interface or split-screen?

**Answer: Split-Screen for Comparison, Tabs for Navigation**

**Different Use Cases Demand Different Patterns:**

**Comparison (analysts want to see side-by-side):**
```
┌────────────────────┬────────────────────┐
│   Q3 2024          │   Q3 2023          │
│   [Chart]          │   [Chart]          │
│                    │                    │
│   ↗ +12.4% YoY     │   baseline         │
└────────────────────┴────────────────────┘
```

**Navigation (analysts want to switch context):**
```
[Q3 2024] [Q2 2024] [Q1 2024] [Q4 2023]  ← Tab bar
[Chart content changes based on selected tab]
```

**Recommendation:**
1. **Tabbed interface for switching between time periods** (quick exploration)
2. **Split-screen when user explicitly asks "compare Q3 to Q3"** (explicit comparison request)
3. **Support both patterns** with user control

**UI Pattern:**
- Default: Tabbed (one period visible at a time)
- On explicit comparison query: Auto-open split-screen
- Manual toggle: "Split view" button in chart header

**Split Screen Limits:**
- Maximum 2 panels side-by-side (more becomes unreadable)
- Minimum panel width: 400px (below this, stack vertically)

---

**Question 4: Chart Annotation**

> Should analysts be able to annotate charts with insights or notes? If so, where should these annotations persist?

**Answer: Yes, with Clear Scope Boundaries**

**Recommended Annotation Feature:**

**Types of Annotations:**
1. **Point annotation** - Click a data point, add a note ("Q3 spike due to Prime Day")
2. **Range annotation** - Highlight a time range, add context ("COVID impact period")
3. **Chart-level note** - General insight about the entire visualization

**UI Pattern:**
- Click data point → Small "+" icon appears → Click to add note
- Notes appear as small badges/icons on annotated points
- Hover badge → Tooltip with note content
- Click badge → Expand to full note view

**Where Annotations Persist:**
- **Session-scoped by default** - Saved in conversation history
- **Exportable** - Annotations included in PNG export (overlay)
- **NOT shared by default** - Private to the analyst unless explicitly shared

**Storage:**
- Attach annotations to the (query, result) pair
- Include in conversation history
- DO NOT persist to raw data layer

**Don't Over-Engineer:**
- No collaborative annotation in Phase 1
- No annotation search/browsing - keep scope tight
- If complexity exceeds budget, defer to Phase 2

---

**Question 5: Data Table Placement**

> For charts that also show raw data, should tables be accessible via toggle, always visible below, or in expandable drawer?

**Answer: Toggle is Correct - Default to Chart, Table on Demand**

**Recommended Pattern:**

```
┌─────────────────────────────────────────┐
│  [Chart Title]           [Table] [▾]    │
│─────────────────────────────────────────│
│                                         │
│           [CHART]                       │
│                                         │
└─────────────────────────────────────────┘
```

**Toggle States:**
1. **Default: Chart only** - Clean view, no table visible
2. **Toggle to Table** - Chart collapses to small preview, full table below
3. **Toggle to Both** - Split view with chart (40%) and table (60%)

**Why Toggle (Not Always-Visible):**
- Tables add visual noise when user wants to see the chart
- Most users want chart first, table second
- Power users who always want tables can set a preference

**Why Not Drawer:**
- Drawers hide data, requiring extra click to access
- Tables in drawers are hard to compare with chart
- Modal tables interrupt flow entirely

**Exception:** For queries returning ONLY tabular data (no visualization applicable), show table as primary, not toggled.

---

**Question 6: Query History Navigation**

> With canvas updates per query, what interaction pattern helps users navigate back to prior visualizations without losing context?

**Answer: Conversation History with Thumbnail Previews**

**Recommended Pattern:**

**Chat Sidebar Shows:**
```
┌─────────────────────────┐
│ [New Query Button]      │
├─────────────────────────┤
│ ○ Today 2:30 PM          │
│   "Target vs Walmart..." │
│   [Thumbnail preview]   │
├─────────────────────────┤
│ ○ Today 2:15 PM          │
│   "Nike market share..." │
│   [Thumbnail preview]   │
├─────────────────────────┤
│ ○ Today 1:45 PM          │
│   "Grocery trends..."   │
│   [Thumbnail preview]   │
└─────────────────────────┘
```

**Clicking a History Item:**
1. Loads that query's visualization into main canvas
2. Scrolls chat to show that message
3. Context is preserved - user can continue from that point

**Additional Features:**
- **Keyboard shortcut:** Cmd/Ctrl + K opens history search
- **"Branch from here"** - Start new conversation from a past query
- **Hover preview** - Hovering a history item shows larger thumbnail

**What's NOT Recommended:**
- Separate "History" tab/window (loses context)
- Modal history picker (too disruptive)
- Linear undo stack (doesn't fit conversational model)

**Key Principle:** The chat IS the history. Don't create a separate navigation paradigm.

---

## Summary

| Question Topic | Recommendation |
|----------------|----------------|
| Observability toggle | Header toggle, NOT slide-out panel; per-message expand when toggled on |
| Chart override | Include in Phase 1; dropdown in chart corner; show auto-selection reasoning |
| Market share + trajectory | Grouped horizontal bar with color-coded trend indicators |
| Cross-shopping 10+ pairs | Top-N bar + filter for rest; heatmap for explicit matrix request |
| HITL clarification | Inline suggestion cards in chat stream, NOT modals |
| Chart interactions | Tooltips + legend toggle (required), data zoom (recommended) |
| Export formats | CSV primary, PNG secondary, PDF rarely needed |
| Dashboard aesthetic | Modern SaaS with Bloomberg-level information density |
| Single aggregate | KPI card (no meaningless chart) |
| Large result sets | Paginate/virtualize tables; suggest aggregation for 1000+ rows |
| Time period comparison | Tabs for navigation, split-screen for explicit comparison |
| Chart annotations | Point annotations with session persistence, defer collaborative features |
| Table placement | Toggle to table; default to chart-only |
| Query history | Chat sidebar with thumbnail previews; chat IS the history |
