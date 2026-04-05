'use client'

/**
 * View Mode Toggle Component
 * Implements FR-5.4: Table Toggle
 *
 * Toggle between Chart only, Table only, and Both (split view).
 */

'use client'

import { useEffect, useState } from 'react'
import { BarChart3, Table2, Columns2 } from 'lucide-react'

export type ViewMode = 'chart' | 'table' | 'both'

const STORAGE_KEY = 'proteus_view_mode'

interface ViewModeToggleProps {
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
  className?: string
}

type ViewModeOption = {
  value: ViewMode
  label: string
  icon: typeof BarChart3
}

const VIEW_MODE_OPTIONS: ViewModeOption[] = [
  { value: 'chart', label: 'Chart', icon: BarChart3 },
  { value: 'table', label: 'Table', icon: Table2 },
  { value: 'both', label: 'Both', icon: Columns2 },
]

export function ViewModeToggle({ viewMode, onViewModeChange, className }: ViewModeToggleProps) {
  const [mounted, setMounted] = useState(false)

  // Load initial value from localStorage on mount
  useEffect(() => {
    setMounted(true)
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored && ['chart', 'table', 'both'].includes(stored)) {
        onViewModeChange(stored as ViewMode)
      }
    } catch {
      // Ignore localStorage errors
    }
  }, [onViewModeChange])

  // Persist to localStorage when viewMode changes
  const handleChange = (mode: ViewMode) => {
    try {
      localStorage.setItem(STORAGE_KEY, mode)
    } catch {
      // Ignore localStorage errors
    }
    onViewModeChange(mode)
  }

  // Avoid hydration mismatch by not rendering until mounted
  if (!mounted) {
    return (
      <div
        className={`inline-flex items-center bg-slate-100 rounded-lg p-1 ${className ?? ''}`}
      >
        {VIEW_MODE_OPTIONS.map((option) => (
          <button
            key={option.value}
            disabled
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md text-slate-400"
          >
            <option.icon className="h-4 w-4" />
            {option.label}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div
      className={`inline-flex items-center bg-slate-100 rounded-lg p-1 ${className ?? ''}`}
    >
      {VIEW_MODE_OPTIONS.map((option) => {
        const isActive = viewMode === option.value
        return (
          <button
            key={option.value}
            onClick={() => handleChange(option.value)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              isActive
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <option.icon className="h-4 w-4" />
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
