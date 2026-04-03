"""NFR-1.4: SSE Streaming Handler for Response Generation.

This module implements Server-Sent Events (SSE) streaming for the Proteus agent,
allowing real-time streaming of response tokens with observability metadata.

NFR Requirements:
- NFR-1.4: Streaming
  - Implement streaming for response generation via Server-Sent Events (SSE)
  - First token SHALL appear within 500ms of pipeline completion

SSE Event Types:
- SSEToolResult: event="tool_result", data=ToolResult
- SSEClarification: event="clarification", data=HITLClarification
- SSEStreamChunk: event="stream", data=str (token chunk)
- SSEDone: event="done", data=ObservabilityMetadata

Architecture:
- StreamingResponseBuilder: Formats events as SSE
- SSEEventFormatter: Formats individual SSE events
- ObservabilityMetadata: Metadata for done event
- create_streaming_response: FastAPI endpoint response factory
- stream_agent_response: Main streaming generator
"""

import asyncio
import inspect
import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agent.context import ToolResult
from src.agent.nodes import HITLClarification


# ============================================================================
# NFR-1.4: Pydantic Models for Streaming
# ============================================================================


class ObservabilityMetadata(BaseModel):
    """Observability metadata sent with the done event.

    NFR-1.4: Contains pipeline stage timing and first token latency
    to verify the 500ms first token requirement.

    Attributes:
        total_latency_ms: Total end-to-end latency in milliseconds.
        pipeline_stages: Timing for each pipeline stage.
        first_token_latency_ms: Time from pipeline completion to first token.
        session_id: Session identifier for correlation.
        error: Optional error message if pipeline failed.
    """

    model_config = {"from_attributes": True}

    total_latency_ms: int = Field(
        ...,
        ge=0,
        description="Total end-to-end latency in milliseconds"
    )
    pipeline_stages: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Timing for each pipeline stage: {stage_name: {latency_ms, stage}}"
    )
    first_token_latency_ms: int = Field(
        ...,
        ge=0,
        description="Time from pipeline completion to first token in milliseconds"
    )
    session_id: str = Field(
        ...,
        description="Session identifier for correlation"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if pipeline failed"
    )


# ============================================================================
# NFR-1.4: SSE Event Formatter
# ============================================================================


class SSEEventFormatter:
    """Formats events as Server-Sent Events (SSE).

    SSE Format: event: <type>\ndata: <json>\n\n

    Attributes:
        json_serializer: Custom JSON serializer function.
    """

    def __init__(self, json_serializer: Optional[callable] = None):
        """Initialize SSE event formatter.

        Args:
            json_serializer: Optional custom JSON serializer.
                              Defaults to json.dumps with default handler.
        """
        self.json_serializer = json_serializer or (lambda x: json.dumps(x, default=str, separators=(",", ":")))

    def format_event(
        self,
        event_type: str,
        data: Union[Dict[str, Any], str, ToolResult, HITLClarification, ObservabilityMetadata],
    ) -> str:
        """Format an event as SSE string.

        NFR-1.4: SSE events follow format: event: <type>\ndata: <json>\n\n

        Args:
            event_type: The SSE event type (stream, tool_result, clarification, done).
            data: The event data (will be serialized to JSON).

        Returns:
            Formatted SSE string with proper line endings.
        """
        # Serialize data to JSON
        if isinstance(data, (ToolResult, HITLClarification, ObservabilityMetadata)):
            # Pydantic models have model_dump
            data_str = data.model_dump_json() if hasattr(data, "model_dump_json") else json.dumps(data)
        elif isinstance(data, dict):
            data_str = self.json_serializer(data)
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = self.json_serializer(data)

        # Format as SSE: event: <type>\ndata: <json>\n\n
        return f"event: {event_type}\ndata: {data_str}\n\n"


# ============================================================================
# NFR-1.4: Streaming Response Builder
# ============================================================================


class StreamingResponseBuilder:
    """Builds SSE stream from agent response events.

    Converts agent events into properly formatted SSE messages
    that can be streamed to the client.
    """

    def __init__(self):
        """Initialize streaming response builder."""
        self.formatter = SSEEventFormatter()

    def build_sse_events(
        self,
        events: Union[List[Dict[str, Any]], AsyncGenerator[Dict[str, Any], None]],
    ) -> AsyncGenerator[str, None]:
        """Build SSE formatted events from agent response.

        Args:
            events: List or async generator of events from agent.

        Yields:
            Properly formatted SSE strings.
        """
        return self._generate_sse(events)

    async def _generate_sse(
        self,
        events: Union[List[Dict[str, Any]], AsyncGenerator[Dict[str, Any], None]],
    ) -> AsyncGenerator[str, None]:
        """Internal async generator for SSE formatting.

        Args:
            events: List or async generator of events.

        Yields:
            Formatted SSE strings.
        """
        if inspect.isasyncgen(events):
            # Async generator
            async for event in events:
                yield self._format_single_event(event)
        else:
            # Regular iterator
            for event in events:
                yield self._format_single_event(event)

    def _format_single_event(self, event: Dict[str, Any]) -> str:
        """Format a single event dict as SSE.

        Args:
            event: Event dict with 'event' and 'data' keys.

        Returns:
            Formatted SSE string.
        """
        event_type = event.get("event", "stream")
        data = event.get("data", {})

        return self.formatter.format_event(event_type, data)


