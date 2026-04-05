import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime"
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph"
import { NextRequest } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000"

/**
 * Creates a configured LangGraphHttpAgent with the selected model.
 *
 * @param model - The selected model ID (e.g., "openai/gpt-4o")
 */
function createChatAgent(model?: string) {
  return new LangGraphHttpAgent({
    url: `${BACKEND_URL}/copilotkit`,
    // Pass the model to the backend via headers
    headers: model ? { "x-model": model } : undefined,
  })
}

const runtime = new CopilotRuntime({
  agents: {
    chat_agent: createChatAgent(),
  } as any,
})

/**
 * POST handler for CopilotKit proxy.
 *
 * Extracts the selected model from request body (via evalParams from CopilotKit/react)
 * and passes it to the backend via headers.
 */
export const POST = async (req: NextRequest) => {
  // Parse the request body to get the model
  let model: string | undefined
  try {
    const body = await req.json()
    // CopilotKit passes evalParams in the message
    if (body?.evalParams?.model) {
      model = body.evalParams.model
    }
  } catch {
    // Body may not be parseable or may be empty; use defaults
  }

  // Update the agent with the model from request
  const agent = createChatAgent(model)
  const runtimeWithModel = new CopilotRuntime({
    agents: {
      chat_agent: agent,
    } as any,
  })

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: runtimeWithModel,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  })
  return handleRequest(req)
}

export const GET = async (_req: NextRequest) => {
  // Return a simple health check response
  return new Response(JSON.stringify({ status: "ok" }), {
    headers: { "Content-Type": "application/json" },
  })
}