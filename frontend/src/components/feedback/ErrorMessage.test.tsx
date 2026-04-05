import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { ErrorMessage } from "./ErrorMessage"

describe("ErrorMessage", () => {
  // FR-1.7: Error Handling
  describe("FR 1.7 — Error Handling", () => {
    it("FR 1.7 — displays error message with text-red-600", () => {
      render(<ErrorMessage message="Something went wrong" />)
      const errorEl = screen.getByTestId("error-message")
      expect(errorEl).toBeDefined()
      expect(errorEl.className).toContain("text-red-600")
    })

    it("FR 1.7 — displays error icon", () => {
      render(<ErrorMessage message="Error occurred" />)
      expect(screen.getByTestId("error-icon")).toBeDefined()
    })

    it("FR 1.7 — displays the error message text", () => {
      render(<ErrorMessage message="API request failed" />)
      expect(screen.getByText("API request failed")).toBeDefined()
    })

    it("FR 1.7 — shows 'Try adjusting: [specific dimension]' suggestion when applicable", () => {
      render(
        <ErrorMessage
          message="Invalid query"
          suggestion="Try adjusting: time period"
        />
      )
      expect(screen.getByText(/Try adjusting:/)).toBeDefined()
      expect(screen.getByText("Try adjusting: time period")).toBeDefined()
    })

    it("FR 1.7 — does not show suggestion when not provided", () => {
      render(<ErrorMessage message="Error occurred" />)
      expect(screen.queryByText(/Try adjusting:/)).toBeNull()
    })

    it("FR 1.7 — accepts onRetry callback", () => {
      const handleRetry = vi.fn()
      render(<ErrorMessage message="Failed" onRetry={handleRetry} />)
      const retryButton = screen.getByTestId("retry-button")
      fireEvent.click(retryButton)
      expect(handleRetry).toHaveBeenCalled()
    })

    it("FR 1.7 — does not show retry button when onRetry not provided", () => {
      render(<ErrorMessage message="Failed" />)
      expect(screen.queryByTestId("retry-button")).toBeNull()
    })
  })

  // FR-1.7: Rate Limit Handling
  describe("FR 1.7 — Rate Limit (429) Countdown", () => {
    it("FR 1.7 — shows countdown timer for rate limit errors", () => {
      render(<ErrorMessage message="Rate limit exceeded" isRateLimit={true} retryAfter={30} />)
      expect(screen.getByTestId("rate-limit-countdown")).toBeDefined()
    })

    it("FR 1.7 — displays retry-after seconds", () => {
      render(<ErrorMessage message="Rate limit" isRateLimit={true} retryAfter={60} />)
      expect(screen.getByText(/60.*seconds/i)).toBeDefined()
    })

    it("FR 1.7 — countdown displays seconds remaining", () => {
      render(<ErrorMessage message="Rate limit" isRateLimit={true} retryAfter={30} />)
      const countdown = screen.getByTestId("rate-limit-countdown")
      expect(countdown.textContent).toContain("30")
    })

    it("FR 1.7 — does not show rate limit UI for non-rate-limit errors", () => {
      render(<ErrorMessage message="Regular error" isRateLimit={false} />)
      expect(screen.queryByTestId("rate-limit-countdown")).toBeNull()
    })
  })

  // FR-1.7: Session Timeout
  describe("FR 1.7 — Session Timeout Banner", () => {
    it("FR 1.7 — shows inline banner for session timeout (not modal)", () => {
      render(<ErrorMessage message="Session expired" isSessionTimeout={true} />)
      const banner = screen.getByTestId("error-banner")
      expect(banner).toBeDefined()
    })

    it("FR 1.7 — does not block input during session timeout", () => {
      render(<ErrorMessage message="Session expired" isSessionTimeout={true} />)
      const banner = screen.getByTestId("error-banner")
      expect(banner.getAttribute("data-blocking")).toBeNull()
    })

    it("FR 1.7 — session timeout is inline (not a modal overlay)", () => {
      const { container } = render(
        <ErrorMessage message="Session expired" isSessionTimeout={true} />
      )
      // Should not have a modal overlay
      expect(container.querySelector("[data-modal]")).toBeNull()
    })

    it("FR 1.7 — shows 30 min recovery time for session timeout", () => {
      render(<ErrorMessage message="Session expired" isSessionTimeout={true} />)
      expect(screen.getByText(/30.*min/i)).toBeDefined()
    })
  })

  // Interface contract
  describe("Interface Contract", () => {
    it("accepts message prop", () => {
      const { container } = render(<ErrorMessage message="Test error" />)
      expect(container.firstChild).toBeDefined()
    })

    it("accepts className prop", () => {
      const { container } = render(
        <ErrorMessage message="Test" className="custom-class" />
      )
      expect(container.firstChild).toBeDefined()
    })
  })

  // Edge cases
  describe("Edge Cases", () => {
    it("handles empty message gracefully", () => {
      const { container } = render(<ErrorMessage message="" />)
      expect(container.firstChild).toBeDefined()
    })

    it("handles very long error messages", () => {
      const longMessage = "Error: " + "x".repeat(500)
      render(<ErrorMessage message={longMessage} />)
      expect(screen.getByTestId("error-message")).toBeDefined()
    })

    it("handles zero retryAfter", () => {
      render(<ErrorMessage message="Rate limit" isRateLimit={true} retryAfter={0} />)
      expect(screen.getByTestId("rate-limit-countdown")).toBeDefined()
    })
  })
})
