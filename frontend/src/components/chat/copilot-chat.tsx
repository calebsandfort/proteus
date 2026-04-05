"use client"

import { ChatSidebar } from "./ChatSidebar"
import { ChatDrawer } from "./ChatDrawer"
import { useSidebar } from "@/hooks/use-sidebar"
import { useObservability } from "@/hooks/use-observability"
import { useConversation } from "@/hooks/use-conversation"
import { StageIndicator } from "@/components/feedback/StageIndicator"
import { ChartSkeleton } from "@/components/feedback/ChartSkeleton"
import { ErrorMessage } from "@/components/feedback/ErrorMessage"
import { EmptyState } from "@/components/chat/EmptyState"
import { MessageBubble } from "@/components/chat/MessageBubble"
import { ClarificationCard } from "@/components/chat/ClarificationCard"
import { cn } from "@/lib/utils"
import { Settings, ChevronDown } from "lucide-react"
import { useState } from "react"

// Model selector constants (FR-1.5)
export const RESPONSE_GENERATION_MODELS = [
  { id: "gpt-4o", name: "GPT-4o", description: "Most capable" },
  { id: "gpt-4o-mini", name: "GPT-4o Mini", description: "Fast & efficient" },
  { id: "claude-3-5-sonnet", name: "Claude 3.5 Sonnet", description: "Balanced" },
  { id: "claude-3-5-haiku", name: "Claude 3.5 Haiku", description: "Quick" },
  { id: "gemini-1-5-pro", name: "Gemini 1.5 Pro", description: "Long context" },
  { id: "gemini-1-5-flash", name: "Gemini 1.5 Flash", description: "Fast" },
] as const

interface CopilotChatProps {
  sidebarWidth?: number
  isSidebarCollapsed?: boolean
  className?: string
}

function ObservabilityToggle({
  isEnabled,
  onToggle,
}: {
  isEnabled: boolean
  onToggle: () => void
}) {
  return (
    <button
      data-testid="observability-toggle"
      onClick={onToggle}
      className={cn(
        "flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors",
        isEnabled
          ? "bg-blue-50 text-blue-700 border border-blue-200"
          : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"
      )}
    >
      <Settings className="size-3" />
      <span>Observability</span>
    </button>
  )
}

function ModelSelector({
  selectedModelId,
  onModelChange,
}: {
  selectedModelId: string
  onModelChange: (modelId: string) => void
}) {
  const [isOpen, setIsOpen] = useState(false)
  const selected = RESPONSE_GENERATION_MODELS.find((m) => m.id === selectedModelId)

  return (
    <div data-testid="model-selector" className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors",
          "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
        )}
      >
        <span className="font-medium">{selected?.name || "Select model"}</span>
        <ChevronDown className="size-3" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg border border-slate-200 shadow-lg z-50">
          {RESPONSE_GENERATION_MODELS.map((model) => (
            <button
              key={model.id}
              onClick={() => {
                onModelChange(model.id)
                setIsOpen(false)
              }}
              className={cn(
                "w-full text-left px-3 py-2 text-xs hover:bg-slate-50 transition-colors",
                model.id === selectedModelId && "bg-blue-50 text-blue-700"
              )}
            >
              <span className="font-medium block">{model.name}</span>
              <span className="text-slate-400">{model.description}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export function CopilotChat({
  sidebarWidth = 400,
  isSidebarCollapsed = false,
  className,
}: CopilotChatProps) {
  const { isMobile, isCollapsed } = useSidebar()
  const { isEnabled: isObservabilityEnabled, toggle: toggleObservability, level: observabilityLevel } = useObservability()
  const {
    isLoading,
    currentStage,
    pendingTools,
    error,
    loadingLevel,
    hasPendingTools,
    messages,
    clearError,
  } = useConversation()

  const [selectedModelId, setSelectedModelId] = useState(RESPONSE_GENERATION_MODELS[0].id)

  // Mobile: use drawer
  if (isMobile) {
    return (
      <div data-testid="copilot-chat-container" className={cn("h-full", className)}>
        <ChatDrawer width={sidebarWidth}>
          <div className="flex flex-col h-full">
            {/* Mobile header */}
            <div
              data-testid="chat-header"
              className="flex items-center justify-between px-4 py-3 border-b border-slate-200"
            >
              <h2 className="text-sm font-semibold text-slate-900">AI Assistant</h2>
              <div className="flex items-center gap-2">
                <ModelSelector
                  selectedModelId={selectedModelId}
                  onModelChange={setSelectedModelId}
                />
                <ObservabilityToggle
                  isEnabled={isObservabilityEnabled}
                  onToggle={toggleObservability}
                />
              </div>
            </div>

            {/* Content area */}
            <div className="flex-1 overflow-y-auto p-4">
              {messages.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <MessageBubble
                      key={msg.id}
                      role={msg.role}
                      content={msg.content}
                      observabilityLevel={observabilityLevel as 0 | 1 | 2 | 3}
                      isObservabilityEnabled={isObservabilityEnabled}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </ChatDrawer>
      </div>
    )
  }

  // Desktop: use sidebar
  return (
    <div data-testid="copilot-chat-container" className={cn("flex h-full", className)}>
      {/* Main visualization canvas */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div
          data-testid="chat-header"
          className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white"
        >
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-semibold text-slate-900">Analysis Canvas</h2>
          </div>
          <div className="flex items-center gap-3">
            <ModelSelector
              selectedModelId={selectedModelId}
              onModelChange={setSelectedModelId}
            />
            <ObservabilityToggle
              isEnabled={isObservabilityEnabled}
              onToggle={toggleObservability}
            />
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-hidden bg-slate-50">
          {/* Loading states (FR-1.6) */}
          {isLoading && loadingLevel === 0 && (
            <div className="p-4">
              <ChartSkeleton />
            </div>
          )}

          {isLoading && loadingLevel === 1 && currentStage && (
            <div className="p-4">
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
                <StageIndicator stage={currentStage} />
              </div>
              <div className="mt-4">
                <ChartSkeleton />
              </div>
            </div>
          )}

          {isLoading && loadingLevel >= 2 && (
            <div className="p-4 space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
                This is taking longer than expected. Please wait...
              </div>
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
                <StageIndicator stage={currentStage || "Generating response"} />
              </div>
            </div>
          )}

          {/* Multi-tool pending (FR-1.6) */}
          {hasPendingTools && (
            <div className="p-4 space-y-2">
              {pendingTools.map((tool) => (
                <div
                  key={tool}
                  className="flex items-center gap-2 text-sm text-slate-500"
                >
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  Waiting for results from {tool}...
                </div>
              ))}
            </div>
          )}

          {/* Error states (FR-1.7) */}
          {error && (
            <div className="p-4">
              <ErrorMessage
                message={error}
                onRetry={() => {
                  clearError()
                }}
                suggestion="Try adjusting: time period"
              />
            </div>
          )}

          {/* Empty state (FR-1.8) */}
          {messages.length === 0 && !isLoading && (
            <EmptyState />
          )}
        </div>
      </div>

      {/* Chat sidebar (FR-1.1) */}
      <ChatSidebar
        width={sidebarWidth}
        isCollapsed={isSidebarCollapsed || isCollapsed}
      />
    </div>
  )
}
