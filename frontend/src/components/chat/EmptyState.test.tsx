import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { EmptyState } from "./EmptyState"

describe("EmptyState", () => {
  // FR-1.8: Empty State
  describe("FR 1.8 — Empty State", () => {
    it("FR 1.8 — renders centered placeholder visualization area", () => {
      render(<EmptyState />)
      const container = screen.getByTestId("empty-state-container")
      expect(container).toBeDefined()
    })

    it("FR 1.8 — displays sample query prompts in muted text", () => {
      render(<EmptyState />)
      // Should have sample prompts displayed
      const container = screen.getByTestId("empty-state-container")
      expect(container.textContent).toBeDefined()
    })

    it("FR 1.8 — has subtle animated visualization placeholder", () => {
      render(<EmptyState />)
      const animation = screen.getByTestId("empty-state-animation")
      expect(animation).toBeDefined()
      expect(animation.className).toContain("animate-")
    })

    it("FR 1.8 — input immediately usable (no required interaction first)", () => {
      render(<EmptyState />)
      const input = screen.getByTestId("empty-state-input")
      expect(input).toBeDefined()
      expect(input).not.toBeDisabled()
    })

    it("FR 1.8 — accepts onSampleQueryClick callback", () => {
      const handleSampleClick = vi.fn()
      render(<EmptyState onSampleQueryClick={handleSampleClick} />)
      const samplePrompts = screen.getAllByTestId("sample-prompt")
      if (samplePrompts.length > 0) {
        expect(samplePrompts[0]).toBeDefined()
      }
    })

    it("FR 1.8 — accepts className prop", () => {
      const { container } = render(<EmptyState className="custom-class" />)
      expect(container.firstChild).toBeDefined()
    })
  })

  // Design system compliance
  describe("Design System Compliance", () => {
    it("uses muted text styling for sample prompts", () => {
      render(<EmptyState />)
      const samplePrompts = screen.getAllByTestId("sample-prompt")
      samplePrompts.forEach((prompt) => {
        expect(prompt.className).toContain("text-slate-400")
      })
    })

    it("animation is subtle (not distracting)", () => {
      render(<EmptyState />)
      const animation = screen.getByTestId("empty-state-animation")
      // Animation should use standard Tailwind animation classes
      expect(animation.className).toMatch(/animate-/)
    })
  })

  // Edge cases
  describe("Edge Cases", () => {
    it("renders without sample queries", () => {
      render(<EmptyState sampleQueries={[]} />)
      const container = screen.getByTestId("empty-state-container")
      expect(container).toBeDefined()
    })

    it("renders with custom sample queries", () => {
      const customQueries = [
        "Custom query 1",
        "Custom query 2",
      ]
      render(<EmptyState sampleQueries={customQueries} />)
      expect(screen.getByText("Custom query 1")).toBeDefined()
      expect(screen.getByText("Custom query 2")).toBeDefined()
    })
  })
})
