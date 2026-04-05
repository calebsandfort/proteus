import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { FloatingActionButton } from "./FloatingActionButton"

describe("FloatingActionButton", () => {
  describe("Basic Rendering", () => {
    it("renders FAB button", () => {
      render(<FloatingActionButton onClick={vi.fn()} isOpen={false} />)
      expect(screen.getByTestId("fab-button")).toBeDefined()
    })

    it("calls onClick when clicked", () => {
      const handleClick = vi.fn()
      render(<FloatingActionButton onClick={handleClick} isOpen={false} />)
      fireEvent.click(screen.getByTestId("fab-button"))
      expect(handleClick).toHaveBeenCalled()
    })

    it("reflects isOpen state", () => {
      const { rerender } = render(
        <FloatingActionButton onClick={vi.fn()} isOpen={false} />
      )
      expect(screen.getByTestId("fab-button").getAttribute("data-open")).toBe("false")

      rerender(<FloatingActionButton onClick={vi.fn()} isOpen={true} />)
      expect(screen.getByTestId("fab-button").getAttribute("data-open")).toBe("true")
    })

    it("accepts className prop", () => {
      const { container } = render(
        <FloatingActionButton onClick={vi.fn()} isOpen={false} className="custom-class" />
      )
      expect(container.firstChild).toBeDefined()
    })
  })

  describe("Accessibility", () => {
    it("has aria-expanded attribute", () => {
      const { rerender } = render(
        <FloatingActionButton onClick={vi.fn()} isOpen={false} />
      )
      expect(screen.getByTestId("fab-button").getAttribute("aria-expanded")).toBe("false")

      rerender(<FloatingActionButton onClick={vi.fn()} isOpen={true} />)
      expect(screen.getByTestId("fab-button").getAttribute("aria-expanded")).toBe("true")
    })

    it("has aria-label for screen readers", () => {
      render(<FloatingActionButton onClick={vi.fn()} isOpen={false} ariaLabel="Open chat" />)
      expect(screen.getByTestId("fab-button").getAttribute("aria-label")).toBe("Open chat")
    })
  })
})
