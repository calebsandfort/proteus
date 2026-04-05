'use client'

/**
 * Chart Component
 * Implements FR-5.5, FR-5.6, FR-5.9: Chart Interactivity
 *
 * ECharts wrapper with resize observer, zoom, legend toggle,
 * click-to-highlight, export (PNG/CSV), and drill-down support.
 */

import { useEffect, useRef, useCallback, useState } from 'react'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import type { ChartType } from '@/lib/chart-selection'
import {
  configureLineChart,
  configureBarChart,
  configurePieChart,
  configureDonutChart,
  configureScatterChart,
  configureHorizontalBarChart,
  configureStackedBarChart,
  configureStackedAreaChart,
  configureWaterfallChart,
  configureBumpChart,
  CHART_COLORS,
} from '@/lib/echarts-config'
import { Download, RotateCcw } from 'lucide-react'

interface ChartComponentProps {
  data: {
    columns: string[]
    rows: Array<Record<string, unknown>>
  }
  chartType: ChartType
  enableZoom?: boolean
  onZoomReset?: () => void
  onDrillDown?: (params: unknown) => void
  onChartReady?: (instance: echarts.ECharts) => void
  className?: string
}

type ChartData = {
  xAxis?: string[]
  yAxis?: string[]
  series: Array<{ name: string; data: number[] | Array<[number, number]> | Array<{ value: number; rank: number }> }>
}

/**
 * Parse raw data into chart-ready format
 */
function parseChartData(
  data: { columns: string[]; rows: Array<Record<string, unknown>> },
  chartType: ChartType
): ChartData {
  const { columns, rows } = data

  if (rows.length === 0) {
    return { series: [] }
  }

  // Find categorical column (usually first non-numeric or labeled column)
  const numericColumns = columns.filter((col) => {
    const firstValue = rows[0]?.[col]
    return typeof firstValue === 'number'
  })

  const categoryColumn = columns.find((col) => !numericColumns.includes(col)) ?? columns[0]

  // Determine x-axis based on chart type
  if (chartType === 'horizontal_bar' || chartType === 'scatter') {
    const yAxis = rows.map((row) => String(row[categoryColumn] ?? ''))
    const series = numericColumns.map((col) => ({
      name: col,
      data: rows.map((row) => {
        const value = row[col]
        if (chartType === 'scatter') {
          // For scatter, return [x, y] pairs
          const index = numericColumns.indexOf(col)
          if (index === 0) return [value as number, 0] // Placeholder
          return [0, value as number] // Placeholder
        }
        return value as number
      }) as number[],
    }))

    // For scatter, pair up numeric columns
    if (chartType === 'scatter' && numericColumns.length >= 2) {
      const scatterSeries = [
        {
          name: `${numericColumns[0]} vs ${numericColumns[1]}`,
          data: rows.map((row) => [row[numericColumns[0]] as number, row[numericColumns[1]] as number]),
        },
      ]
      return { yAxis, series: scatterSeries }
    }

    return { yAxis, series }
  }

  // For most chart types, use category column as x-axis
  const xAxis = rows.map((row) => String(row[categoryColumn] ?? ''))

  // Create series for each numeric column
  const series = numericColumns.map((col) => ({
    name: col,
    data: rows.map((row) => row[col] as number),
  }))

  return { xAxis, series }
}

/**
 * Get chart configuration based on chart type
 */
function getChartConfig(
  chartData: ChartData,
  chartType: ChartType,
  enableZoom: boolean
): EChartsOption {
  switch (chartType) {
    case 'line':
      return configureLineChart(chartData as { xAxis: string[]; series: Array<{ name: string; data: number[] }> }, enableZoom)
    case 'bar':
      return configureBarChart(chartData as { xAxis: string[]; series: Array<{ name: string; data: number[] }> })
    case 'horizontal_bar':
      return configureHorizontalBarChart(chartData as { yAxis: string[]; series: Array<{ name: string; data: number[] }> })
    case 'pie':
      return configurePieChart(
        chartData.series[0]?.data.map((value, i) => ({
          name: chartData.xAxis?.[i] ?? `Item ${i}`,
          value: value as number,
        })) ?? []
      )
    case 'donut':
      return configureDonutChart(
        chartData.series[0]?.data.map((value, i) => ({
          name: chartData.xAxis?.[i] ?? `Item ${i}`,
          value: value as number,
        })) ?? []
      )
    case 'scatter':
      return configureScatterChart(
        chartData.series as Array<{ name: string; data: Array<[number, number]> }>
      )
    case 'stacked_bar':
      return configureStackedBarChart(chartData as { xAxis: string[]; series: Array<{ name: string; data: number[] }> })
    case 'stacked_area':
      return configureStackedAreaChart(chartData as { xAxis: string[]; series: Array<{ name: string; data: number[] }> }, enableZoom)
    case 'waterfall':
      return configureWaterfallChart(
        chartData.series[0]?.data.map((value, i) => ({
          name: chartData.xAxis?.[i] ?? `Item ${i}`,
          value: Math.abs(value as number),
          type: (value as number) >= 0 ? 'increase' : 'decrease',
        })) ?? []
      )
    case 'bump':
      return configureBumpChart(
        chartData as { xAxis: string[]; series: Array<{ name: string; data: Array<{ value: number; rank: number }> }> }
      )
    default:
      return configureBarChart(chartData as { xAxis: string[]; series: Array<{ name: string; data: number[] }> })
  }
}

