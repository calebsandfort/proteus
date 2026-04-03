from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agent.streaming import create_streaming_response
from src.api.health import router as health_router


# ============================================================================
# CopilotKit Request/Response Models (FR-1.2, FR-8.3, NFR-1.4)
# ============================================================================


class ChatMessage(BaseModel):
    """Chat message in multi-turn conversation.

    FR-1.2: Each message has role and content for multi-turn context.

    Attributes:
        role: Message sender role ("user" or "assistant").
        content: Message content string.
    """

    model_config = {"from_attributes": True}

    role: Literal["user", "assistant"] = Field(
        ...,
        description="Role of the message sender"
    )
    content: str = Field(
        ...,
        description="Message content"
    )


class CopilotKitRequest(BaseModel):
    """Request body for CopilotKit endpoint.

    FR-1.2: Multi-turn conversation with messages array.
    FR-8.3: Model selection from request.

    Attributes:
        messages: List of conversation messages (multi-turn context).
        session_id: Session identifier for tracking.
        selected_model: Model ID for response generation.
    """

    model_config = {"from_attributes": True}

    messages: List[ChatMessage] = Field(
        ...,
        description="List of conversation messages for multi-turn context"
    )
    session_id: str = Field(
        ...,
        description="Session identifier for tracking"
    )
    selected_model: str = Field(
        ...,
        description="Selected model ID for response generation (FR-8.3)"
    )


# ============================================================================
# CopilotKit Router (FR-1.2, FR-8.3, NFR-1.4)
# ============================================================================


api_router = APIRouter()


@api_router.post(
    "/copilotkit",
    response_model=None,
    summary="CopilotKit Agent Endpoint",
    description="Multi-turn conversation endpoint with SSE streaming response",
)
async def copilotkit_endpoint(request: CopilotKitRequest) -> StreamingResponse:
    """Handle CopilotKit agent requests with SSE streaming.

    FR-1.2: Multi-Turn Conversation - receives multi-turn context via messages array.
    FR-8.3: Response Generation Model - uses selected_model from request.
    NFR-1.4: Streaming - returns SSE stream of SSEToolResult | SSEClarification | SSEStreamChunk | SSEDone.

    Args:
        request: CopilotKitRequest with messages, session_id, and selected_model.

    Returns:
        StreamingResponse with text/event-stream content type.

    SSE Event Types:
        - stream: Token chunks with { token: str }
        - tool_result: Tool results with referenceId, toolName, dimensions, data, timestamp
        - clarification: HITL clarification requests
        - done: Final event with ObservabilityMetadata
    """
    # Extract the query from the last user message
    query = ""
    conversation_history: List[Dict[str, Any]] = []

    for msg in request.messages:
        if msg.role == "user":
            query = msg.content
        conversation_history.append({"role": msg.role, "content": msg.content})

    # If no query found, use the last message content
    if not query and request.messages:
        query = request.messages[-1].content

    # Create streaming response with selected model
    return await create_streaming_response(
        query=query,
        session_id=request.session_id,
        conversation_history=conversation_history,
        selected_model=request.selected_model,
    )


# Note: health_router is now registered directly in main.py without prefix
