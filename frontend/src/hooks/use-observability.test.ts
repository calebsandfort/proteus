import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useObservability } from "./use-observability"

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, "localStorage", { value: localStorageMock })

describe("useObservability", () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  // FR-1.3: Observability Panel State
  describe("FR 1.3 — Observability Panel State", () => {
    it("FR 1.3 — isEnabled defaults to false", () => {
      const { result } = renderHook(() => useObservability())
      expect(result.current.isEnabled).toBe(false)
    })

    it("FR 1.3 — level defaults to 0", () => {
      const { result } = renderHook(() => useObservability())
      expect(result.current.level).toBe(0)
    })

    it("FR 1.3 — toggle changes isEnabled state", () => {
      const { result } = renderHook(() => useObservability())
      act(() => {
        result.current.toggle()
      })
      expect(result.current.isEnabled).toBe(true)
    })

    it("FR 1.3 — second toggle reverts to disabled", () => {
      const { result } = renderHook(() => useObservability())
      act(() => {
        result.current.toggle()
        result.current.toggle()
      })
      expect(result.current.isEnabled).toBe(false)
    })
  })

  // FR-1.3: Persistence
  describe("FR 1.3 — localStorage Persistence", () => {
    it("FR 1.3 — saves isEnabled state to localStorage", () => {
      const { result } = renderHook(() => useObservability())
      act(() => {
        result.current.toggle()
      })
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "proteus-observability-enabled",
        "true"
      )
    })

    it("FR 1.3 — loads isEnabled state from localStorage on init", () => {
      localStorageMock.getItem.mockReturnValueOnce("true")
      const { result } = renderHook(() => useObservability())
      expect(result.current.isEnabled).toBe(true)
    })

    it("FR 1.3 — saves level to localStorage", () => {
      const { result } = renderHook(() => useObservability())
      act(() => {
        result.current.setLevel(2)
      })
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "proteus-observability-level",
        "2"
      )
    })

    it("FR 1.3 — loads level from localStorage on init", () => {
      localStorageMock.getItem.mockReturnValueOnce("true") // isEnabled
      localStorageMock.getItem.mockReturnValueOnce("3") // level
      const { result } = renderHook(() => useObservability())
      expect(result.current.level).toBe(3)
    })
  })

  // FR-1.4: Progressive Disclosure Levels
  describe("FR 1.4 — Progressive Disclosure (4-Level)", () => {
    it("FR 1.4 — Level 0 is default (clean chat)", () => {
      const { result } = renderHook(() => useObservability())
      expect(result.current.level).toBe(0)
      expect(result.current.isEnabled).toBe(false)
    })

    it("FR 1.4 — Level 1 shows expand icons and metadata", () => {
      const { result } = renderHook(() => useObservability())
      act(() => {
        result.current.toggle()
        result.current.setLevel(1)
      })
      expect(result.current.level).toBe(1)
      expect(result.current.isEnabled).toBe(true)
    })

    it("FR 1.4 — Level 2 shows inline JSON viewer", () => {
      const { result } = renderHook(() => useObservability())
      act(() => {
        result.current.setLevel(2)
      })
      expect(result.current.level).toBe(2)
    })

    it("FR 1.4 — Level 3 shows raw API data", () => {
      const { result } = renderHook(() => useObservability())
      act(() => {
        result.current.setLevel(3)
      })
      expect(result.current.level).toBe(3)
    })

    it("FR 1.4 — setLevel only accepts 0-3", () => {
      const { result } = renderHook(() => useObservability())
      act(() => {
        result.current.setLevel(1)
      })
      expect(result.current.level).toBe(1)

      act(() => {
        result.current.setLevel(0)
      })
      expect(result.current.level).toBe(0)
    })
  })

  // Interface contract
  describe("Interface Contract", () => {
    it("returns ObservabilityState interface", () => {
      const { result } = renderHook(() => useObservability())
      expect(typeof result.current.isEnabled).toBe("boolean")
      expect(typeof result.current.level).toBe("number")
    })

    it("has required methods", () => {
      const { result } = renderHook(() => useObservability())
      expect(typeof result.current.toggle).toBe("function")
      expect(typeof result.current.setLevel).toBe("function")
      expect(typeof result.current.enable).toBe("function")
      expect(typeof result.current.disable).toBe("function")
    })
  })

  // Edge cases
  describe("Edge Cases", () => {
    it("handles invalid localStorage value gracefully", () => {
      localStorageMock.getItem.mockReturnValueOnce("invalid")
      const { result } = renderHook(() => useObservability())
      expect(result.current.isEnabled).toBe(false)
    })

    it("handles negative level from localStorage", () => {
      localStorageMock.getItem.mockReturnValueOnce("-1")
      const { result } = renderHook(() => useObservability())
      // Should clamp to valid range
      expect(result.current.level).toBe(0)
    })

    it("handles level > 3 from localStorage", () => {
      localStorageMock.getItem.mockReturnValueOnce("10")
      const { result } = renderHook(() => useObservability())
      // Should clamp to valid range
      expect(result.current.level).toBe(0)
    })
  })
})
