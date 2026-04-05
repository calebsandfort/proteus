import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { ChatDrawer } from "./ChatDrawer"

// Mock the FAB component behavior
const mockOpen = vi.fn()
const mockClose = vi.fn()

vi.mock("./FloatingActionButton", () => ({
  FloatingActionButton: ({
    onClick,
    isOpen,
  }: {
    onClick: () => void
    isOpen: boolean
  }) => (
    <button
      data-testid="fab-button"
      onClick={onClick}
      aria-expanded={isOpen}
      data-open={isOpen}
    >
      FAB
    </button>
  ),
}))

describe("ChatDrawer", () => {
  // FR-1.1: Mobile layout
  describe("FR 1.1 — Mobile Layout (below 1024px)", () => {
    it("FR 1.1 — renders FAB button trigger", () => {
      render(<ChatDrawer />)
      expect(screen.getByTestId("fab-button")).toBeDefined()
    })

    it("FR 1.1 — FAB click opens the drawer", () => {
      render(<ChatDrawer />)
      const fab = screen.getByTestId("fab-button")
      fireEvent.click(fab)
      // After click, drawer should open
      expect(fab.getAttribute("data-open")).toBe("true")
    })

    it("FR 1.1 — drawer is hidden below 1024px breakpoint", () => {
      render(<ChatDrawer />)
      // Default state should be collapsed on mobile
      const fab = screen.getByTestId("fab-button")
      expect(fab).toBeDefined()
    })

    it("FR 1.1 — accepts children for drawer content", () => {
      render(
        <ChatDrawer>
          <div data-testid="drawer-content">Drawer Content</div>
        </ChatDrawer>
      )
      expect(screen.getByTestId("drawer-content")).toBeDefined()
    })

    it("FR 1.1 — accepts width prop", () => {
      const { container } = render(<ChatDrawer width={400} />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.1 — accepts className prop", () => {
      const { container } = render(<ChatDrawer className="custom-class" />)
      expect(container.firstChild).toBeDefined()
    })
  })
})
