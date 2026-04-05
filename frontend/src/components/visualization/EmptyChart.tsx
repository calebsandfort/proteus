'use client'

/**
 * Empty Chart Component
 * Implements FR-5.9: Chart Interaction Details - Empty data state
 *
 * Shows centered empty state message when no data matches the query.
 */

import { BarChart3 } from 'lucide-react'

interface EmptyChartProps {
  className?: string
}

export function EmptyChart({ className }: EmptyChartProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center h-64 w-full bg-slate-50 rounded-lg border border-slate-200 ${className ?? ''}`}
    >
      <BarChart3 className="h-12 w-12 text-slate-300 mb-3" />
      <p className="text-sm font-medium text-slate-500">No data matches your query</p>
      <p className="text-xs text-slate-400 mt-1">Try adjusting your filters or time period</p>
    </div>
  )
}
