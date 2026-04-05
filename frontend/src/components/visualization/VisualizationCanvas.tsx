'use client'

/**
 * Visualization Canvas
 * Implements FR-5.1 through FR-5.9: Main Canvas
 *
 * Orchestrates chart selection, display modes, and data visualization.
 */

import { useState, useCallback, useMemo, useEffect } from 'react'
import type { QueryResponse } from '@/lib/query-response'
import type { ChartType } from '@/lib/chart-selection'
import { selectChartType } from '@/lib/chart-selection'
import { getResultSetConfig } from '@/lib/result-set-handler'
import { useVisualizationHistory } from '@/hooks/use-visualization-history'
import { ChartToolbar } from './ChartToolbar'
import { ViewModeToggle, type ViewMode } from './ViewModeToggle'
import { ChartComponent } from './ChartComponent'
import { KPICard, type KPIData } from './KPICard'
import { EmptyChart } from './EmptyChart'
import * as echarts from 'echarts'

interface VisualizationCanvasProps {
  data: QueryResponse
  selectedChartType?: ChartType
  defaultViewMode?: ViewMode
  className?: string
}

/**
 * Extract column names from query response data
 */
function extractColumns(data: QueryResponse): string[] {
  if (!data.data || data.data.length === 0) return []
  const firstRow = data.data[0]
  return Object.keys(firstRow)
}

/**
 * Determine if the result is suitable for KPI display
 */
function isKPISuitable(data: QueryResponse): boolean {
  return (
    data.metadata.row_count === 1 &&
    data.data.length === 1 &&
    !data.metadata.metric_name?.toLowerCase().includes('trend') &&
    !data.metadata.metric_name?.toLowerCase().includes('over time')
  )
}

/**
 * Extract KPI data from query response
 */
function extractKPIData(data: QueryResponse): KPIData | null {
  if (!isKPISuitable(data)) return null

  const row = data.data[0]
  const columns = Object.keys(row)
  const valueColumn = columns.find((col) => typeof row[col] === 'number')
  const value = valueColumn ? (row[valueColumn] as number) : 0

  return {
    metricName: data.metadata.metric_name ?? valueColumn ?? 'Value',
    value,
    unit: data.metadata.unit,
    // These would need to be calculated from historical data in a real implementation
    priorPeriodValue: undefined,
    categoryAverageValue: undefined,
    yoyChange: undefined,
    momChange: undefined,
  }
}

/**
 * Transform QueryResponse to chart-friendly format
 */
function transformDataForChart(data: QueryResponse): {
  columns: string[]
  rows: Array<Record<string, unknown>>
} {
  const columns = extractColumns(data)
  return {
    columns,
    rows: data.data,
  }
}

