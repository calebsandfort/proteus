"use client"

import { cn } from "@/lib/utils"
import { HelpCircle, X } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface ClarificationOption {
  id: string
  label: string
  description?: string
}

interface ClarificationCardProps {
  originalQuery: string
  ambiguity: string
  options: ClarificationOption[]
  onSelect: (optionId: string) => void
  onDismiss: () => void
  className?: string
}

const MAX_OPTIONS = 3

export function ClarificationCard({
  originalQuery,
  ambiguity,
  options,
  onSelect,
  onDismiss,
  className,
}: ClarificationCardProps) {
  // Ensure max 3 options
  const displayOptions = options.slice(0, MAX_OPTIONS)

  return (
    <div
      data-testid="clarification-card"
      className={cn(
        "bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-3",
        "shadow-sm",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-2">
        <HelpCircle className="size-4 text-amber-600 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-900">{ambiguity}</p>
          <p className="text-xs text-slate-500 mt-1">
            Re: {originalQuery}
          </p>
        </div>
        <button
          data-testid="dismiss-button"
          onClick={onDismiss}
          className="p-1 rounded hover:bg-amber-100 transition-colors shrink-0"
          aria-label="Dismiss"
        >
          <X className="size-4 text-slate-400" />
        </button>
      </div>

      {/* Options */}
      <div className="space-y-2">
        {displayOptions.map((option) => (
          <button
            key={option.id}
            onClick={() => onSelect(option.id)}
            className={cn(
              "w-full text-left px-3 py-2 rounded-lg transition-colors",
              "bg-white border border-amber-200 hover:border-amber-300 hover:bg-amber-100",
              "text-sm text-slate-700"
            )}
          >
            <span className="font-medium">{option.label}</span>
            {option.description && (
              <span className="block text-xs text-slate-500 mt-0.5">
                {option.description}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
