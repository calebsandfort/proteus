# Cross-SME Questions for UX Designer SME (ux-designer-sme)

## From AI/NLP SME (ai-nlp-sme)

**Context:** The AI/NLP SME is designing the observability panel and chart type override features. They recommend a collapsed sidebar toggle and support manual chart override.

1. **Observability Panel Default State:**
   From an AI pipeline perspective, a collapsed sidebar toggle (not per-message expansion) is recommended. Per-message expansion would interrupt conversation flow and complicate streaming implementation. The toggle should show a slide-out panel that doesn't reflow the main canvas. What are your thoughts on this implementation approach?

2. **Chart Type Override:**
   Should users be able to manually override the auto-selected chart type? From an AI perspective, this is low-cost to implement - just expose a dropdown after visualization renders. The AI/NLP SME recommends adding this for power users. Do you agree with this prioritization?

---

## From Consumer Spending SME (consumer-spending-sme)

**Context:** The Consumer Spending SME is designing market share and cross-shopping visualizations. They need UX guidance on effective chart types and interaction patterns.

1. **Market Share Visualization with Trajectory:**
   When presenting market share results, what chart types effectively communicate both absolute share and share trajectory (gaining/losing)? Analysts typically want to see both at once. What visualization approach do you recommend?

2. **Cross-Shopping Visualization for Many Brand Pairs:**
   For cross-shopping analysis results (potentially many brand pairs), how should the UI handle visualization when there are 10+ significant cross-shopping relationships?

3. **Ambiguous Query HITL Interaction Pattern:**
   When a user query is ambiguous and requires HITL clarification, what interaction pattern keeps users engaged without breaking conversational flow?

---

## From Market Analyst SME (market-analyst-sme)

**Context:** The Market Analyst is prioritizing chart interactions and report export features. They need UX guidance on what ECharts interactions analysts actually use.

1. **Chart Interaction Priorities:**
   What ECharts interaction patterns are most valuable? Should analysts prioritize hover tooltips and legend toggling, or are there more advanced interactions (brush select, data zoom) that analysts actually use?

2. **Clarification UX Presentation:**
   How should ambiguous query clarifications be presented? Modal dialog? Inline suggestion? Chat follow-up?

3. **Report Export Formats:**
   What export formats do analysts actually use? CSV for data, PNG for charts, or PDF for full reports?

4. **Dashboard Aesthetic:**
   Should this feel more like a Bloomberg terminal (dense, keyboard-driven) or a modern SaaS tool (cleaner, mouse-driven)? This affects information density decisions.

---

## From Data Analytics SME (data-analytics-sme)

**Context:** The Data Analytics SME is designing KPI card vs. chart rendering and large result set handling.

1. **KPI Card vs. Visualization for Single Aggregate Values:**
   For queries that return single aggregate values (e.g., "average Target spend"), should we skip chart rendering entirely and show a large KPI card? Or always render a visualization even for trivial results?

2. **Result Set Cardinality and Pagination:**
   What's the expected cardinality of result sets? If a query returns 10,000 rows (e.g., all transactions), how should we handle pagination or aggregation? The current spec mentions "basic interactivity" - does this include scroll/pagination for large tables?

3. **Visualization Comparison for Time Periods:**
   How should users compare two different time periods' visualizations side-by-side? Tabbed interface or split-screen?

4. **Chart Annotation:**
   Should analysts be able to annotate charts with insights or notes? If so, where should these annotations persist?

5. **Data Table Placement:**
   For charts that also show raw data, should tables be accessible via toggle, always visible below, or in expandable drawer?

6. **Query History Navigation:**
   With canvas updates per query, what interaction pattern helps users navigate back to prior visualizations without losing context?
