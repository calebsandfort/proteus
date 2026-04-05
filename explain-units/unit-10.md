# Unit 10: Visualization Engine

> **Status:** Implemented
> **FR Coverage:** FR-5.1, FR-5.2, FR-5.3, FR-5.4, FR-5.5, FR-5.6, FR-5.7, FR-5.8, FR-5.9
> **Dependencies:** IU-3 (ASP.NET Core Data API)*

## Overview

Unit 10 implements the visualization layer of Proteus, providing interactive chart rendering, automatic chart-type selection, and comprehensive data presentation for consumer transaction analytics. This unit uses **ECharts** as the primary charting library, integrated with a smart selection system that automatically chooses the optimal visualization based on query patterns and result shape.

The visualization engine sits at the end of the user query pipeline, receiving structured data from the backend (via IU-8's SSE streaming) and transforming it into interactive visual representations. It supports 14 distinct chart types ranging from simple KPI cards to complex multi-series visualizations like choropleth maps and bump charts. The engine also handles table views, result set pagination, and thumbnail generation for conversation history.

This unit is critical for enabling analysts to quickly interpret query results. Rather than presenting raw data tables, the system automatically selects the most appropriate visualization based on natural language patterns in the query (e.g., "trend over time" suggests a line chart, "market share" suggests a pie/donut chart).

## Functionality Implemented

- **Auto Chart-Type Selection** (FR-5.1) — Decision matrix selecting from 14 chart types based on query keywords and result shape (KPI, line, bar, horizontal_bar, pie, donut, stacked_bar, scatter, heatmap, choropleth, stacked_area, waterfall, bump, table)
- **Manual Override** (FR-5.2) — Floating toolbar with dropdown to manually select chart type, includes tooltip explaining auto-selection reasoning
- **KPI Card Display** (FR-5.3) — Single value display with prior period comparison (YoY/MoM), category average comparison, growth rate indicator, "View as table" toggle
- **Table Toggle** (FR-5.4) — View mode switcher: Chart only, Table only, Both (split view); persisted to localStorage
- **Chart Interactivity - Required** (FR-5.5) — Hover tooltips, legend toggling, responsive resize
- **Chart Interactivity - Advanced** (FR-5.6) — Data zoom (slider) for 8+ data points, click-to-highlight, reset button
- **Result Set Handling** (FR-5.7) — Full display (1-100), paginated (101-1000), aggregated (1001-10000), mandatory aggregation (10000+)
- **Visualization Updates** (FR-5.8) — Canvas updates per query, thumbnail generation (64x48px, 4:3 aspect) for history, hover tooltips with query text, click to re-render
- **Chart Interaction Details** (FR-5.9) — Drill-down on click, export dropdown (PNG, CSV), empty state display

## Implementation Details

### Technology Stack

- **Charting Library:** ECharts (`echarts` npm package)
- **Framework:** Next.js 14 with React hooks
- **UI Components:** ShadCN/ui primitives with Tailwind CSS
- **State Management:** React hooks with localStorage for view mode persistence
- **Testing:** Vitest with unit tests for chart selection logic

### Architecture Patterns

**Chart Selection Pipeline:**
The selection system uses a decision matrix approach with confidence scoring:
1. Query analysis extracts keywords (trend, compare, share, ranking, etc.)
2. Result shape analysis determines row count, time dimension presence, series count, metric type
3. Rules are evaluated in priority order, returning first match with confidence score
4. Fallback to line (if time dimension) or bar chart with 0.6 confidence

**ECharts Integration:**
The `echarts-config.ts` provides base configurations that all chart types extend. This includes:
- Consistent tooltip styling (dark theme, rounded corners)
- Legend positioning and text styling
- Grid configuration with label containment
- Responsive resize handling via `window.addEventListener('resize')`

**KPI Calculation:**
KPI cards compute comparisons using the formula: `((current - prior) / prior) * 100`
- YoY comparison: Same quarter, prior year
- MoM comparison: Prior month
- Category average: Unweighted mean of all brands in queried category

### Key Design Decisions

1. **Confidence-Based Selection** — Each rule returns a confidence score (0.80-0.95), allowing fallback logic and future confidence-weighted ensemble approaches
2. **LocalStorage View Mode** — User's chart/table/both preference persists across sessions via `proteus_view_mode` key
3. **Thumbnail via ECharts.getDataURL()** — Uses canvas snapshot at 0.5 pixel ratio for efficient 64x48px thumbnails
4. **Aggregation Triggers** — Result set thresholds (100/1000/10000) trigger different handling to prevent browser performance degradation
5. **Drill-Down Prompt** — "Click to explore" appears in detailed tooltips, enabling future sub-query generation

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/components/visualization/VisualizationCanvas.tsx` | Main canvas component coordinating chart, KPI, and table rendering |
| `frontend/src/components/visualization/ChartComponent.tsx` | ECharts wrapper with event handlers, tooltips, zoom, export |
| `frontend/src/components/visualization/KPICard.tsx` | Single value display with comparisons and growth indicators |
| `frontend/src/components/visualization/ChartToolbar.tsx` | Manual override dropdown with auto-selection reasoning tooltip |
| `frontend/src/components/visualization/ViewModeToggle.tsx` | Chart/Table/Both toggle with localStorage persistence |
| `frontend/src/components/visualization/EmptyChart.tsx` | Empty state display for no-data queries |
| `frontend/src/lib/chart-selection.ts` | Decision matrix with 12 rules for auto chart-type selection |
| `frontend/src/lib/echarts-config.ts` | Base chart configurations (tooltip, legend, grid) and type-specific configs |
| `frontend/src/lib/result-set-handler.ts` | Pagination and aggregation logic based on row count thresholds |
| `frontend/src/lib/query-response.ts` | Query response type definitions and utilities |
| `frontend/src/hooks/use-visualization-history.ts` | Thumbnail generation, history management, click-to-restore |

## Integration Points

### This Unit Provides

- **To IU-9 (Chat UI):** VisualizationCanvas renders in main canvas area; MessageBubble embeds chart data in tool results; thumbnail previews for conversation history
- **To IU-11 (Model Selector):** View mode toggle state shared via localStorage
- **To Users:** Interactive charts, KPI cards, table views, export functionality
- **To localStorage:** `proteus_view_mode` key for view preference persistence

### This Unit Depends On

- **IU-8 (Response Generation):** Query results passed via SSE as tool result data
- **IU-3 (Data API):** API contracts for query response shape (can use mock data)
- **ECharts:** `echarts` npm package for all chart rendering
- **Next.js:** React context and window API for resize handling

## Usage Guide

### Rendering a Chart

The VisualizationCanvas receives query results and handles selection and rendering:

```typescript
import { VisualizationCanvas } from '@/components/visualization/VisualizationCanvas';
import { selectChartType } from '@/lib/chart-selection';

// Input from backend query result
const input = {
  query: "Show Walmart's market share trend over time",
  toolId: "market_share_daily",
  resultShape: {
    rowCount: 12,
    hasTimeDimension: true,
    hasMultipleSeries: false,
    metricType: "time_series"
  }
};

// Auto-select chart type
const { chartType, confidence } = selectChartType(input);

// Render
<VisualizationCanvas data={queryResult} chartType={chartType} />
```

### Manual Override

Users can override auto-selection via ChartToolbar:

```typescript
// Toolbar provides override options
const overrideOptions = ['auto', 'table', 'line', 'bar', 'horizontal_bar', 'pie', 'donut', 'scatter'];

// When override differs from auto, show reasoning
<ChartToolbar
  autoChartType={autoSelected}
  selectedChartType={userSelected}
  showReasoning={userSelected !== autoSelected}
/>
```

### View Mode Toggle

Switch between visualization modes:

```typescript
// View mode stored in localStorage
localStorage.getItem('proteus_view_mode'); // 'chart' | 'table' | 'both'

<ViewModeToggle
  currentMode={viewMode}
  onChange={setViewMode}
/>
```

### Exporting Charts

ECharts provides native export:

```typescript
// PNG export via chart instance
chartInstance.getConnectedDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' });

// CSV export requires manual conversion
const csvContent = convertToCSV(data);
downloadAsFile(csvContent, 'export.csv');
```

### Running Tests

```bash
cd frontend
pnpm test -- --run lib/chart-selection
pnpm test -- --run lib/result-set-handler
```

## Git History

| Commit | Date | Message |
|--------|------|---------|
| `2ebed28` | 2026-04-04 | feat: implement Unit 10 Visualization Engine |
| `45bee9f` | 2026-04-04 | Merge branch 'unit-10' |

---

*Note: IU-3 (Data API) is listed as a soft dependency (*), allowing parallel development. The visualization engine can work with mock data during development before the API is fully integrated.*