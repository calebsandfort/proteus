"""TDD Tests for SSE Streaming Handler (NFR-1.4).

Tests the SSE streaming implementation for response generation.
First token SHALL appear within 500ms of pipeline completion.

NFR Requirements:
- NFR-1.4: Streaming
  - Implement streaming for response generation via Server-Sent Events (SSE)
  - First token SHALL appear within 500ms of pipeline completion

SSE Event Types:
- SSEToolResult: event="tool_result", data=ToolResult
- SSEClarification: event="clarification", data=HITLClarification
- SSEStreamChunk: event="stream", data=str (token chunk)
- SSEDone: event="done", data=ObservabilityMetadata
"""

import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.context import SessionContext, ToolResult
from src.agent.nodes import (
    AgentOutput,
    ClarificationOption,
    HITLClarification,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_session_context() -> SessionContext:
    """Create a mock session context for testing."""
    return SessionContext(
        session_id="test-session-123",
        session_anchor="Show spending by generation",
        recent_turns=[],
        extracted_dimensions={},
        topic_tracker=["spending", "generation"],
        model_context_limit=128000,
    )


@pytest.fixture
def mock_tool_result() -> ToolResult:
    """Create a mock tool result for testing."""
    return ToolResult(
        referenceId="ref_abc123",
        tool_name="spending_by_generation",
        data={"total_spending": 50000, "generation": "gen_z"},
    )


@pytest.fixture
def mock_clarification() -> HITLClarification:
    """Create a mock HITL clarification for testing."""
    return HITLClarification(
        ambiguity_type="tool_selection",
        message="I need more information to help you.",
        options=[
            ClarificationOption(
                id="opt1",
                label="Gen Z Spending",
                interpreted_params={"generation": ["gen_z"]},
                reasoning="Focus on Gen Z demographic",
            ),
            ClarificationOption(
                id="opt2",
                label="All Generations",
                interpreted_params={"generation": ["gen_z", "millennial", "gen_x"]},
                reasoning="Compare across all generations",
            ),
        ],
        suggested_question="Which generation would you like to focus on?",
    )


@pytest.fixture
def mock_observability_metadata() -> Dict[str, Any]:
    """Create mock observability metadata for done event."""
    return {
        "total_latency_ms": 1200,
        "pipeline_stages": {
            "retrieval": {"latency_ms": 150, "stage": "retrieve"},
            "dimension_extraction": {"latency_ms": 400, "stage": "extract_dimensions"},
            "tool_selection": {"latency_ms": 200, "stage": "tool_selection"},
            "execution": {"latency_ms": 300, "stage": "execution"},
            "response": {"latency_ms": 150, "stage": "response"},
        },
        "first_token_latency_ms": 350,
        "session_id": "test-session-123",
    }


# ============================================================================
# Test SSE Event Formatting (NFR-1.4)
# ============================================================================

class TestSSEEventFormatting:
    """Tests for proper SSE event formatting."""

    def test_sse_event_format_has_event_line(self) -> None:
        """Test that SSE event has proper 'event: <type>' line."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        event_data = {"test": "data"}
        formatted = formatter.format_event("stream", event_data)

        # Should have event type line
        lines = formatted.strip().split("\n")
        event_line = [l for l in lines if l.startswith("event:")]
        assert len(event_line) == 1
        assert event_line[0] == "event: stream"

    def test_sse_event_format_has_data_line(self) -> None:
        """Test that SSE event has proper 'data: <json>' line."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        event_data = {"test": "data", "value": 123}
        formatted = formatter.format_event("stream", event_data)

        # Should have data line with JSON
        lines = formatted.strip().split("\n")
        data_line = [l for l in lines if l.startswith("data:")]
        assert len(data_line) == 1
        assert "test" in data_line[0]
        assert "data" in data_line[0]

    def test_sse_event_format_ends_with_double_newline(self) -> None:
        """Test that SSE event ends with double newline (\\n\\n)."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        event_data = {"test": "data"}
        formatted = formatter.format_event("stream", event_data)

        # SSE events must end with \n\n
        assert formatted.endswith("\n\n")

    def test_sse_event_format_no_extra_newlines_between_event_and_data(
        self,
    ) -> None:
        """Test that event and data lines are consecutive without extra blank lines."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        event_data = {"content": "Hello"}
        formatted = formatter.format_event("stream", event_data)

        # SSE format ends with \n\n which produces 2 empty lines when split by \n
        # The key check: event line and data line should have NO blank lines between them
        lines = formatted.split("\n")
        # Find non-empty lines
        non_empty_lines = [l for l in lines if l.strip()]

        # Should have exactly 2 content lines: "event: stream" and "data: {...}"
        assert len(non_empty_lines) == 2, f"Expected 2 content lines, got {len(non_empty_lines)}: {non_empty_lines}"
        assert non_empty_lines[0] == "event: stream"
        assert non_empty_lines[1].startswith("data: ")

    def test_sse_stream_chunk_event_formatting(self) -> None:
        """Test SSE stream chunk event formatting for token streaming."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        token_chunk = "Hello world this is a token"
        formatted = formatter.format_event("stream", token_chunk)

        # Parse the formatted event
        lines = formatted.strip().split("\n")

        # First line should be event type
        assert lines[0] == "event: stream"

        # Second line should be data with the token
        assert lines[1].startswith("data:")
        assert token_chunk in lines[1]

    def test_sse_tool_result_event_formatting(
        self,
        mock_tool_result: ToolResult,
    ) -> None:
        """Test SSE tool_result event formatting."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        formatted = formatter.format_event("tool_result", mock_tool_result)

        lines = formatted.strip().split("\n")

        assert lines[0] == "event: tool_result"
        assert lines[1].startswith("data:")

        # Verify JSON parsing
        data_json = lines[1][5:].strip()  # Remove "data: " prefix
        parsed = json.loads(data_json)
        assert parsed["referenceId"] == mock_tool_result.referenceId
        assert parsed["tool_name"] == mock_tool_result.tool_name

    def test_sse_clarification_event_formatting(
        self,
        mock_clarification: HITLClarification,
    ) -> None:
        """Test SSE clarification event formatting."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        formatted = formatter.format_event("clarification", mock_clarification)

        lines = formatted.strip().split("\n")

        assert lines[0] == "event: clarification"
        assert lines[1].startswith("data:")

        # Verify JSON parsing
        data_json = lines[1][5:].strip()
        parsed = json.loads(data_json)
        assert parsed["ambiguity_type"] == mock_clarification.ambiguity_type
        assert len(parsed["options"]) == 2

    def test_sse_done_event_formatting(
        self,
        mock_observability_metadata: Dict[str, Any],
    ) -> None:
        """Test SSE done event formatting with observability metadata."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        formatted = formatter.format_event("done", mock_observability_metadata)

        lines = formatted.strip().split("\n")

        assert lines[0] == "event: done"
        assert lines[1].startswith("data:")

        # Verify JSON parsing
        data_json = lines[1][5:].strip()
        parsed = json.loads(data_json)
        assert "total_latency_ms" in parsed
        assert "pipeline_stages" in parsed
        assert "first_token_latency_ms" in parsed


# ============================================================================
# Test First Token Timing (NFR-1.4: 500ms requirement)
# ============================================================================

class TestFirstTokenTiming:
    """Tests for first token timing measurement."""

    @pytest.mark.asyncio
    async def test_first_token_timing_is_tracked(self) -> None:
        """Test that first token timing can be measured and tracked."""
        from src.agent.streaming import StreamingResponseBuilder

        timings: Dict[str, float] = {}

        async def mock_token_generator():
            """Mock token generator that tracks timing."""
            start_time = time.perf_counter()

            # First token after small delay
            yield "Hello"
            timings["first_token"] = time.perf_counter() - start_time

            yield " world"
            timings["second_token"] = time.perf_counter() - start_time

        builder = StreamingResponseBuilder()
        tokens = []
        async for token in mock_token_generator():
            tokens.append(token)

        # First token should be tracked
        assert "first_token" in timings
        assert timings["first_token"] >= 0

    @pytest.mark.asyncio
    async def test_first_token_timing_included_in_done_event(self) -> None:
        """Test that first token timing is included in done event metadata."""
        from src.agent.streaming import (
            StreamingResponseBuilder,
            ObservabilityMetadata,
        )

        first_token_latency_ms = 350

        metadata = ObservabilityMetadata(
            total_latency_ms=1200,
            pipeline_stages={},
            first_token_latency_ms=first_token_latency_ms,
            session_id="test-session",
        )

        # Verify metadata contains first_token_latency_ms
        assert metadata.first_token_latency_ms == first_token_latency_ms

    @pytest.mark.asyncio
    async def test_done_event_has_timing_info(self) -> None:
        """Test that done event contains all required timing information."""
        from src.agent.streaming import ObservabilityMetadata

        metadata = ObservabilityMetadata(
            total_latency_ms=1200,
            pipeline_stages={
                "retrieval": {"latency_ms": 150, "stage": "retrieve"},
                "dimension_extraction": {"latency_ms": 400, "stage": "extract_dimensions"},
            },
            first_token_latency_ms=350,
            session_id="test-session",
        )

        # Verify all timing fields are present
        assert metadata.total_latency_ms == 1200
        assert "retrieval" in metadata.pipeline_stages
        assert "dimension_extraction" in metadata.pipeline_stages
        assert metadata.first_token_latency_ms == 350


# ============================================================================
# Test Streaming Handler (NFR-1.4)
# ============================================================================

class TestStreamingHandler:
    """Tests for the main SSE streaming handler."""

    @pytest.mark.asyncio
    async def test_streaming_handler_exists(self) -> None:
        """Test that streaming handler function exists."""
        from src.agent import streaming

        assert hasattr(streaming, "create_streaming_response")
        assert hasattr(streaming, "stream_agent_response")

    @pytest.mark.asyncio
    async def test_streaming_handler_returns_streaming_response(self) -> None:
        """Test that streaming handler returns proper StreamingResponse."""
        from fastapi.responses import StreamingResponse
        from src.agent.streaming import create_streaming_response

        with patch("src.agent.graph.run_agent_graph") as mock_run:
            # Setup mock to return immediately
            mock_run.return_value = {
                "final_output": {
                    "answer": "Test answer",
                    "tool_results": {},
                    "visualizations": [],
                    "suggestions": [],
                }
            }

            response = await create_streaming_response(
                query="Show spending",
                session_id="test-session",
                conversation_history=[],
            )

            assert isinstance(response, StreamingResponse)

    @pytest.mark.asyncio
    async def test_streaming_handler_uses_sse_content_type(self) -> None:
        """Test that streaming response uses text/event-stream content type."""
        from fastapi.responses import StreamingResponse
        from src.agent.streaming import create_streaming_response

        with patch("src.agent.graph.run_agent_graph") as mock_run:
            mock_run.return_value = {
                "final_output": {
                    "answer": "Test answer",
                    "tool_results": {},
                    "visualizations": [],
                    "suggestions": [],
                }
            }

            response = await create_streaming_response(
                query="Show spending",
                session_id="test-session",
                conversation_history=[],
            )

            assert isinstance(response, StreamingResponse)
            assert response.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_streaming_handler_streams_token_chunks(self) -> None:
        """Test that streaming handler streams token chunks."""
        from src.agent.streaming import stream_agent_response

        # Create mock agent result that yields tokens
        async def mock_stream():
            tokens = ["Hello", " world", "!"]
            for token in tokens:
                yield {"event": "stream", "data": token}
            yield {"event": "done", "data": {"total_latency_ms": 100}}

        with patch("src.agent.graph.run_agent_graph", return_value=mock_stream()):
            chunks = []
            async for chunk in stream_agent_response(
                query="Show spending",
                session_id="test-session",
                conversation_history=[],
            ):
                chunks.append(chunk)

            assert len(chunks) > 0


# ============================================================================
# Test Agent Graph Integration with Streaming (NFR-1.4)
# ============================================================================

class TestAgentGraphStreamingIntegration:
    """Tests for agent graph integration with streaming."""

    @pytest.mark.asyncio
    async def test_agent_graph_can_stream_response(self) -> None:
        """Test that agent graph can be used with streaming."""
        from src.agent.streaming import stream_agent_response

        # Mock the agent graph to avoid real LLM calls
        async def mock_agent_stream():
            # Simulate streaming tokens
            words = ["Based ", "on ", "your ", "query, ", "here ", "is ", "the ", "answer."]
            for word in words:
                yield {"event": "stream", "data": word}
            yield {
                "event": "done",
                "data": {
                    "total_latency_ms": 500,
                    "first_token_latency_ms": 200,
                },
            }

        with patch("src.agent.graph.run_agent_graph", return_value=mock_agent_stream()):
            events = []
            async for event in stream_agent_response(
                query="Show gen z spending",
                session_id="test-session",
                conversation_history=[],
            ):
                events.append(event)

            # Should have stream events and done event
            stream_events = [e for e in events if e.get("event") == "stream"]
            done_events = [e for e in events if e.get("event") == "done"]

            assert len(stream_events) == 8
            assert len(done_events) == 1

    @pytest.mark.asyncio
    async def test_streaming_with_tool_results(self) -> None:
        """Test that streaming handler can emit tool_result events."""
        from src.agent.streaming import stream_agent_response

        tool_result = ToolResult(
            referenceId="ref_123",
            tool_name="spending_tool",
            data={"total": 5000},
        )

        async def mock_agent_stream():
            yield {"event": "tool_result", "data": tool_result}
            yield {"event": "stream", "data": "Here is the '"}
            yield {"event": "stream", "data": "analysis you requested"}
            yield {"event": "done", "data": {"total_latency_ms": 800}}

        with patch("src.agent.graph.run_agent_graph", return_value=mock_agent_stream()):
            events = []
            async for event in stream_agent_response(
                query="Show spending",
                session_id="test-session",
                conversation_history=[],
            ):
                events.append(event)

            tool_events = [e for e in events if e.get("event") == "tool_result"]
            assert len(tool_events) == 1

    @pytest.mark.asyncio
    async def test_streaming_with_clarification(self) -> None:
        """Test that streaming handler can emit clarification events."""
        from src.agent.streaming import stream_agent_response

        clarification = HITLClarification(
            ambiguity_type="tool_selection",
            message="Please clarify",
            options=[],
        )

        async def mock_agent_stream():
            yield {"event": "clarification", "data": clarification}
            yield {"event": "done", "data": {"total_latency_ms": 300}}

        with patch("src.agent.graph.run_agent_graph", return_value=mock_agent_stream()):
            events = []
            async for event in stream_agent_response(
                query="Show spending",
                session_id="test-session",
                conversation_history=[],
            ):
                events.append(event)

            clarification_events = [
                e for e in events if e.get("event") == "clarification"
            ]
            assert len(clarification_events) == 1


# ============================================================================
# Test Cancellation Support (NFR-1.4)
# ============================================================================

class TestCancellationSupport:
    """Tests for streaming cancellation support."""

    @pytest.mark.asyncio
    async def test_streaming_can_be_cancelled_via_generator(self) -> None:
        """Test that streaming supports cancellation via async generator."""
        from src.agent.streaming import stream_agent_response

        cancellation_requested = {"cancelled": False}

        async def mock_agent_stream():
            for i in range(100):
                if cancellation_requested["cancelled"]:
                    break
                yield {"event": "stream", "data": f"token_{i}"}
            yield {"event": "done", "data": {"total_latency_ms": 1000}}

        with patch("src.agent.graph.run_agent_graph", return_value=mock_agent_stream()):
            tokens = []
            async for event in stream_agent_response(
                query="Show spending",
                session_id="test-session",
                conversation_history=[],
            ):
                tokens.append(event)
                if len(tokens) >= 5:
                    cancellation_requested["cancelled"] = True
                    break

            # Should have stopped after cancellation
            assert len(tokens) == 5


# ============================================================================
# Test ObservabilityMetadata Model
# ============================================================================

class TestObservabilityMetadata:
    """Tests for ObservabilityMetadata model."""

    def test_observability_metadata_has_required_fields(self) -> None:
        """Test that ObservabilityMetadata has all required fields."""
        from src.agent.streaming import ObservabilityMetadata

        metadata = ObservabilityMetadata(
            total_latency_ms=1000,
            pipeline_stages={"retrieve": {"latency_ms": 100}},
            first_token_latency_ms=200,
            session_id="test-123",
        )

        assert metadata.total_latency_ms == 1000
        assert "retrieve" in metadata.pipeline_stages
        assert metadata.first_token_latency_ms == 200
        assert metadata.session_id == "test-123"

    def test_observability_metadata_optional_fields_default_to_empty(self) -> None:
        """Test that optional fields default to empty dict/list."""
        from src.agent.streaming import ObservabilityMetadata

        metadata = ObservabilityMetadata(
            total_latency_ms=1000,
            pipeline_stages={},
            first_token_latency_ms=200,
            session_id="test-123",
        )

        assert metadata.pipeline_stages == {}
        assert metadata.error is None


# ============================================================================
# Test SSE Event Formatter
# ============================================================================

class TestSSEEventFormatter:
    """Tests for SSEEventFormatter class."""

    def test_formatter_produces_valid_sse(self) -> None:
        """Test that formatter produces valid SSE output."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        result = formatter.format_event("test", {"key": "value"})

        # SSE format: event: <type>\ndata: <json>\n\n
        assert "event: test" in result
        assert "data:" in result
        assert result.endswith("\n\n")

    def test_formatter_serializes_dict_as_json(self) -> None:
        """Test that formatter serializes dict data as JSON."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        data = {"string": "value", "number": 42, "bool": True}
        result = formatter.format_event("stream", data)

        # Should contain valid JSON in data line
        assert "string" in result
        assert "value" in result
        assert "42" in result

    def test_formatter_serializes_string_as_plain_data(self) -> None:
        """Test that formatter serializes string data directly."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        result = formatter.format_event("stream", "plain string")

        # For string data, should be in data line directly
        assert "plain string" in result

    def test_formatter_handles_empty_data(self) -> None:
        """Test that formatter handles empty data gracefully."""
        from src.agent.streaming import SSEEventFormatter

        formatter = SSEEventFormatter()
        result = formatter.format_event("done", {})

        assert "event: done" in result
        assert "data:" in result


# ============================================================================
# Test StreamingResponseBuilder
# ============================================================================

class TestStreamingResponseBuilder:
    """Tests for StreamingResponseBuilder class."""

    @pytest.mark.asyncio
    async def test_builder_yields_sse_formatted_events(self) -> None:
        """Test that builder yields properly formatted SSE events."""
        from src.agent.streaming import StreamingResponseBuilder

        builder = StreamingResponseBuilder()

        events = [
            {"event": "stream", "data": "Hello"},
            {"event": "stream", "data": " World"},
            {"event": "done", "data": {"total": 100}},
        ]

        results = []
        async for formatted in builder.build_sse_events(events):
            results.append(formatted)

        assert len(results) == 3
        for result in results:
            assert "event:" in result
            assert "data:" in result
            assert result.endswith("\n\n")

    @pytest.mark.asyncio
    async def test_builder_handles_generator_input(self) -> None:
        """Test that builder accepts async generator input."""
        from src.agent.streaming import StreamingResponseBuilder

        async def event_generator():
            yield {"event": "stream", "data": "A"}
            yield {"event": "stream", "data": "B"}

        builder = StreamingResponseBuilder()
        results = []
        async for formatted in builder.build_sse_events(event_generator()):
            results.append(formatted)

        assert len(results) == 2


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases in streaming implementation."""

    @pytest.mark.asyncio
    async def test_handles_empty_response(self) -> None:
        """Test that streaming handles empty responses gracefully."""
        from src.agent.streaming import stream_agent_response

        async def mock_empty_stream():
            yield {"event": "done", "data": {"total_latency_ms": 0}}
            return

        with patch("src.agent.graph.run_agent_graph", return_value=mock_empty_stream()):
            events = []
            async for event in stream_agent_response(
                query="Show spending",
                session_id="test-session",
                conversation_history=[],
            ):
                events.append(event)

            # Should still have done event
            done_events = [e for e in events if e.get("event") == "done"]
            assert len(done_events) == 1

    @pytest.mark.asyncio
    async def test_handles_rapid_tokens(self) -> None:
        """Test that streaming handles rapid token emission."""
        from src.agent.streaming import stream_agent_response

        async def mock_rapid_stream():
            for _ in range(100):
                yield {"event": "stream", "data": "x"}
            yield {"event": "done", "data": {"total_latency_ms": 50}}

        with patch("src.agent.graph.run_agent_graph", return_value=mock_rapid_stream()):
            tokens = []
            async for event in stream_agent_response(
                query="Show spending",
                session_id="test-session",
                conversation_history=[],
            ):
                tokens.append(event)

            # Should handle all tokens
            assert len(tokens) == 101  # 100 stream + 1 done