export function ChartComponent({
  data,
  chartType,
  enableZoom = false,
  onZoomReset,
  onDrillDown,
  onChartReady,
  className,
}: ChartComponentProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartInstanceRef = useRef<echarts.ECharts | null>(null)
  const [isZoomActive, setIsZoomActive] = useState(false)
  const [showExportMenu, setShowExportMenu] = useState(false)

  // Initialize chart
  useEffect(() => {
    if (!containerRef.current) return

    // Initialize ECharts instance
    const chart = echarts.init(containerRef.current, undefined, {
      renderer: 'canvas',
    })
    chartInstanceRef.current = chart

    // Call onChartReady callback
    if (onChartReady) {
      onChartReady(chart)
    }

    // Cleanup on unmount
    return () => {
      chart.dispose()
      chartInstanceRef.current = null
    }
  }, [onChartReady])

  // Handle resize
  useEffect(() => {
    if (!chartInstanceRef.current || !containerRef.current) return

    const resizeObserver = new ResizeObserver(() => {
      chartInstanceRef.current?.resize()
    })

    resizeObserver.observe(containerRef.current)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  // Update chart when data or type changes
  useEffect(() => {
    if (!chartInstanceRef.current || !data || data.rows.length === 0) return

    const chartData = parseChartData(data, chartType)
    const options = getChartConfig(chartData, chartType, enableZoom)

    chartInstanceRef.current.setOption(options, true)

    // Set up event handlers
    chartInstanceRef.current.off('click')
    chartInstanceRef.current.on('click', (params) => {
      if (onDrillDown) {
        onDrillDown(params)
      }
    })

    // Handle datazoom events for zoom state
    if (enableZoom) {
      chartInstanceRef.current.off('datazoom')
      chartInstanceRef.current.on('datazoom', (params: unknown) => {
        setIsZoomActive(true)
      })
    }
  }, [data, chartType, enableZoom, onDrillDown])

  // Reset zoom
  const handleZoomReset = useCallback(() => {
    if (!chartInstanceRef.current) return
    chartInstanceRef.current.dispatchAction({
      type: 'dataZoom',
      start: 0,
      end: 100,
    })
    setIsZoomActive(false)
    if (onZoomReset) {
      onZoomReset()
    }
  }, [onZoomReset])

  // Export handlers
  const exportPNG = useCallback(() => {
    if (!chartInstanceRef.current) return
    const url = chartInstanceRef.current.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#ffffff',
    })
    const link = document.createElement('a')
    link.download = 'chart.png'
    link.href = url
    link.click()
    setShowExportMenu(false)
  }, [])

  const exportCSV = useCallback(() => {
    if (!data || data.rows.length === 0) return

    const headers = data.columns.join(',')
    const rows = data.rows.map((row) =>
      data.columns.map((col) => JSON.stringify(row[col] ?? '')).join(',')
    )
    const csv = [headers, ...rows].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.download = 'chart-data.csv'
    link.href = url
    link.click()
    URL.revokeObjectURL(url)
    setShowExportMenu(false)
  }, [data])

  return (
    <div className={`relative ${className ?? ''}`}>
      {/* Export and zoom controls */}
      <div className="absolute top-2 right-2 z-10 flex items-center gap-2">
        {/* Zoom reset button */}
        {enableZoom && isZoomActive && (
          <button
            onClick={handleZoomReset}
            className="flex items-center gap-1 px-2 py-1 bg-white border border-slate-200 rounded-md text-xs font-medium text-slate-600 hover:bg-slate-50 shadow-sm transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset Zoom
          </button>
        )}

        {/* Export dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="flex items-center gap-1 px-2 py-1 bg-white border border-slate-200 rounded-md text-xs font-medium text-slate-600 hover:bg-slate-50 shadow-sm transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            Export
          </button>

          {showExportMenu && (
            <div className="absolute right-0 top-full mt-1 w-32 bg-white border border-slate-200 rounded-md shadow-lg py-1 z-20">
              <button
                onClick={exportPNG}
                className="w-full px-3 py-1.5 text-xs text-left text-slate-700 hover:bg-slate-50"
              >
                Export PNG
              </button>
              <button
                onClick={exportCSV}
                className="w-full px-3 py-1.5 text-xs text-left text-slate-700 hover:bg-slate-50"
              >
                Export CSV
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Chart container */}
      <div ref={containerRef} className="h-64 w-full" />
    </div>
  )
}
