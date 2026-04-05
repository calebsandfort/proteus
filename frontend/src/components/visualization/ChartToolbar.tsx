'use client'

/**
 * Chart Toolbar Component
 * Implements FR-5.2: Manual Override
 *
 * Floating toolbar with chart type override dropdown.
 */

import { Sparkles, Table, TrendingUp, BarChart3, Circle, ScatterChart, RotateCcw } from 'lucide-react'
import type { ChartType } from '@/lib/chart-selection'

interface ChartToolbarProps {
  autoChartType: ChartType
  selectedChartType: ChartType
  onChartTypeChange: (type: ChartType) => void
  showReasoning?: boolean
  reasoning?: string
  onZoomReset?: () => void
  isZoomActive?: boolean
  className?: string
}

type ChartTypeOption = {
  value: ChartType
  label: string
  icon: typeof Sparkles
  description?: string
}

const CHART_TYPE_OPTIONS: ChartTypeOption[] = [
  { value: 'table', label: 'Auto', icon: Sparkles, description: 'Let the system choose' },
  { value: 'table', label: 'Table', icon: Table, description: 'Tabular data view' },
  { value: 'line', label: 'Line', icon: TrendingUp, description: 'Trend over time' },
  { value: 'bar', label: 'Bar (Vertical)', icon: BarChart3, description: 'Vertical bars' },
  { value: 'horizontal_bar', label: 'Bar (Horizontal)', icon: BarChart3, description: 'Horizontal bars' },
  { value: 'pie', label: 'Pie', icon: Circle, description: 'Proportion breakdown' },
  { value: 'donut', label: 'Donut', icon: Circle, description: 'Donut chart' },
  { value: 'scatter', label: 'Scatter', icon: ScatterChart, description: 'Correlation plot' },
]

export function ChartToolbar({
  autoChartType,
  selectedChartType,
  onChartTypeChange,
  showReasoning = false,
  reasoning,
  onZoomReset,
  isZoomActive = false,
  className,
}: ChartToolbarProps) {
  const isAuto = selectedChartType === 'auto' || selectedChartType === autoChartType
  const currentOption = CHART_TYPE_OPTIONS.find((opt) => opt.value === selectedChartType)

  return (
    <div
      className={`flex items-center gap-3 p-2 bg-white rounded-lg border border-slate-200 shadow-sm ${className ?? ''}`}
    >
      {/* Chart type dropdown */}
      <div className="relative group">
        <select
          value={selectedChartType}
          onChange={(e) => onChartTypeChange(e.target.value as ChartType)}
          className="appearance-none bg-slate-50 border border-slate-200 rounded-md px-3 py-1.5 pr-8 text-sm font-medium text-slate-700 cursor-pointer hover:bg-slate-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
        >
          {CHART_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {/* Custom dropdown arrow */}
        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
          <svg
            className="h-4 w-4 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>

        {/* Tooltip with reasoning when override differs */}
        {showReasoning && !isAuto && reasoning && (
          <div className="absolute right-0 top-full mt-2 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
            <p className="font-medium mb-1">Auto-selection reasoning:</p>
            <p className="text-slate-300">{reasoning}</p>
            <div className="absolute -top-1 right-4 w-2 h-2 bg-slate-900 rotate-45" />
          </div>
        )}
      </div>

      {/* Zoom reset button (only show when zoom is active) */}
      {isZoomActive && onZoomReset && (
        <button
          onClick={onZoomReset}
          className="flex items-center gap-1.5 px-2 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Reset Zoom
        </button>
      )}

      {/* Current chart type indicator */}
      {currentOption && (
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <currentOption.icon className="h-4 w-4" />
          <span>{currentOption.label}</span>
        </div>
      )}
    </div>
  )
}
