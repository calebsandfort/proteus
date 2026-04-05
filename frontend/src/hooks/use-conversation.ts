"use client"

import { useState, useCallback, useMemo } from "react"

export interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  timestamp?: number
}

interface UseConversationOptions {
  onStageChange?: (stage: string) => void
}

const STAGE_NAMES = [
  "Parsing query",
  "Retrieving tools",
  "Extracting dimensions",
  "Querying data",
  "Generating response",
] as const

export type StageName = (typeof STAGE_NAMES)[number]

interface UseConversationReturn {
  messages: Message[]
  isLoading: boolean
  currentStage: StageName | null
  pendingTools: string[]
  completedTools: string[]
  error: string | null
  loadingLevel: number
  isSummaryReady: boolean
  hasPendingTools: boolean
  startTime: number | null
  addMessage: (message: Message) => void
  setCurrentStage: (stage: StageName | null) => void
  setError: (error: string | null) => void
  clearError: () => void
  addPendingTool: (toolId: string) => void
  completeTool: (toolId: string) => void
  setStartTime: (time: number) => void
  reset: () => void
}

export function useConversation(_options?: UseConversationOptions): UseConversationReturn {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentStage, setCurrentStageState] = useState<StageName | null>(null)
  const [pendingTools, setPendingTools] = useState<string[]>([])
  const [completedTools, setCompletedTools] = useState<string[]>([])
  const [error, setErrorState] = useState<string | null>(null)
  const [startTime, setStartTimeState] = useState<number | null>(null)

  const hasPendingTools = pendingTools.length > 0

  const isSummaryReady = useMemo(() => {
    return pendingTools.length === 0 && completedTools.length > 0
  }, [pendingTools, completedTools])

  const loadingLevel = useMemo(() => {
    if (!startTime) return 0
    const elapsed = Date.now() - startTime
    const seconds = elapsed / 1000

    if (seconds < 2) return 0
    if (seconds < 5) return 1
    return 2 // 5s+
  }, [startTime])

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message])
  }, [])

  const setCurrentStage = useCallback((stage: StageName | null) => {
    setCurrentStageState(stage)
  }, [])

  const setError = useCallback((error: string | null) => {
    setErrorState(error)
  }, [])

  const clearError = useCallback(() => {
    setErrorState(null)
  }, [])

  const addPendingTool = useCallback((toolId: string) => {
    setPendingTools((prev) => {
      if (prev.includes(toolId)) return prev
      return [...prev, toolId]
    })
    // Start timing if this is the first pending tool
    setStartTimeState((prev) => prev ?? Date.now())
    setIsLoading(true)
  }, [])

  const completeTool = useCallback((toolId: string) => {
    setPendingTools((prev) => prev.filter((id) => id !== toolId))
    setCompletedTools((prev) => {
      if (prev.includes(toolId)) return prev
      return [...prev, toolId]
    })
    // If no more pending tools, we're done loading
    setPendingTools((current) => {
      if (current.length === 0 && current !== pendingTools) {
        setIsLoading(false)
      }
      return current
    })
  }, [])

  const setStartTime = useCallback((time: number) => {
    setStartTimeState(time)
  }, [])

  const reset = useCallback(() => {
    setMessages([])
    setIsLoading(false)
    setCurrentStageState(null)
    setPendingTools([])
    setCompletedTools([])
    setErrorState(null)
    setStartTimeState(null)
  }, [])

  return {
    messages,
    isLoading,
    currentStage,
    pendingTools,
    completedTools,
    error,
    loadingLevel,
    isSummaryReady,
    hasPendingTools,
    startTime,
    addMessage,
    setCurrentStage,
    setError,
    clearError,
    addPendingTool,
    completeTool,
    setStartTime,
    reset,
  }
}
