import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { StageIndicator } from "./StageIndicator"

describe("StageIndicator", () => {
  // FR-1.6: Loading and Feedback States
  describe("FR 1.6 — Stage Indicator (2-5s delay)", () => {
    const stages = [
      "Parsing query",
      "Retrieving tools",
      "Extracting dimensions",
      "Querying data",
      "Generating response",
    ]

    it("FR 1.6 — displays current pipeline stage name", () => {
      render(<StageIndicator stage="Extracting dimensions" />)
      expect(screen.getByText("Extracting dimensions")).toBeDefined()
    })

    it("FR 1.6 — displays all 5 stage names correctly", () => {
      stages.forEach((stage) => {
        const { unmount } = render(<StageIndicator stage={stage} />)
        expect(screen.getByText(stage)).toBeDefined()
        unmount()
      })
    })

    it("FR 1.6 — shows current stage as active/highlighted", () => {
      render(<StageIndicator stage="Querying data" />)
      const activeStage = screen.getByTestId("stage-active")
      expect(activeStage.textContent).toContain("Querying data")
    })

    it("FR 1.6 — shows completed stages differently", () => {
      render(<StageIndicator stage="Querying data" completedStages={["Parsing query", "Retrieving tools"]} />)
      const completedStages = screen.getAllByTestId("stage-completed")
      expect(completedStages.length).toBe(2)
    })

    it("FR 1.6 — accepts className prop", () => {
      const { container } = render(
        <StageIndicator stage="Parsing query" className="custom-class" />
      )
      expect(container.firstChild).toBeDefined()
    })
  })

  // Design system
  describe("Design System", () => {
    it("uses blue-600 for active stage", () => {
      render(<StageIndicator stage="Extracting dimensions" />)
      const activeStage = screen.getByTestId("stage-active")
      expect(activeStage.className).toContain("text-blue-600")
    })

    it("uses muted styling for completed stages", () => {
      render(<StageIndicator stage="Querying data" completedStages={["Parsing query"]} />)
      const completed = screen.getByTestId("stage-completed")
      expect(completed.className).toContain("text-slate-400")
    })
  })

  // Edge cases
  describe("Edge Cases", () => {
    it("handles empty completedStages", () => {
      render(<StageIndicator stage="Parsing query" completedStages={[]} />)
      const completed = screen.getAllByTestId("stage-completed")
      expect(completed.length).toBe(0)
    })

    it("handles all stages completed except current", () => {
      render(
        <StageIndicator
          stage="Generating response"
          completedStages={[
            "Parsing query",
            "Retrieving tools",
            "Extracting dimensions",
            "Querying data",
          ]}
        />
      )
      const completed = screen.getAllByTestId("stage-completed")
      expect(completed.length).toBe(4)
    })
  })
})