export function VisualizationCanvas({
  data,
  selectedChartType: initialChartType,
  defaultViewMode = 'chart',
  className,
}: VisualizationCanvasProps) {
  const [selectedChartType, setSelectedChartType] = useState<ChartType>(
    initialChartType ?? ('auto' as ChartType)
  )
  const [viewMode, setViewMode] = useState<ViewMode>(defaultViewMode)
  const [autoChartType, setAutoChartType] = useState<ChartType>('table')
  const [selectionReasoning, setSelectionReasoning] = useState<string>('')
  const [chartInstance, setChartInstance] = useState<echarts.ECharts | null>(null)

  const { addToHistory } = useVisualizationHistory()

  // Determine result set config based on row count
  const resultSetConfig = useMemo(
    () => getResultSetConfig(data.metadata.row_count),
    [data.metadata.row_count]
  )

  // Auto-select chart type based on query and result shape
  useEffect(() => {
    if (!data.data || data.data.length === 0) return

    const columns = extractColumns(data)
    const numericColumns = columns.filter((col) => {
      const firstValue = data.data[0]?.[col]
      return typeof firstValue === 'number'
    })

    // Determine result shape
    const resultShape = {
      rowCount: data.data.length,
      hasTimeDimension: columns.some(
        (col) =>
          col.toLowerCase().includes('date') ||
          col.toLowerCase().includes('month') ||
          col.toLowerCase().includes('quarter') ||
          col.toLowerCase().includes('year') ||
          col.toLowerCase().includes('time')
      ),
      categoryCount: columns.length - numericColumns.length,
      valueCount: numericColumns.length,
    }

    // Query text would come from conversation context in real implementation
    // Using placeholder for now
    const queryText = data.metadata.metric_name ?? 'Show data'

    const result = selectChartType({
      queryText,
      resultShape,
    })

    setAutoChartType(result.chartType)
    setSelectionReasoning(result.reasoning ?? '')

    // Only update selectedChartType if it's set to auto
    if (!initialChartType) {
      setSelectedChartType(result.chartType)
    }
  }, [data, initialChartType])

  // Handle chart type change (manual override)
  const handleChartTypeChange = useCallback((type: ChartType) => {
    setSelectedChartType(type)
  }, [])

  // Handle zoom reset
  const handleZoomReset = useCallback(() => {
    // Zoom is reset via ChartComponent internal state
  }, [])

  // Handle drill-down
  const handleDrillDown = useCallback(
    (params: unknown) => {
      // In a real implementation, this would trigger a new query
      // with filtered parameters based on the clicked element
      console.log('Drill-down params:', params)
    },
    []
  )

  // Handle chart ready
  const handleChartReady = useCallback((instance: echarts.ECharts) => {
    setChartInstance(instance)
  }, [])

  // Add to history when visualization changes
  useEffect(() => {
    if (data && chartInstance) {
      addToHistory(
        data.metadata.metric_name ?? 'Query',
        selectedChartType,
        chartInstance
      )
    }
  }, [data, selectedChartType, chartInstance, addToHistory])

  // Check if data is empty
  const isEmpty = !data.data || data.data.length === 0

  // Check if zoom is enabled (for time series with 8+ data points)
  const enableZoom =
    autoChartType === 'line' &&
    data.metadata.row_count >= 8

  // Determine period type for KPI card
  const periodType = useMemo(() => {
    const aggregation = data.metadata.aggregation_level?.toLowerCase() ?? ''
    if (aggregation.includes('quarter')) return 'quarter'
    if (aggregation.includes('month')) return 'month'
    if (aggregation.includes('year')) return 'year'
    return 'quarter' // Default
  }, [data.metadata.aggregation_level])

  // KPI data extraction
  const kpiData = useMemo(() => extractKPIData(data), [data])

  // Chart data transformation
  const chartData = useMemo(
    () => transformDataForChart(data),
    [data]
  )

  // Handle view as table for KPI card
  const handleViewAsTable = useCallback(() => {
    setViewMode('table')
  }, [])

  // If empty, show empty state
  if (isEmpty) {
    return (
      <div className={className}>
        <EmptyChart />
      </div>
    )
  }

  // If KPI and chart mode is chart-only or both, show KPI card
  const showKPI = kpiData && (viewMode === 'chart' || viewMode === 'both')

  // If table-only or both, need to render table
  const showTable = viewMode === 'table' || viewMode === 'both'

  // Table pagination
  const pageSize = resultSetConfig.pageSize ?? 50
  const [currentPage, setCurrentPage] = useState(0)

  const totalPages = Math.ceil(data.data.length / pageSize)
  const paginatedRows = showTable
    ? data.data.slice(currentPage * pageSize, (currentPage + 1) * pageSize)
    : []

  return (
    <div className={`space-y-4 ${className ?? ''}`}>
      {/* Toolbar row */}
      <div className="flex items-center justify-between gap-4">
        <ViewModeToggle viewMode={viewMode} onViewModeChange={setViewMode} />
        <ChartToolbar
          autoChartType={autoChartType}
          selectedChartType={selectedChartType}
          onChartTypeChange={handleChartTypeChange}
          showReasoning={selectedChartType !== autoChartType}
          reasoning={selectionReasoning}
          onZoomReset={handleZoomReset}
          isZoomActive={enableZoom}
        />
      </div>

      {/* Content area */}
      <div className="space-y-4">
        {/* KPI Card */}
        {showKPI && (
          <KPICard
            data={kpiData}
            periodType={periodType}
            onViewAsTable={handleViewAsTable}
          />
        )}

        {/* Chart */}
        {(viewMode === 'chart' || viewMode === 'both') && !showKPI && (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <ChartComponent
              data={chartData}
              chartType={selectedChartType === 'auto' ? autoChartType : selectedChartType}
              enableZoom={enableZoom}
              onZoomReset={handleZoomReset}
              onDrillDown={handleDrillDown}
              onChartReady={handleChartReady}
            />
          </div>
        )}

        {/* Table */}
        {showTable && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    {extractColumns(data).map((col) => (
                      <th
                        key={col}
                        className="text-left px-4 py-2.5 text-xs font-medium uppercase tracking-wide text-slate-400"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {paginatedRows.map((row, i) => (
                    <tr
                      key={i}
                      className="hover:bg-slate-50 transition-colors"
                    >
                      {extractColumns(data).map((col) => (
                        <td
                          key={col}
                          className="px-4 py-2.5 font-medium text-slate-900"
                        >
                          {typeof row[col] === 'number'
                            ? (row[col] as number).toLocaleString()
                            : String(row[col] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
                <p className="text-xs text-slate-500">
                  Showing {currentPage * pageSize + 1} to{' '}
                  {Math.min((currentPage + 1) * pageSize, data.data.length)} of{' '}
                  {data.data.length} rows
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                    disabled={currentPage === 0}
                    className="px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-xs text-slate-500">
                    Page {currentPage + 1} of {totalPages}
                  </span>
                  <button
                    onClick={() =>
                      setCurrentPage((p) => Math.min(totalPages - 1, p + 1))
                    }
                    disabled={currentPage >= totalPages - 1}
                    className="px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
