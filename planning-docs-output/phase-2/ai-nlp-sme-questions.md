# Cross-SME Questions for AI/NLP SME (ai-nlp-sme)

## From Integration Engineer SME (integration-engineer-sme)

**Context:** The Integration Engineer is designing the data retrieval API and AI pipeline integration. They need to understand how the AI pipeline handles aggregation level determination and the network path to the data API.

1. **Aggregation Level in Tool Selection Pipeline:**
   How does the tool selection pipeline determine which aggregation level to request from the API? If the user asks "What were Target's sales last quarter?" the pipeline must decide whether to request daily, weekly, or monthly aggregates. Does this decision happen during dimension extraction or during tool selection? Should the AI pipeline be aware of aggregation level at all, or should it always request `aggregation: "auto"` and let the API decide?

2. **Expected Network Path from FastAPI to Data API:**
   What is the expected network path from FastAPI to the data API? If the data API is ASP.NET Core (per HLRD) vs. FastAPI endpoints (per established stack), the pipeline's call pattern differs. Is the pipeline making HTTP calls to an external API, or calling internal service methods?

---

## From UX Designer SME (ux-designer-sme)

**Context:** The UX Designer is implementing the observability panel and HITL clarification patterns. They need to understand what data the AI pipeline can surface and what format HITL responses should take.

1. **Observability Panel Data Surface:**
   How does the observability panel surface tool selection reasoning? Should it show RAG retrieval scores, LLM confidence scores, or just the final selected tool? What's the performance cost of surfacing this data per message?

2. **Ambiguous Query HITL Format:**
   For ambiguous queries triggering HITL clarification, what's the expected format from the LLM? Can it provide confidence scores for each candidate, or just a list?

---

## From Consumer Spending SME (consumer-spending-sme)

**Context:** The Consumer Spending SME is modeling synthetic data correlations and designing tool capabilities. They need to understand how the AI handles multi-tool queries and dimension disambiguation.

1. **Multi-Tool Query Handling:**
   How does the RAG-based tool retrieval handle cases where a user query spans multiple analytical capabilities (e.g., "show me Target's market share trend by generation compared to Walmart" requires both market share and demographic analysis)?

2. **Dimension Disambiguation Strategy:**
   What is the strategy for disambiguating dimension references when users say vague terms like "recently," "most," or "growing"? How do you map these to specific time ranges or comparison operators?

3. **Synonym and Layman Term Handling:**
   How will the system handle dimension extraction when users use synonyms or layman terms (e.g., "young people" for Gen Z, "credit card" broadly for all card types)?

---

## From Market Analyst SME (market-analyst-sme)

**Context:** The Market Analyst is prioritizing tools and designing the eval framework. They need AI/NLP guidance on tool prioritization, clarification language, and multi-turn context.

1. **Tool Prioritization for Eval Suite:**
   Given the 10-50 tool range, which analytical capabilities are most valuable for investor/analyst audiences? The Market Analyst needs this to prioritize which tools to implement first for the eval suite. Common analyst questions suggest: market share, cross-shopping, customer demographics, and transaction volume trends.

2. **Eval Query Examples:**
   The Market Analyst can provide 20-30 representative queries across complexity levels for the eval suite. What natural language phrasing should these queries use?

3. **Clarification Language Expectations:**
   When the system asks for clarification, what phrasing do analysts expect? For example, "Which time period?" vs. "Did you mean last quarter or the past 3 months?" Domain-appropriate phrasing improves user trust.

---

## From Data Analytics SME (data-analytics-sme)

**Context:** The Data Analytics SME is designing statistical validation and result sanity checks. They need to understand how the AI pipeline handles temporal ambiguity and validation.

1. **Temporal Ambiguity Resolution:**
   How does the NLP layer handle queries like "show spending" without explicit time range? Should we default to last 30 days, current month, or ask for clarification?

2. **Multi-Tool Orchestration:**
   With 10-50 tools each having 30+ dimensions, how should tool selection handle compound queries that span multiple tools?

3. **Clarification Generation Criteria:**
   When aggregation granularity is ambiguous, what criteria should the NLP layer use to generate appropriate clarification questions?

4. **Confidence Thresholds for Clarification:**
   What tool selection confidence level should trigger a clarification prompt vs. proceeding with best guess?
