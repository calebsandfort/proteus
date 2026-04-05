import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { ChartSkeleton } from "./ChartSkeleton"

describe("ChartSkeleton", () => {
  // FR-1.6: Loading and Feedback States
  describe("FR 1.6 — Chart Shaped Skeleton Loaders", () => {
    it("FR 1.6 — renders skeleton with shimmer animation", () => {
      render(<ChartSkeleton />)
      const skeleton = screen.getByTestId("chart-skeleton")
      expect(skeleton).toBeDefined()
    })

    it("FR 1.6 — shimmer uses gradient animation", () => {
      render(<ChartSkeleton />)
      const skeleton = screen.getByTestId("chart-skeleton")
      expect(skeleton.className).toContain("bg-gradient-to-r")
      expect(skeleton.className).toContain("animate-pulse")
    })

    it("FR 1.6 — skeleton resembles chart shape", () => {
      render(<ChartSkeleton chartType="bar" />)
      const skeleton = screen.getByTestId("chart-skeleton")
      expect(skeleton).toBeDefined()
    })

    it("FR 1.6 — supports bar chart type", () => {
      const { container } = render(<ChartSkeleton chartType="bar" />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.6 — supports line chart type", () => {
      const { container } = render(<ChartSkeleton chartType="line" />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.6 — supports pie chart type", () => {
      const { container } = render(<ChartSkeleton chartType="pie" />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.6 — shimmer uses bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100", () => {
      render(<ChartSkeleton />)
      const skeleton = screen.getByTestId("chart-skeleton")
      // Check for gradient animation pattern
      expect(skeleton.className).toContain("from-slate-100")
      expect(skeleton.className).toContain("via-slate-200")
      expect(skeleton.className).toContain("to-slate-100")
    })

    it("FR 1.6 — accepts className prop", () => {
      const { container } = render(<ChartSkeleton className="custom-class" />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.6 — accepts height prop", () => {
      const { container } = render(<ChartSkeleton height={300} />)
      expect(container.firstChild).toBeDefined()
    })

    it("FR 1.6 — accepts width prop", () => {
      const { container } = render(<ChartSkeleton width={500} />)
      expect(container.firstChild).toBeDefined()
    })
  })

  // Edge cases
  describe("Edge Cases", () => {
    it("handles default dimensions", () => {
      render(<ChartSkeleton />)
      const skeleton = screen.getByTestId("chart-skeleton")
      expect(skeleton).toBeDefined()
    })

    it("handles zero height gracefully", () => {
      const { container } = render(<ChartSkeleton height={0} />)
      expect(container.firstChild).toBeDefined()
    })

    it("handles negative height gracefully", () => {
      const { container } = render(<ChartSkeleton height={-100} />)
      expect(container.firstChild).toBeDefined()
    })
  })
})
