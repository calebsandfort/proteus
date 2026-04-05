import { describe, it, expect, vi, afterEach } from "vitest"
import { render, screen, cleanup, fireEvent } from "@testing-library/react"
import { ModelSelector, RESPONSE_GENERATION_MODELS, type ModelOption } from "./ModelSelector"

afterEach(() => {
  cleanup()
})

describe("ModelSelector", () => {
  // FR-1.5: Model Selector dropdown in header bar
  describe("FR 1.5 — Model Selector in Header", () => {
    it("FR 1.5 — renders model selector dropdown", () => {
      render(
        <ModelSelector
          selectedModelId="openai/gpt-4o"
          onModelChange={vi.fn()}
        />
      )
      const selector = screen.getByTestId("model-selector")
      expect(selector).toBeDefined()
    })

    it("FR 1.5 — displays current model name prominently", () => {
      render(
        <ModelSelector
          selectedModelId="openai/gpt-4o"
          onModelChange={vi.fn()}
        />
      )
      // Should show the current model name
      expect(screen.getByText("GPT-4o")).toBeDefined()
    })

    it("FR 1.5 — shows dropdown when clicked", () => {
      render(
        <ModelSelector
          selectedModelId="openai/gpt-4o"
          onModelChange={vi.fn()}
        />
      )
      const button = screen.getByTestId("model-selector-button")
      fireEvent.click(button)
      // Dropdown should now be visible
      expect(screen.getByTestId("model-dropdown")).toBeDefined()
    })
  })

  // FR-1.5: Display model names and provider logos
  describe("FR 1.5 — Model Names and Provider Logos", () => {
    it("FR 1.5 — displays all six model options", () => {
      render(
        <ModelSelector
          selectedModelId="openai/gpt-4o"
          onModelChange={vi.fn()}
        />
      )
      const button = screen.getByTestId("model-selector-button")
      fireEvent.click(button)

      // Check all models are in dropdown - use getAllByText since selected model appears in both button and dropdown
      expect(screen.getAllByText("GPT-4o").length).toBe(2)
      expect(screen.getAllByText("Gemini 2.0 Flash").length).toBe(1)
      expect(screen.getAllByText("Claude 3.5 Sonnet").length).toBe(1)
      expect(screen.getAllByText("Kimi K2").length).toBe(1)
      expect(screen.getAllByText("MiniMax Text-01").length).toBe(1)
      expect(screen.getAllByText("GLM-4-Pro").length).toBe(1)
    })

    it("FR 1.5 — displays provider indicator for each model", () => {
      render(
        <ModelSelector
          selectedModelId="openai/gpt-4o"
          onModelChange={vi.fn()}
        />
      )
      const button = screen.getByTestId("model-selector-button")
      fireEvent.click(button)

      // Provider indicators should exist
      const providerIndicators = screen.getAllByTestId("model-provider")
      expect(providerIndicators.length).toBeGreaterThan(0)
    })
  })

  // FR-1.5: Changes apply to subsequent queries
  describe("FR 1.5 — Model Selection Changes", () => {
    it("FR 1.5 — calls onModelChange with new model id when selected", () => {
      const handleChange = vi.fn()
      render(
        <ModelSelector
          selectedModelId="openai/gpt-4o"
          onModelChange={handleChange}
        />
      )
      const button = screen.getByTestId("model-selector-button")
      fireEvent.click(button)

      // Click on a different model
      const newModelOption = screen.getByTestId("model-option-anthropic/claude-3.5-sonnet")
      fireEvent.click(newModelOption)

      expect(handleChange).toHaveBeenCalledWith("anthropic/claude-3.5-sonnet")
    })

    it("FR 1.5 — updates display when selectedModelId changes", () => {
      const { rerender } = render(
        <ModelSelector
          selectedModelId="openai/gpt-4o"
          onModelChange={vi.fn()}
        />
      )
      expect(screen.getByTestId("model-selector-button")).toHaveTextContent("GPT-4o")

      rerender(
        <ModelSelector
          selectedModelId="google/gemini-2.0-flash"
          onModelChange={vi.fn()}
        />
      )
      expect(screen.getByTestId("model-selector-button")).toHaveTextContent("Gemini 2.0 Flash")
    })

    it("FR 1.5 — closes dropdown after selection", () => {
      render(
        <ModelSelector
          selectedModelId="openai/gpt-4o"
          onModelChange={vi.fn()}
        />
      )
      const button = screen.getByTestId("model-selector-button")
      fireEvent.click(button)

      // Select a model
      const modelOption = screen.getByTestId("model-option-google/gemini-2.0-flash")
      fireEvent.click(modelOption)

      // Dropdown should be closed
      expect(screen.queryByTestId("model-dropdown")).toBeNull()
    })
  })

  // FR-1.5: Model Option Interface
  describe("FR 1.5 — Model Option Interface", () => {
    it("FR 1.5 — RESPONSE_GENERATION_MODELS has six models", () => {
      expect(RESPONSE_GENERATION_MODELS).toHaveLength(6)
    })

    it("FR 1.5 — each model has required fields", () => {
      RESPONSE_GENERATION_MODELS.forEach((model) => {
        expect(model.id).toBeDefined()
        expect(model.provider).toBeDefined()
        expect(model.displayName).toBeDefined()
        expect(model.supportsFunctionCalling).toBeDefined()
      })
    })

    it("FR 1.5 — includes all six providers", () => {
      const providers = RESPONSE_GENERATION_MODELS.map((m) => m.provider)
      expect(providers).toContain("openai")
      expect(providers).toContain("google")
      expect(providers).toContain("anthropic")
      expect(providers).toContain("kimi")
      expect(providers).toContain("minimax")
      expect(providers).toContain("glm")
    })

    it("FR 1.5 — models include openai/gpt-4o with function calling", () => {
      const gpt4o = RESPONSE_GENERATION_MODELS.find((m) => m.id === "openai/gpt-4o")
      expect(gpt4o).toBeDefined()
      expect(gpt4o?.supportsFunctionCalling).toBe(true)
    })
  })
})

describe("ModelOption Interface", () => {
  it("FR 1.5 — ModelOption interface structure", () => {
    const model: ModelOption = {
      id: "test/model",
      provider: "openai",
      displayName: "Test Model",
      supportsFunctionCalling: true,
    }
    expect(model.id).toBe("test/model")
    expect(model.provider).toBe("openai")
    expect(model.displayName).toBe("Test Model")
    expect(model.supportsFunctionCalling).toBe(true)
  })
})