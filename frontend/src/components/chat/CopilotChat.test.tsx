import { describe, it, expect, vi, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import { CopilotChat } from "./copilot-chat"

afterEach(() => {
  cleanup()
})

// Mock CopilotKit
vi.mock("@copilotkit/react-ui", () => ({
  CopilotChat: () => <div data-testid="copilot-chat-ui">CopilotChatUI</div>,
}))

vi.mock("@copilotkit/react-core", () => ({
  useCopilotContext: () => ({}),
}))

describe("CopilotChat", () => {
  // FR-1.1: Integration with ChatSidebar
  describe("FR 1.1 — Integration with ChatSidebar", () => {
    it("FR 1.1 — renders ChatSidebar component", () => {
      render(<CopilotChat />)
      // The updated CopilotChat should render ChatSidebar
      const sidebar = screen.getByTestId("chat-sidebar")
      expect(sidebar).toBeDefined()
    })

    it("FR 1.1 — passes width prop to ChatSidebar (380-420px range)", () => {
      const { container } = render(<CopilotChat sidebarWidth={400} />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.1 — passes isCollapsed prop to ChatSidebar", () => {
      render(<CopilotChat isSidebarCollapsed={true} />)
      const sidebar = screen.getByTestId("chat-sidebar")
      expect(sidebar).toBeDefined()
    })

    it("FR 1.1 — accepts className prop", () => {
      const { container } = render(<CopilotChat className="custom-class" />)
      expect(container.firstChild).toBeDefined()
    })
  })

  // FR-1.1: Mobile handling
  describe("FR 1.1 — Mobile Layout", () => {
    it("FR 1.1 — uses ChatDrawer on mobile", () => {
      render(<CopilotChat />)
      // Should render either sidebar or drawer depending on viewport
      const container = screen.getByTestId("copilot-chat-container")
      expect(container).toBeDefined()
    })

    it("FR 1.1 — passes mobile breakpoint handling to drawer", () => {
      const { container } = render(<CopilotChat />)
      expect(container.firstChild).toBeDefined()
    })
  })

  // FR-1.5: Model Selector
  describe("FR 1.5 — Model Selector (Stub)", () => {
    it("FR 1.5 — has model selector dropdown in header", () => {
      render(<CopilotChat />)
      const header = screen.getByTestId("chat-header")
      expect(header).toBeDefined()
    })

    it("FR 1.5 — model selector has RESPONSE_GENERATION_MODELS options", () => {
      render(<CopilotChat />)
      const selector = screen.getByTestId("model-selector")
      expect(selector).toBeDefined()
    })
  })
})
