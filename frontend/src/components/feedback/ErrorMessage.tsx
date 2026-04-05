"use client"

import { cn } from "@/lib/utils"
import { AlertCircle, RefreshCw, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useEffect, useState } from "react"

interface ErrorMessageProps {
  message: string
  className?: string
  // Suggestion
  suggestion?: string
  // Retry
  onRetry?: () => void
  // Rate limit
  isRateLimit?: boolean
  retryAfter?: number
  // Session timeout
  isSessionTimeout?: boolean
}

export function ErrorMessage({
  message,
  className,
  suggestion,
  onRetry,
  isRateLimit = false,
  retryAfter = 0,
  isSessionTimeout = false,
}: ErrorMessageProps) {
  const [countdown, setCountdown] = useState(retryAfter)

  // Countdown timer for rate limits
  useEffect(() => {
    if (!isRateLimit || countdown <= 0) return

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [isRateLimit, countdown])

  // Session timeout banner
  if (isSessionTimeout) {
    return (
      <div
        data-testid="error-banner"
        className={cn(
          "flex items-center gap-3 px-4 py-3 rounded-lg",
          "bg-amber-50 border border-amber-200",
          "text-sm text-slate-700",
          className
        )}
      >
        <Clock className="size-4 text-amber-600 shrink-0" />
        <div className="flex-1">
          <p className="font-medium text-amber-800">{message}</p>
          <p className="text-xs text-amber-600 mt-0.5">
            Conversation preserved for 30 min
          </p>
        </div>
      </div>
    )
  }

  // Rate limit with countdown
  if (isRateLimit) {
    return (
      <div
        data-testid="error-message"
        className={cn(
          "flex flex-col gap-3 px-4 py-3 rounded-lg",
          "bg-red-50 border border-red-200",
          className
        )}
      >
        <div className="flex items-start gap-3">
          <AlertCircle className="size-4 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-red-800">{message}</p>
            <p data-testid="rate-limit-countdown" className="text-xs text-red-600 mt-1">
              Retry in {countdown} seconds
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Standard error message
  return (
    <div
      data-testid="error-message"
      className={cn(
        "flex flex-col gap-3 px-4 py-3 rounded-lg",
        "bg-red-50 border border-red-200",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <AlertCircle
          data-testid="error-icon"
          className="size-4 text-red-600 shrink-0 mt-0.5"
        />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-red-800">{message}</p>
          {suggestion && (
            <p className="text-xs text-red-600 mt-1">{suggestion}</p>
          )}
        </div>
        {onRetry && (
          <Button
            data-testid="retry-button"
            variant="ghost"
            size="sm"
            onClick={onRetry}
            className="shrink-0 h-7 px-2 text-xs"
          >
            <RefreshCw className="size-3 mr-1" />
            Retry
          </Button>
        )}
      </div>
    </div>
  )
}