# ============================================================================
# NFR-1.4: Main Streaming Functions
# ============================================================================


async def stream_agent_response(
    query: str,
    session_id: str,
    conversation_history: List[Dict[str, Any]],
    selected_model: str = "openai/gpt-4o",
) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream agent response events from the agent graph.

    This function wraps the agent graph execution and yields events
    as they occur, enabling real-time streaming to the client.

    NFR-1.4: First token SHALL appear within 500ms of pipeline completion.

    Args:
        query: The user query string.
        session_id: Session identifier for tracking.
        conversation_history: List of conversation history dicts.
        selected_model: Model ID for response generation (FR-8.3).

    Yields:
        Event dicts with 'event' and 'data' keys.
    """
    # Import here to avoid circular imports
    from src.agent.graph import run_agent_graph

    pipeline_start_time = time.perf_counter()
    first_token_time: Optional[float] = None
    pipeline_stages: Dict[str, Dict[str, Any]] = {}

    try:
        # Run the agent graph and stream events
        result = await run_agent_graph(
            query=query,
            session_id=session_id,
            conversation_history=conversation_history,
        )

        # Track when pipeline "completes" (before streaming response)
        pipeline_complete_time = time.perf_counter()

        # Check if result is a generator or a dict
        if asyncio.iscoroutine(result):
            result = await result

        if hasattr(result, "__aiter__"):
            # Streaming result from agent
            async for event in result:
                # Track first token time
                if first_token_time is None and event.get("event") == "stream":
                    first_token_time = time.perf_counter() - pipeline_complete_time

                yield event
        else:
            # Non-streaming result, emit as done
            total_time = int((time.perf_counter() - pipeline_start_time) * 1000)
            first_token_latency = int(first_token_time * 1000) if first_token_time else total_time

            yield {
                "event": "done",
                "data": ObservabilityMetadata(
                    total_latency_ms=total_time,
                    pipeline_stages=pipeline_stages,
                    first_token_latency_ms=first_token_latency,
                    session_id=session_id,
                ).model_dump(),
            }

    except Exception as e:
        # Emit error in done event
        total_time = int((time.perf_counter() - pipeline_start_time) * 1000)
        first_token_latency = int(first_token_time * 1000) if first_token_time else total_time

        yield {
            "event": "done",
            "data": ObservabilityMetadata(
                total_latency_ms=total_time,
                pipeline_stages=pipeline_stages,
                first_token_latency_ms=first_token_latency,
                session_id=session_id,
                error=str(e),
            ).model_dump(),
        }


async def create_streaming_response(
    query: str,
    session_id: str,
    conversation_history: List[Dict[str, Any]],
    selected_model: str = "openai/gpt-4o",
) -> StreamingResponse:
    """Create a FastAPI StreamingResponse for SSE streaming.

    NFR-1.4: Uses text/event-stream content type for SSE.

    Args:
        query: The user query string.
        session_id: Session identifier for tracking.
        conversation_history: List of conversation history dicts.
        selected_model: Model ID for response generation (FR-8.3).

    Returns:
        FastAPI StreamingResponse with text/event-stream content type.
    """
    builder = StreamingResponseBuilder()

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE formatted events for the response stream."""
        async for event in stream_agent_response(
            query=query,
            session_id=session_id,
            conversation_history=conversation_history,
            selected_model=selected_model,
        ):
            # Format as SSE
            event_type = event.get("event", "stream")
            data = event.get("data", {})

            # Handle ToolResult and HITLClarification serialization
            if isinstance(data, ToolResult):
                data = data.model_dump()
            elif hasattr(data, "model_dump"):
                data = data.model_dump()

            formatted = SSEEventFormatter().format_event(event_type, data)
            yield formatted

    return StreamingResponse(
        content=event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ============================================================================
# NFR-1.4: Token Streaming Helper
# ============================================================================


async def stream_tokens_from_response(
    response_text: str,
    chunk_size: int = 4,
) -> AsyncGenerator[str, None]:
    """Stream text response as token chunks.

    Helper function to stream a complete response text as smaller
    token chunks for a more natural streaming experience.

    Args:
        response_text: The complete response text.
        chunk_size: Size of each token chunk in words/characters.

    Yields:
        Token chunks as strings.
    """
    words = response_text.split()

    # Stream in word chunks
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            yield chunk

    # Ensure we always end with a done event marker
    yield ""


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "ObservabilityMetadata",
    "SSEEventFormatter",
    "StreamingResponseBuilder",
    "create_streaming_response",
    "stream_agent_response",
    "stream_tokens_from_response",
]
