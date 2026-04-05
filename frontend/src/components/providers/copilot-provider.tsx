"use client"

import { CopilotKit } from "@copilotkit/react-core"
import { useEffect, useState } from "react"

interface CopilotProviderProps {
  children: React.ReactNode
  selectedModel?: string
}

/**
 * CopilotProvider wraps the application with CopilotKit.
 *
 * @param children - The React children to render
 * @param selectedModel - The selected model ID for response generation (FR-1.5, FR-8.3)
 */
export function CopilotProvider({ children, selectedModel = "openai/gpt-4o" }: CopilotProviderProps) {
  const [model, setModel] = useState(selectedModel)

  // Update model when prop changes
  useEffect(() => {
    setModel(selectedModel)
  }, [selectedModel])

  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="chat_agent"
      // Pass the selected model to the backend via evalParams
      evalParams={{
        model: model,
      }}
    >
      {children}
    </CopilotKit>
  )
}