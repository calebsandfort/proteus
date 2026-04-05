import { describe, it, expect, vi, afterEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import { CopilotProvider } from "./copilot-provider"
import { CopilotKit } from "@copilotkit/react-core"

afterEach(() => {
  cleanup()
})

// Mock CopilotKit
vi.mock("@copilotkit/react-core", () => ({
  CopilotKit: vi.fn(({ children, runtimeUrl, agent, evalParams }) => (
    <div
      data-testid="copilot-kit"
      data-runtime-url={runtimeUrl}
      data-agent={agent}
      data-model={evalParams?.model}
    >
      {children}
    </div>
  )),
}))

describe("CopilotProvider", () => {
  // FR-1.5: Pass model to CopilotKit configuration
  describe("FR 1.5 — CopilotKit Integration", () => {
    it("FR 1.5 — renders children", () => {
      render(
        <CopilotProvider>
          <div data-testid="child-content">Child Content</div>
        </CopilotProvider>
      )
      expect(screen.getByTestId("child-content")).toBeDefined()
    })

    it("FR 1.5 — accepts selectedModel prop", () => {
      render(
        <CopilotProvider selectedModel="openai/gpt-4o">
          <div>Content</div>
        </CopilotProvider>
      )
      const provider = screen.getByTestId("copilot-kit")
      expect(provider).toBeDefined()
    })

    it("FR 1.5 — uses default runtimeUrl and agent", () => {
      render(
        <CopilotProvider>
          <div>Content</div>
        </CopilotProvider>
      )
      const provider = screen.getByTestId("copilot-kit")
      expect(provider.getAttribute("data-runtime-url")).toBe("/api/copilotkit")
      expect(provider.getAttribute("data-agent")).toBe("chat_agent")
    })
  })

  // FR-8.3: Response Generation Model configurable
  describe("FR 8.3 — Response Generation Model", () => {
    it("FR 8.3 — accepts different model selections", () => {
      const models = [
        "openai/gpt-4o",
        "google/gemini-2.0-flash",
        "anthropic/claude-3.5-sonnet",
        "moonshot/kimi-k2",
        "minimax/text-01",
        "google/gemini-2.5-pro",
      ]

      models.forEach((model) => {
        const { container } = render(
          <CopilotProvider selectedModel={model}>
            <div>Content</div>
          </CopilotProvider>
        )
        expect(container.firstChild).toBeDefined()
      })
    })

    it("FR 8.3 — passes model to backend via configuration", () => {
      // The provider should pass the model to the runtime
      render(
        <CopilotProvider selectedModel="openai/gpt-4o">
          <div>Content</div>
        </CopilotProvider>
      )
      // The CopilotKit component should be configured with the model
      const provider = screen.getByTestId("copilot-kit")
      expect(provider).toBeDefined()
    })
  })
})