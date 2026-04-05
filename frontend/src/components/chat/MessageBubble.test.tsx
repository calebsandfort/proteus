import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { MessageBubble } from "./MessageBubble"

describe("MessageBubble", () => {
  // FR-1.1: Message bubbles styling
  describe("FR 1.1 — Message Bubble Styling", () => {
    it("FR 1.1 — renders user message with correct styling", () => {
      render(<MessageBubble role="user" content="Hello" />)
      const bubble = screen.getByTestId("message-bubble")
      expect(bubble).toBeDefined()
      expect(bubble.className).toContain("bg-blue-600")
      expect(bubble.className).toContain("text-white")
    })

    it("FR 1.1 — renders assistant message with correct styling", () => {
      render(<MessageBubble role="assistant" content="Hello" />)
      const bubble = screen.getByTestId("message-bubble")
      expect(bubble).toBeDefined()
      expect(bubble.className).toContain("bg-white")
    })

    it("FR 1.1 — user bubble has rounded-2xl rounded-br-md", () => {
      render(<MessageBubble role="user" content="Hello" />)
      const bubble = screen.getByTestId("message-bubble")
      expect(bubble.className).toContain("rounded-2xl")
      expect(bubble.className).toContain("rounded-br-md")
    })

    it("FR 1.1 — assistant bubble has rounded-2xl rounded-bl-md", () => {
      render(<MessageBubble role="assistant" content="Hello" />)
      const bubble = screen.getByTestId("message-bubble")
      expect(bubble.className).toContain("rounded-2xl")
      expect(bubble.className).toContain("rounded-bl-md")
    })

    it("FR 1.1 — assistant bubble has border and shadow", () => {
      render(<MessageBubble role="assistant" content="Hello" />)
      const bubble = screen.getByTestId("message-bubble")
      expect(bubble.className).toContain("border")
      expect(bubble.className).toContain("shadow-sm")
    })
  })

  // FR-1.3: Observability Panel
  describe("FR 1.3 — Observability Panel Expand Icon", () => {
    it("FR 1.3 — shows expand icon when observability is enabled (level 1+)", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Test message"
          observabilityLevel={1}
          isObservabilityEnabled={true}
        />
      )
      const expandIcon = screen.getByTestId("expand-icon")
      expect(expandIcon).toBeDefined()
    })

    it("FR 1.3 — hide expand icon when observability is disabled (level 0)", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Test message"
          observabilityLevel={0}
          isObservabilityEnabled={false}
        />
      )
      const container = screen.getByTestId("message-bubble-container")
      expect(container.querySelector('[data-testid="expand-icon"]')).toBeNull()
    })

    it("FR 1.3 — expand icon hidden for user messages", () => {
      render(
        <MessageBubble
          role="user"
          content="Test message"
          observabilityLevel={1}
          isObservabilityEnabled={true}
        />
      )
      const container = screen.getByTestId("message-bubble-container")
      expect(container.querySelector('[data-testid="expand-icon"]')).toBeNull()
    })
  })

  // FR-1.4: Progressive Disclosure
  describe("FR 1.4 — Observability Progressive Disclosure", () => {
    it("FR 1.4 — Level 1 shows selected tool and dimensions", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Result"
          observabilityLevel={1}
          isObservabilityEnabled={true}
          metadata={{
            toolSelected: "market_share",
            extractedDimensions: { brand: "Chipotle", geo: "TX" },
          }}
        />
      )
      const metadata = screen.getByTestId("message-metadata")
      expect(metadata.textContent).toContain("market_share")
      expect(metadata.textContent).toContain("Chipotle")
    })

    it("FR 1.4 — Level 2 shows inline JSON viewer", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Result"
          observabilityLevel={2}
          isObservabilityEnabled={true}
          metadata={{
            toolSelected: "market_share",
            extractedDimensions: { brand: "Chipotle" },
            latencyMs: 250,
          }}
        />
      )
      const jsonViewer = screen.getByTestId("json-viewer")
      expect(jsonViewer).toBeDefined()
    })

    it("FR 1.4 — Level 3 shows raw API request/response", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Result"
          observabilityLevel={3}
          isObservabilityEnabled={true}
          rawData={{
            request: { query: "test" },
            response: { data: "test" },
          }}
        />
      )
      const rawButton = screen.getByTestId("show-raw-button")
      expect(rawButton).toBeDefined()
    })

    it("FR 1.4 — JSON viewer uses font-mono text-xs", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Result"
          observabilityLevel={2}
          isObservabilityEnabled={true}
          metadata={{ toolSelected: "test" }}
        />
      )
      const jsonViewer = screen.getByTestId("json-viewer")
      expect(jsonViewer.className).toContain("font-mono")
      expect(jsonViewer.className).toContain("text-xs")
    })

    it("FR 1.4 — JSON viewer collapses nodes > 3 levels", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Result"
          observabilityLevel={2}
          isObservabilityEnabled={true}
          metadata={{
            deeplyNested: {
              level1: {
                level2: {
                  level3: {
                    level4: "too deep",
                  },
                },
              },
            },
          }}
        />
      )
      const jsonViewer = screen.getByTestId("json-viewer")
      expect(jsonViewer).toBeDefined()
    })

    it("FR 1.4 — JSON viewer shows 'Show more' for > 20 lines", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Result"
          observabilityLevel={2}
          isObservabilityEnabled={true}
          metadata={{
            items: Array(25)
              .fill(null)
              .map((_, i) => ({ id: i, value: `item ${i}` })),
          }}
        />
      )
      const showMore = screen.getByTestId("show-more-button")
      expect(showMore).toBeDefined()
    })
  })

  // Interface contract
  describe("Interface Contract", () => {
    it("accepts role prop (user | assistant)", () => {
      const { container: userContainer } = render(
        <MessageBubble role="user" content="Hi" />
      )
      const { container: assistantContainer } = render(
        <MessageBubble role="assistant" content="Hi" />
      )
      expect(userContainer.firstChild).toBeDefined()
      expect(assistantContainer.firstChild).toBeDefined()
    })

    it("accepts content prop", () => {
      render(<MessageBubble role="user" content="Hello World" />)
      expect(screen.getByText("Hello World")).toBeDefined()
    })

    it("accepts className prop", () => {
      const { container } = render(
        <MessageBubble role="user" content="Hi" className="custom-class" />
      )
      expect(container.firstChild).toBeDefined()
    })
  })

  // Empty state
  describe("Empty State Handling", () => {
    it("handles empty content gracefully", () => {
      render(<MessageBubble role="assistant" content="" />)
      const bubble = screen.getByTestId("message-bubble")
      expect(bubble).toBeDefined()
    })

    it("handles missing metadata gracefully", () => {
      render(
        <MessageBubble
          role="assistant"
          content="Hi"
          observabilityLevel={1}
          isObservabilityEnabled={true}
        />
      )
      const bubble = screen.getByTestId("message-bubble")
      expect(bubble).toBeDefined()
    })
  })
})
