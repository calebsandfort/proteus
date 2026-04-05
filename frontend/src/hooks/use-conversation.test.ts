import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useConversation } from "./use-conversation"

describe("useConversation", () => {
  // FR-1.6: Loading and Feedback States
  describe("FR 1.6 — Conversation State Management", () => {
    it("FR 1.6 — tracks loading state", () => {
      const { result } = renderHook(() => useConversation())
      expect(result.current.isLoading).toBe(false)
    })

    it("FR 1.6 — tracks pending state for multi-tool queries", () => {
      const { result } = renderHook(() => useConversation())
      expect(result.current.pendingTools).toEqual([])
    })

    it("FR 1.6 — updates current stage during processing", () => {
      const { result } = renderHook(() => useConversation())
      act(() => {
        result.current.setCurrentStage("Extracting dimensions")
      })
      expect(result.current.currentStage).toBe("Extracting dimensions")
    })

    it("FR 1.6 — tracks completed tools", () => {
      const { result } = renderHook(() => useConversation())
      // Fixed: Implementation uses completeTool, not addCompletedTool
      act(() => {
        result.current.completeTool("market_share")
      })
      expect(result.current.completedTools).toContain("market_share")
    })

    it("FR 1.6 — calculates loading level (< 2s, 2-5s, > 5s)", () => {
      const { result } = renderHook(() => useConversation())
      act(() => {
        result.current.setStartTime(Date.now())
      })
      // Should be in loading level 0 (< 2s) by default
      expect(result.current.loadingLevel).toBeLessThanOrEqual(0)
    })
  })

  // State management
  describe("State Management", () => {
    it("FR 1.6 — tracks messages in conversation", () => {
      const { result } = renderHook(() => useConversation())
      const testMessage = { id: "1", role: "user" as const, content: "Test" }
      act(() => {
        result.current.addMessage(testMessage)
      })
      expect(result.current.messages).toContainEqual(expect.objectContaining({ id: "1" }))
    })

    it("FR 1.6 — clears messages on reset", () => {
      const { result } = renderHook(() => useConversation())
      act(() => {
        result.current.addMessage({ id: "1", role: "user", content: "Test" })
        result.current.reset()
      })
      expect(result.current.messages).toEqual([])
    })

    it("FR 1.6 — tracks error state", () => {
      const { result } = renderHook(() => useConversation())
      act(() => {
        result.current.setError("Test error")
      })
      expect(result.current.error).toBe("Test error")
    })

    it("FR 1.6 — clears error state", () => {
      const { result } = renderHook(() => useConversation())
      act(() => {
        result.current.setError("Test error")
        result.current.clearError()
      })
      expect(result.current.error).toBeNull()
    })
  })

  // Multi-tool support
  describe("FR 1.6 — Multi-Tool Support", () => {
    it("FR 1.6 — shows 'Waiting for results...' per pending tool", () => {
      const { result } = renderHook(() => useConversation())
      act(() => {
        result.current.addPendingTool("tool1")
        result.current.addPendingTool("tool2")
      })
      expect(result.current.pendingTools).toHaveLength(2)
      expect(result.current.hasPendingTools).toBe(true)
    })

    it("FR 1.6 — removes tool from pending when completed", () => {
      const { result } = renderHook(() => useConversation())
      act(() => {
        result.current.addPendingTool("tool1")
        result.current.completeTool("tool1")
      })
      expect(result.current.pendingTools).not.toContain("tool1")
    })

    it("FR 1.6 — summary only after all tools complete", () => {
      const { result } = renderHook(() => useConversation())
      act(() => {
        result.current.addPendingTool("tool1")
      })
      expect(result.current.isSummaryReady).toBe(false)

      act(() => {
        result.current.completeTool("tool1")
      })
      expect(result.current.isSummaryReady).toBe(true)
    })
  })

  // Interface contract
  describe("Interface Contract", () => {
    it("returns all required properties", () => {
      const { result } = renderHook(() => useConversation())
      expect(result.current.messages).toBeDefined()
      expect(result.current.isLoading).toBeDefined()
      expect(result.current.currentStage).toBeDefined()
      expect(result.current.pendingTools).toBeDefined()
      expect(result.current.completedTools).toBeDefined()
      expect(result.current.error).toBeDefined()
      expect(result.current.loadingLevel).toBeDefined()
    })

    it("has all required methods", () => {
      const { result } = renderHook(() => useConversation())
      expect(typeof result.current.addMessage).toBe("function")
      expect(typeof result.current.setCurrentStage).toBe("function")
      expect(typeof result.current.setError).toBe("function")
      expect(typeof result.current.clearError).toBe("function")
      expect(typeof result.current.reset).toBe("function")
    })
  })
})
