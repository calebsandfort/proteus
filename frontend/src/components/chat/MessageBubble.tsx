"use client"

import { cn } from "@/lib/utils"
import { ChevronDown, ChevronRight, FileJson, Eye } from "lucide-react"
import { useState } from "react"

interface MessageBubbleProps {
  role: "user" | "assistant"
  content: string
  className?: string
  // Observability
  observabilityLevel?: 0 | 1 | 2 | 3
  isObservabilityEnabled?: boolean
  metadata?: {
    toolSelected?: string
    extractedDimensions?: Record<string, string | number>
    latencyMs?: number
    [key: string]: unknown
  }
  rawData?: {
    request?: unknown
    response?: unknown
  }
}

function JsonViewer({
  data,
  maxLines = 20,
}: {
  data: unknown
  maxLines?: number
}) {
  const [showAll, setShowAll] = useState(false)
  const jsonString = JSON.stringify(data, null, 2)
  const lines = jsonString.split("\n")

  const isLong = lines.length > maxLines
  const displayLines = showAll ? lines : lines.slice(0, maxLines)
  const displayText = displayLines.join("\n")

  return (
    <div data-testid="json-viewer" className="font-mono text-xs text-slate-600 bg-slate-50 rounded-lg p-3">
      <pre className="whitespace-pre-wrap break-words">{displayText}</pre>
      {isLong && !showAll && (
        <button
          data-testid="show-more-button"
          onClick={() => setShowAll(true)}
          className="text-blue-600 hover:text-blue-700 text-xs mt-2"
        >
          Show more
        </button>
      )}
    </div>
  )
}

export function MessageBubble({
  role,
  content,
  className,
  observabilityLevel = 0,
  isObservabilityEnabled = false,
  metadata,
  rawData,
}: MessageBubbleProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showRaw, setShowRaw] = useState(false)

  const showExpandIcon = isObservabilityEnabled && role === "assistant" && observabilityLevel >= 1
  const showJsonViewer = isObservabilityEnabled && observabilityLevel >= 2 && metadata
  const showRawButton = isObservabilityEnabled && observabilityLevel >= 3 && rawData

  return (
    <div data-testid="message-bubble-container" className={cn("flex", role === "user" ? "justify-end" : "justify-start")}>
      <div
        data-testid="message-bubble"
        className={cn(
          "relative px-4 py-2.5 max-w-[80%] text-sm leading-relaxed",
          role === "user" && [
            "bg-blue-600 text-white rounded-2xl rounded-br-md",
          ],
          role === "assistant" && [
            "bg-white rounded-2xl rounded-bl-md border border-slate-200 shadow-sm",
          ],
          className
        )}
      >
        <p className={cn(role === "user" ? "text-white" : "text-slate-900")}>{content}</p>

        {/* Expand icon for observability */}
        {showExpandIcon && (
          <button
            data-testid="expand-icon"
            onClick={() => setIsExpanded(!isExpanded)}
            className={cn(
              "absolute top-2 right-2 p-1 rounded hover:bg-slate-100 transition-colors",
              role === "user" && "hover:bg-blue-500"
            )}
            aria-label={isExpanded ? "Collapse details" : "Expand details"}
          >
            {isExpanded ? (
              <ChevronDown className="size-4 text-slate-400" />
            ) : (
              <ChevronRight className="size-4 text-slate-400" />
            )}
          </button>
        )}

        {/* Expanded metadata (Level 1) */}
        {isExpanded && observabilityLevel >= 1 && metadata && (
          <div data-testid="message-metadata" className="mt-3 pt-3 border-t border-slate-100 space-y-1.5 text-xs">
            {metadata.toolSelected && (
              <p className="text-slate-500">
                Tool selected: <span className="text-slate-900 font-medium">{metadata.toolSelected}</span>
              </p>
            )}
            {metadata.extractedDimensions && (
              <p className="text-slate-500">
                Dimensions:{" "}
                <span className="text-slate-900 font-medium">
                  {Object.entries(metadata.extractedDimensions)
                    .map(([k, v]) => `${k}=${v}`)
                    .join(", ")}
                </span>
              </p>
            )}
            {metadata.latencyMs && (
              <p className="text-slate-500">
                Latency: <span className="text-slate-900 font-medium">{metadata.latencyMs}ms</span>
              </p>
            )}
          </div>
        )}

        {/* JSON Viewer (Level 2) */}
        {showJsonViewer && isExpanded && (
          <div className="mt-3">
            <JsonViewer data={metadata} />
          </div>
        )}

        {/* Raw data button (Level 3) */}
        {showRawButton && isExpanded && (
          <div className="mt-3 space-y-2">
            {!showRaw ? (
              <button
                data-testid="show-raw-button"
                onClick={() => setShowRaw(true)}
                className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700"
              >
                <Eye className="size-3" />
                Show raw
              </button>
            ) : (
              <div className="space-y-2">
                <JsonViewer data={{ request: rawData.request }} />
                <JsonViewer data={{ response: rawData.response }} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
