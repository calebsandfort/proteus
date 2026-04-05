"use client"

import { cn } from "@/lib/utils"
import { Check } from "lucide-react"

type StageName =
  | "Parsing query"
  | "Retrieving tools"
  | "Extracting dimensions"
  | "Querying data"
  | "Generating response"

const ALL_STAGES: StageName[] = [
  "Parsing query",
  "Retrieving tools",
  "Extracting dimensions",
  "Querying data",
  "Generating response",
]

interface StageIndicatorProps {
  stage: StageName
  completedStages?: StageName[]
  className?: string
}

export function StageIndicator({
  stage,
  completedStages = [],
  className,
}: StageIndicatorProps) {
  const currentIndex = ALL_STAGES.indexOf(stage)
  const isCompleted = (s: StageName) => completedStages.includes(s)

  return (
    <div
      data-testid="stage-indicator"
      className={cn("flex flex-col gap-2", className)}
    >
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-400">
        <span>Pipeline</span>
      </div>

      <div className="space-y-1.5">
        {ALL_STAGES.map((s, index) => {
          const completed = isCompleted(s)
          const active = s === stage

          return (
            <div
              key={s}
              data-testid={completed ? "stage-completed" : active ? "stage-active" : "stage-pending"}
              className={cn(
                "flex items-center gap-2 text-sm",
                completed && "text-slate-400",
                active && "text-blue-600",
                !completed && !active && "text-slate-400"
              )}
            >
              {/* Stage indicator */}
              <div
                className={cn(
                  "w-5 h-5 rounded-full flex items-center justify-center shrink-0",
                  completed && "bg-emerald-100 text-emerald-600",
                  active && "bg-blue-100 text-blue-600",
                  !completed && !active && "bg-slate-100 text-slate-400"
                )}
              >
                {completed ? (
                  <Check className="size-3" />
                ) : active ? (
                  <div className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
                ) : (
                  <div className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                )}
              </div>

              {/* Stage name */}
              <span className={cn(active && "font-medium")}>{s}</span>

              {/* Active indicator */}
              {active && (
                <span className="ml-auto text-xs text-blue-500 animate-pulse">
                  processing...
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
