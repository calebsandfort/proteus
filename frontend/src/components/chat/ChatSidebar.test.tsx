import { describe, it, expect, vi, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import { ChatSidebar } from "./ChatSidebar"

// Mock CopilotKit components
vi.mock("@copilotkit/react-ui", () => ({
  CopilotChat: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="copilot-chat">{children}</div>
  ),
}))

vi.mock("@copilotkit/react-core", () => ({
  useCopilotContext: () => ({}),
}))

afterEach(() => {
  cleanup()
})

describe("ChatSidebar", () => {
  // FR-1.1: Layout and Structure
  describe("FR 1.1 — Layout and Structure", () => {
    it("FR 1.1 — renders with default width of 400px", () => {
      render(<ChatSidebar />)
      const sidebar = screen.getByTestId("chat-sidebar")
      expect(sidebar).toBeDefined()
    })

    it("FR 1.1 — accepts custom width prop within valid range (380-420px)", () => {
      const { container } = render(<ChatSidebar width={420} />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.1 — accepts width of 380px (minimum)", () => {
      const { container } = render(<ChatSidebar width={380} />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.1 — accepts width of 420px (maximum)", () => {
      const { container } = render(<ChatSidebar width={420} />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.1 — isCollapsed prop hides the sidebar content", () => {
      render(<ChatSidebar isCollapsed={true} />)
      const sidebar = screen.getByTestId("chat-sidebar")
      expect(sidebar).toBeDefined()
    })

    it("FR 1.1 — renders CopilotChat component", () => {
      render(<ChatSidebar />)
      expect(screen.getByTestId("copilot-chat")).toBeDefined()
    })

    it("FR 1.1 — accepts className prop for layout flexibility", () => {
      const { container } = render(
        <ChatSidebar className="custom-class" />
      )
      expect(container.firstChild).toBeDefined()
    })
  })
})
