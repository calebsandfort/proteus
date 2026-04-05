"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { ChevronDown, Check } from "lucide-react"

// Model Option Interface (FR-1.5)
export interface ModelOption {
  id: string
  provider: "openai" | "google" | "anthropic" | "kimi" | "minimax" | "glm"
  displayName: string
  logoUrl?: string
  supportsFunctionCalling: boolean
}

// Response Generation Models (FR-1.5, FR-8.3)
export const RESPONSE_GENERATION_MODELS: ModelOption[] = [
  {
    id: "openai/gpt-4o",
    provider: "openai",
    displayName: "GPT-4o",
    supportsFunctionCalling: true,
  },
  {
    id: "google/gemini-2.0-flash",
    provider: "google",
    displayName: "Gemini 2.0 Flash",
    supportsFunctionCalling: true,
  },
  {
    id: "anthropic/claude-3.5-sonnet",
    provider: "anthropic",
    displayName: "Claude 3.5 Sonnet",
    supportsFunctionCalling: true,
  },
  {
    id: "moonshot/kimi-k2",
    provider: "kimi",
    displayName: "Kimi K2",
    supportsFunctionCalling: true,
  },
  {
    id: "minimax/text-01",
    provider: "minimax",
    displayName: "MiniMax Text-01",
    supportsFunctionCalling: true,
  },
  {
    id: "google/gemini-2.5-pro",
    provider: "glm",
    displayName: "GLM-4-Pro",
    supportsFunctionCalling: true,
  },
]

// Provider logo components
function ProviderLogo({ provider }: { provider: ModelOption["provider"] }) {
  const logos: Record<ModelOption["provider"], JSX.Element> = {
    openai: (
      <svg viewBox="0 0 24 24" className="size-4" fill="currentColor">
        <path d="M22.282 9.821a5.985 5.985 0 0 0-.515-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .511 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494z" />
      </svg>
    ),
    google: (
      <svg viewBox="0 0 24 24" className="size-4" fill="none">
        <path
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          fill="#4285F4"
        />
        <path
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          fill="#34A853"
        />
        <path
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          fill="#FBBC05"
        />
        <path
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          fill="#EA4335"
        />
      </svg>
    ),
    anthropic: (
      <svg viewBox="0 0 24 24" className="size-4" fill="currentColor">
        <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8zm-2-8a2 2 0 1 1 4 0 2 2 0 0 1-4 0z" />
      </svg>
    ),
    kimi: (
      <svg viewBox="0 0 24 24" className="size-4" fill="currentColor">
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M8 12h8M12 8v8" stroke="currentColor" strokeWidth="2" />
      </svg>
    ),
    minimax: (
      <svg viewBox="0 0 24 24" className="size-4" fill="currentColor">
        <path d="M12 2l2.4 7.2h7.6l-6 4.8 2.4 7.2-6-4.8-6 4.8 2.4-7.2-6-4.8h7.6z" />
      </svg>
    ),
    glm: (
      <svg viewBox="0 0 24 24" className="size-4" fill="currentColor">
        <rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
    ),
  }
  return logos[provider]
}

interface ModelSelectorProps {
  selectedModelId: string
  onModelChange: (modelId: string) => void
  className?: string
}

export function ModelSelector({
  selectedModelId,
  onModelChange,
  className,
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const selectedModel = RESPONSE_GENERATION_MODELS.find(
    (model) => model.id === selectedModelId
  )

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <div
      data-testid="model-selector"
      className={cn("relative", className)}
      ref={dropdownRef}
    >
      <button
        data-testid="model-selector-button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors",
          "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
          isOpen && "bg-slate-100"
        )}
      >
        <span className="font-medium">{selectedModel?.displayName || "Select model"}</span>
        <ChevronDown
          className={cn("size-3 transition-transform", isOpen && "rotate-180")}
        />
      </button>

      {isOpen && (
        <div
          data-testid="model-dropdown"
          className="absolute right-0 top-full mt-1 w-56 bg-white rounded-lg border border-slate-200 shadow-lg z-50"
        >
          <div className="py-1">
            {RESPONSE_GENERATION_MODELS.map((model) => (
              <button
                key={model.id}
                data-testid={`model-option-${model.id}`}
                onClick={() => {
                  onModelChange(model.id)
                  setIsOpen(false)
                }}
                className={cn(
                  "w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-slate-50 transition-colors",
                  model.id === selectedModelId && "bg-blue-50 text-blue-700"
                )}
              >
                <span data-testid="model-provider" className="flex-shrink-0">
                  <ProviderLogo provider={model.provider} />
                </span>
                <span className="flex-1 font-medium">{model.displayName}</span>
                {model.id === selectedModelId && (
                  <Check className="size-3 text-blue-600" />
                )}
                {model.supportsFunctionCalling && (
                  <span className="text-[10px] text-slate-400" title="Supports Function Calling">
                    FC
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}