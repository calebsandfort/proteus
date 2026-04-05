"use client"

import { cn } from "@/lib/utils"
import { useState } from "react"

interface EmptyStateProps {
  className?: string
  sampleQueries?: string[]
  onSampleQueryClick?: (query: string) => void
}

const DEFAULT_SAMPLE_QUERIES = [
  "What was Chipotle's market share in Texas last quarter?",
  "Show me consumer spending trends for restaurants",
  "Compare QSR performance across major brands",
]

export function EmptyState({
  className,
  sampleQueries = DEFAULT_SAMPLE_QUERIES,
  onSampleQueryClick,
}: EmptyStateProps) {
  const [hoveredQuery, setHoveredQuery] = useState<string | null>(null)

  return (
    <div
      data-testid="empty-state-container"
      className={cn(
        "flex flex-col items-center justify-center h-full",
        "p-8 text-center",
        className
      )}
    >
      {/* Animated placeholder visualization */}
      <div
        data-testid="empty-state-animation"
        className="mb-8 relative w-48 h-32"
      >
        {/* Subtle animated bars representing chart placeholder */}
        <div className="absolute inset-0 flex items-end justify-center gap-2">
          {[40, 60, 45, 80, 55, 70, 50, 65, 45, 75].map((height, i) => (
            <div
              key={i}
              className={cn(
                "w-4 bg-slate-200 rounded-t transition-all duration-500",
                "animate-pulse"
              )}
              style={{
                height: `${height}%`,
                animationDelay: `${i * 100}ms`,
              }}
            />
          ))}
        </div>
        {/* Subtle glow effect */}
        <div className="absolute -inset-4 bg-gradient-radial from-blue-100/30 to-transparent rounded-full blur-xl" />
      </div>

      {/* Sample query prompts */}
      <div className="space-y-2 max-w-md">
        <p className="text-sm text-slate-500 mb-4">
          Try one of these sample queries:
        </p>
        {sampleQueries.map((query, index) => (
          <button
            key={index}
            data-testid="sample-prompt"
            onClick={() => onSampleQueryClick?.(query)}
            onMouseEnter={() => setHoveredQuery(query)}
            onMouseLeave={() => setHoveredQuery(null)}
            className={cn(
              "block w-full text-left px-4 py-3 rounded-lg text-sm",
              "text-slate-400 bg-slate-50 border border-slate-200",
              "hover:text-slate-600 hover:bg-slate-100 transition-colors",
              "cursor-pointer"
            )}
          >
            {query}
          </button>
        ))}
      </div>

      {/* Input placeholder hint */}
      <p data-testid="empty-state-input" className="mt-6 text-xs text-slate-400">
        Or type your own query above to get started
      </p>
    </div>
  )
}
