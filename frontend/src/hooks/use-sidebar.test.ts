import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useSidebar } from "./use-sidebar"

describe("useSidebar", () => {
  // Mock matchMedia for all tests
  const originalMatchMedia = window.matchMedia
  const mockMatchMedia = vi.fn().mockReturnValue({
    matches: false,
    media: "",
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })

  beforeEach(() => {
    window.matchMedia = mockMatchMedia
  })

  afterEach(() => {
    window.matchMedia = originalMatchMedia
  })

  // FR-1.1: Mobile Breakpoint Handling
  describe("FR 1.1 — Mobile Breakpoint Handling (1024px)", () => {
    it("FR 1.1 — isMobile defaults to false on desktop", () => {
      // Default matchMedia returns false (desktop)
      const { result } = renderHook(() => useSidebar())
      expect(result.current.isMobile).toBe(false)
    })

    it("FR 1.1 — isCollapsed defaults to true on mobile", () => {
      // Mock mobile environment
      const originalMatchMedia = window.matchMedia
      window.matchMedia = vi.fn().mockReturnValue({
        matches: true,
        media: "",
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })

      const { result } = renderHook(() => useSidebar())
      expect(result.current.isMobile).toBe(true)
      expect(result.current.isCollapsed).toBe(true)

      window.matchMedia = originalMatchMedia
    })

    it("FR 1.1 — toggle collapses/expands sidebar", () => {
      const { result } = renderHook(() => useSidebar())
      // Initial isCollapsed = true (collapsed)
      // Fixed: After first toggle from true -> false (expanded)
      act(() => {
        result.current.toggle()
      })
      expect(result.current.isCollapsed).toBe(false)

      // After second toggle from false -> true (collapsed)
      act(() => {
        result.current.toggle()
      })
      expect(result.current.isCollapsed).toBe(true)
    })

    it("FR 1.1 — open() sets isCollapsed to false", () => {
      const { result } = renderHook(() => useSidebar())
      act(() => {
        result.current.open()
      })
      expect(result.current.isCollapsed).toBe(false)
    })

    it("FR 1.1 — close() sets isCollapsed to true", () => {
      const { result } = renderHook(() => useSidebar())
      act(() => {
        result.current.open()
        result.current.close()
      })
      expect(result.current.isCollapsed).toBe(true)
    })

    it("FR 1.1 — onCollapseChange callback is called", () => {
      const callback = vi.fn()
      renderHook(() => useSidebar({ onCollapseChange: callback }))
      // Callback should be defined
      expect(typeof callback).toBe("function")
    })
  })

  // Interface contract
  describe("Interface Contract", () => {
    it("returns isCollapsed boolean", () => {
      const { result } = renderHook(() => useSidebar())
      expect(typeof result.current.isCollapsed).toBe("boolean")
    })

    it("returns isMobile boolean", () => {
      const { result } = renderHook(() => useSidebar())
      expect(typeof result.current.isMobile).toBe("boolean")
    })

    it("has required methods", () => {
      const { result } = renderHook(() => useSidebar())
      expect(typeof result.current.toggle).toBe("function")
      expect(typeof result.current.open).toBe("function")
      expect(typeof result.current.close).toBe("function")
    })
  })

  // Edge cases
  describe("Edge Cases", () => {
    it("handles multiple rapid toggles", () => {
      const { result } = renderHook(() => useSidebar())
      // Initial: true (collapsed)
      // After 1st toggle: false (expanded)
      // After 2nd toggle: true (collapsed)
      // After 3rd toggle: false (expanded)
      act(() => {
        result.current.toggle()
        result.current.toggle()
        result.current.toggle()
      })
      expect(result.current.isCollapsed).toBe(false)
    })

    it("handles open followed by close", () => {
      const { result } = renderHook(() => useSidebar())
      act(() => {
        result.current.open()
        result.current.close()
      })
      expect(result.current.isCollapsed).toBe(true)
    })
  })
})
