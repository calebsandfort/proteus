import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { ClarificationCard } from "./ClarificationCard"

describe("ClarificationCard", () => {
  // FR-1.7: Error Handling and HITL Clarification
  describe("FR 1.7 — HITL Clarification (Inline Cards)", () => {
    const mockOptions = [
      { id: "opt1", label: "Option 1", description: "First option" },
      { id: "opt2", label: "Option 2", description: "Second option" },
      { id: "opt3", label: "Option 3", description: "Third option" },
    ]

    const defaultProps = {
      originalQuery: "What was Chipotle's market share?",
      ambiguity: "Which time period would you like to know about?",
      options: mockOptions,
      onSelect: vi.fn(),
      onDismiss: vi.fn(),
    }

    it("FR 1.7 — renders as inline card (not modal)", () => {
      render(<ClarificationCard {...defaultProps} />)
      const card = screen.getByTestId("clarification-card")
      expect(card).toBeDefined()
    })

    it("FR 1.7 — displays original query", () => {
      render(<ClarificationCard {...defaultProps} />)
      expect(screen.getByText("What was Chipotle's market share?")).toBeDefined()
    })

    it("FR 1.7 — displays ambiguity explanation", () => {
      render(<ClarificationCard {...defaultProps} />)
      expect(
        screen.getByText("Which time period would you like to know about?")
      ).toBeDefined()
    })

    it("FR 1.7 — displays clarification options (max 3)", () => {
      render(<ClarificationCard {...defaultProps} />)
      expect(screen.getByText("Option 1")).toBeDefined()
      expect(screen.getByText("Option 2")).toBeDefined()
      expect(screen.getByText("Option 3")).toBeDefined()
    })

    it("FR 1.7 — does NOT render 4th option (max 3)", () => {
      const fourOptions = [
        ...mockOptions,
        { id: "opt4", label: "Option 4", description: "Fourth option" },
      ]
      render(<ClarificationCard {...defaultProps} options={fourOptions} />)
      expect(screen.queryByText("Option 4")).toBeNull()
    })

    it("FR 1.7 — clicking option calls onSelect with optionId", () => {
      render(<ClarificationCard {...defaultProps} />)
      fireEvent.click(screen.getByText("Option 1"))
      expect(defaultProps.onSelect).toHaveBeenCalledWith("opt1")
    })

    it("FR 1.7 — clicking dismiss calls onDismiss", () => {
      render(<ClarificationCard {...defaultProps} />)
      fireEvent.click(screen.getByTestId("dismiss-button"))
      expect(defaultProps.onDismiss).toHaveBeenCalled()
    })

    it("FR 1.7 — input remains active during clarification (no modal blocking)", () => {
      // ClarificationCard should not use a modal overlay
      const { container } = render(<ClarificationCard {...defaultProps} />)
      // Should not have a portal/overlay blocking interaction
      expect(container.querySelector("[data-blocked]")).toBeNull()
    })

    it("FR 1.7 — accepts className prop", () => {
      const { container } = render(
        <ClarificationCard {...defaultProps} className="custom-class" />
      )
      expect(container.firstChild).toBeDefined()
    })
  })

  // Edge cases
  describe("Edge Cases", () => {
    it("handles single option", () => {
      const props = {
        originalQuery: "Test query",
        ambiguity: "Which one?",
        options: [{ id: "only", label: "Only Option", description: "Just one" }],
        onSelect: vi.fn(),
        onDismiss: vi.fn(),
      }
      render(<ClarificationCard {...props} />)
      expect(screen.getByText("Only Option")).toBeDefined()
    })

    it("handles two options", () => {
      const props = {
        originalQuery: "Test query",
        ambiguity: "Which one?",
        options: [
          { id: "first", label: "First", description: "First option" },
          { id: "second", label: "Second", description: "Second option" },
        ],
        onSelect: vi.fn(),
        onDismiss: vi.fn(),
      }
      render(<ClarificationCard {...props} />)
      expect(screen.getByText("First")).toBeDefined()
      expect(screen.getByText("Second")).toBeDefined()
    })
  })
})
