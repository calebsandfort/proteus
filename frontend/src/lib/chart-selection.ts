/**
 * Chart Type Selection Engine
 * Implements FR-5.1: Auto Chart-Type Selection
 *
 * Decision matrix that maps query patterns and result shapes to appropriate chart types.
 */

export type ChartType =
  | 'kpi'
  | 'line'
  | 'bar'
  | 'horizontal_bar'
  | 'pie'
  | 'donut'
  | 'stacked_bar'
  | 'scatter'
  | 'heatmap'
  | 'choropleth'
  | 'stacked_area'
  | 'waterfall'
  | 'bump'
  | 'table'

export interface ChartSelectionInput {
  queryText: string
  resultShape: {
    rowCount: number
    hasTimeDimension: boolean
    categoryCount: number
    valueCount: number
  }
}

export interface ChartSelectionResult {
  chartType: ChartType
  confidence: number
  reasoning?: string
}

/**
 * Pattern matchers for query intent detection
 */
const KPI_PATTERNS = /\b(average|total|sum|total|mean|median|count|count of)\b/i
const TIME_PATTERNS = /\b(over time|trend|history|historical|over the|by (month|quarter|year|week)|time series|daily|weekly|monthly|quarterly|yearly|annually)\b/i
const COMPARE_PATTERNS = /\b(compare|vs|versus|compared to|against|competition|competition between)\b/i
const PIE_PATTERNS = /\b(percentage|proportion|distribution|segmentation)\b/i
const MULTI_DIMENSION_PATTERNS = /\b(across|by|segmented|segment|split|grouped|stacked)\b/i
const SCATTER_PATTERNS = /\b(correlation|relationship|scatter|relate|compare.*vs|improve|depend)\b/i
const RANKING_PATTERNS = /\b(ranking|rank|top|bottom|best|worst|leading|lagging|highest|lowest)\b/i
const STACKED_AREA_PATTERNS = /\b(share trend|market share trend|trend over time|evolving share|changing share)\b/i
const WATERFALL_PATTERNS = /\b(decomposition|decompose|drivers?|contribution|breakdown|waterfall|impact|effect of|change in)\b/i
const BUMP_PATTERNS = /\b(ranking change|ranking evolution|rankings? (change|evolve|evolution)|how did (the )?(brand )?rankings|rankings over time|ranking trend|position changed|climbing|falling)\b/i

/**
 * Selects the most appropriate chart type based on query text and result shape.
 * Pure function with no side effects.
 */
export function selectChartType(input: ChartSelectionInput): ChartSelectionResult {
  const { queryText, resultShape } = input
  const { rowCount, hasTimeDimension, categoryCount, valueCount } = resultShape

  // KPI Card: single aggregate values
  if (rowCount === 1 && categoryCount === 0 && valueCount === 1) {
    if (KPI_PATTERNS.test(queryText)) {
      return { chartType: 'kpi', confidence: 0.95, reasoning: 'Single aggregate value detected with metric keyword' }
    }
  }

  // Scatter Plot: correlation/relationship with 2+ value columns
  if (valueCount >= 2 && SCATTER_PATTERNS.test(queryText)) {
    return { chartType: 'scatter', confidence: 0.85, reasoning: 'Correlation or relationship query with multiple value dimensions' }
  }

  // Scatter fallback: multiple values without categories
  if (valueCount >= 2 && categoryCount === 0 && !hasTimeDimension) {
    return { chartType: 'scatter', confidence: 0.7, reasoning: 'Multiple value dimensions suggest scatter plot' }
  }

  // Line Chart: time series data (STACKED_AREA and BUMP take precedence within this block)
  if (hasTimeDimension && TIME_PATTERNS.test(queryText)) {
    if (STACKED_AREA_PATTERNS.test(queryText) && categoryCount >= 2) {
      return { chartType: 'stacked_area', confidence: 0.9, reasoning: 'Share trend over time with multiple categories' }
    }
    if (BUMP_PATTERNS.test(queryText) && categoryCount >= 2) {
      return { chartType: 'bump', confidence: 0.9, reasoning: 'Ranking change query with time dimension' }
    }
    return { chartType: 'line', confidence: 0.85, reasoning: 'Time series query detected' }
  }

  // Bump Chart: ranking changes over time (outside TIME block — for queries where TIME_PATTERNS doesn't match but result has time dimension)
  if (hasTimeDimension && BUMP_PATTERNS.test(queryText) && categoryCount >= 2) {
    return { chartType: 'bump', confidence: 0.9, reasoning: 'Ranking change query with time dimension' }
  }

  // Horizontal Bar: ranking queries
  if (RANKING_PATTERNS.test(queryText) && categoryCount >= 3) {
    return { chartType: 'horizontal_bar', confidence: 0.85, reasoning: 'Ranking query with multiple categories' }
  }

  // Pie/Donut: share/percentage/proportion (checked before Stacked Bar per FR-5.1)
  if (PIE_PATTERNS.test(queryText) && categoryCount >= 2 && categoryCount <= 8) {
    return { chartType: 'pie', confidence: 0.85, reasoning: 'Share/percentage query with categorical breakdown' }
  }

  // Stacked Bar: multi-dimension queries (requires more specific "across"/"segmented" keywords)
  if (MULTI_DIMENSION_PATTERNS.test(queryText) && categoryCount >= 2) {
    return { chartType: 'stacked_bar', confidence: 0.8, reasoning: 'Multi-dimensional query with segmentation' }
  }

  // Bar Chart: comparison queries
  if (COMPARE_PATTERNS.test(queryText) && categoryCount >= 2 && categoryCount <= 5) {
    return { chartType: 'bar', confidence: 0.8, reasoning: 'Comparison query with 2-5 categories' }
  }

  // Waterfall: decomposition queries (after Pie — "driver"/"decomposition" is more specific than "change")
  if (WATERFALL_PATTERNS.test(queryText)) {
    return { chartType: 'waterfall', confidence: 0.85, reasoning: 'Decomposition or driver analysis query' }
  }

  // Line fallback: time dimension without clear pattern
  if (hasTimeDimension && rowCount >= 3) {
    return { chartType: 'line', confidence: 0.6, reasoning: 'Time series data detected' }
  }

  // KPI fallback: single row with metric keyword
  if (rowCount === 1 && KPI_PATTERNS.test(queryText)) {
    return { chartType: 'kpi', confidence: 0.8, reasoning: 'Single aggregate value with metric keyword' }
  }

  // Horizontal bar fallback: ranking with small category count
  if (RANKING_PATTERNS.test(queryText) && categoryCount >= 2) {
    return { chartType: 'horizontal_bar', confidence: 0.7, reasoning: 'Ranking query detected' }
  }

  // Bar fallback: comparison with small category count (before table — "show all data" with categories is a bar)
  if (categoryCount >= 2 && categoryCount <= 5 && !hasTimeDimension) {
    return { chartType: 'bar', confidence: 0.6, reasoning: 'Categorical comparison detected' }
  }

  // Default to table for complex or ambiguous queries
  return { chartType: 'table', confidence: 0.5, reasoning: 'No clear chart type pattern matched; defaulting to table' }
}
