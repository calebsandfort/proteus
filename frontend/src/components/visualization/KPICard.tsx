'use client'

/**
 * KPI Card Component
 * Implements FR-5.3: KPI Card Display
 *
 * Displays single aggregate values with comparison metrics.
 */

import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export interface KPIData {
  metricName: string
  value: number
  unit?: string
  priorPeriodValue?: number
  categoryAverageValue?: number
  yoyChange?: number // percentage
  momChange?: number // percentage
}

interface KPICardProps {
  data: KPIData
  periodType: 'quarter' | 'month' | 'year'
  onViewAsTable?: () => void
  className?: string
}

/**
 * Format a number with appropriate suffix (K, M, B)
 */
function formatValue(value: number, unit?: string): string {
  const absValue = Math.abs(value)

  let formatted: string
  if (absValue >= 1_000_000_000) {
    formatted = `${(value / 1_000_000_000).toFixed(1)}B`
  } else if (absValue >= 1_000_000) {
    formatted = `${(value / 1_000_000).toFixed(1)}M`
  } else if (absValue >= 1_000) {
    formatted = `${(value / 1_000).toFixed(1)}K`
  } else {
    formatted = value.toFixed(1)
  }

  return unit ? `${formatted} ${unit}` : formatted
}

/**
 * Format percentage change with sign
 */
function formatChange(change: number | undefined, isYoy: boolean): string {
  if (change === undefined) return ''
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(1)}% ${isYoy ? 'YoY' : 'MoM'}`
}

/**
 * Get the appropriate change indicator icon
 */
function ChangeIndicator({ change }: { change: number }) {
  if (change > 0) {
    return <TrendingUp className="h-3.5 w-3.5 text-emerald-600" />
  } else if (change < 0) {
    return <TrendingDown className="h-3.5 w-3.5 text-red-600" />
  }
  return <Minus className="h-3.5 w-3.5 text-slate-400" />
}

/**
 * Get the color class for change text
 */
function getChangeColorClass(change: number | undefined): string {
  if (change === undefined) return 'text-slate-500'
  if (change > 0) return 'text-emerald-600'
  if (change < 0) return 'text-red-600'
  return 'text-slate-500'
}

export function KPICard({ data, periodType, onViewAsTable, className }: KPICardProps) {
  const isYoy = periodType === 'quarter' || periodType === 'year'
  const change = isYoy ? data.yoyChange : data.momChange

  // Calculate comparison to prior period
  const priorPeriodComparison =
    data.priorPeriodValue !== undefined && data.value !== data.priorPeriodValue
      ? ((data.value - data.priorPeriodValue) / data.priorPeriodValue) * 100
      : undefined

  // Calculate comparison to category average
  const categoryComparison =
    data.categoryAverageValue !== undefined && data.value !== data.categoryAverageValue
      ? data.value - data.categoryAverageValue
      : undefined

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-1 ${className ?? ''}`}
    >
      {/* Metric name */}
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {data.metricName}
      </p>

      {/* Primary value */}
      <p className="text-2xl font-semibold tabular-nums text-slate-900">
        {formatValue(data.value, data.unit)}
      </p>

      {/* Prior period comparison */}
      {priorPeriodComparison !== undefined && (
        <div className="flex items-center gap-1.5">
          <ChangeIndicator change={priorPeriodComparison} />
          <p className={`text-xs font-medium ${getChangeColorClass(priorPeriodComparison)}`}>
            {priorPeriodComparison >= 0 ? '+' : ''}
            {priorPeriodComparison.toFixed(1)}% vs. prior {periodType}
          </p>
        </div>
      )}

      {/* Category average comparison */}
      {categoryComparison !== undefined && (
        <p className="text-xs text-slate-500">
          {categoryComparison >= 0 ? '+' : ''}
          {categoryComparison.toFixed(1)} vs. category average
        </p>
      )}

      {/* YoY/MoM change indicator */}
      {change !== undefined && (
        <div className="flex items-center gap-1.5 pt-1">
          <ChangeIndicator change={change} />
          <p className={`text-xs font-medium ${getChangeColorClass(change)}`}>
            {formatChange(change, isYoy)}
          </p>
        </div>
      )}

      {/* View as table link */}
      {onViewAsTable && (
        <button
          onClick={onViewAsTable}
          className="text-xs text-blue-600 hover:text-blue-700 mt-2 font-medium"
        >
          View as table
        </button>
      )}
    </div>
  )
}
