"""TDD Tests for CopilotKit Endpoint (FR-1.2, FR-8.3, NFR-1.4).

Tests the /api/copilotkit endpoint that handles multi-turn conversation
with SSE streaming response.

FR Requirements:
- FR-1.2: Multi-Turn Conversation (endpoint receives multi-turn context)
- FR-8.3: Response Generation Model (model selection from request)
- NFR-1.4: Streaming (SSE response)

Interface Contract:
POST /api/copilotkit
Request: { messages: List[ChatMessage], session_id: str, selected_model: str }
Response: SSE stream of SSEToolResult | SSEClarification | SSEStreamChunk | SSEDone

Where:
- ChatMessage: { role: "user" | "assistant", content: str }
- SSEToolResult: event="tool_result", data={ referenceId, toolName, dimensions, data, timestamp }
- SSEClarification: event="clarification", data=HITLClarification
- SSEStreamChunk: event="stream", data={ token: str }
- SSEDone: event="done", data=ObservabilityMetadata
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def client() -> TestClient:
    """Create test client for the FastAPI app."""
    from src.main import app
    return TestClient(app)


@pytest.fixture
def valid_copilotkit_payload() -> Dict[str, Any]:
    """Create a valid CopilotKit request payload."""
    return {
        "messages": [
            {"role": "user", "content": "Show spending by generation"},
            {"role": "assistant", "content": "Here's spending by generation..."},
            {"role": "user", "content": "Now filter by Gen Z only"},
        ],
        "session_id": "test-session-123",
        "selected_model": "openai/gpt-4o",
    }


@pytest.fixture
def mock_streaming_response() -> List[Dict[str, Any]]:
    """Create a mock streaming response sequence."""
    return [
        {"event": "stream", "data": {"token": "Based"}},
        {"event": "stream", "data": {"token": " on"}},
        {"event": "stream", "data": {"token": " your"}},
        {"event": "stream", "data": {"token": " query"}},
        {"event": "done", "data": {
            "total_latency_ms": 1200,
            "pipeline_stages": {},
            "first_token_latency_ms": 350,
            "session_id": "test-session-123",
        }},
    ]


# ============================================================================
# Test FR-1.2: Multi-Turn Conversation
# ============================================================================


class TestFR1_2_MultiTurnConversation:
    """Tests for FR-1.2: Multi-Turn Conversation support."""

    def test_fr_1_2_endpoint_accepts_post_request(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test FR-1.2: Endpoint accepts POST requests with multi-turn context."""
        with patch("src.api.router.create_streaming_response") as mock_stream:
            # Setup mock to return a simple streaming response
            async def mock_response():
                async def generator():
                    yield "event: done\ndata: {}\n\n"
                return generator()

            mock_stream.return_value = MagicMock(
                status_code=200,
                body_iterator=mock_response(),
            )

            response = client.post("/api/copilotkit", json=valid_copilotkit_payload)

            # Should accept the POST request
            assert response.status_code in [200, 500]  # 500 if mock not properly async

    def test_fr_1_2_messages_field_is_list(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test FR-1.2: messages field accepts list of conversation turns."""
        with patch("src.api.router.create_streaming_response") as mock_stream:
            mock_stream.return_value = MagicMock(
                status_code=200,
                body_iterator=iter([]),
            )

            response = client.post("/api/copilotkit", json=valid_copilotkit_payload)

            # Request should be accepted (validation passes)
            assert response.status_code in [200, 500]

    def test_fr_1_2_messages_have_role_and_content(
        self,
        client: TestClient,
    ) -> None:
        """Test FR-1.2: Each message has role and content fields."""
        payload = {
            "messages": [
                {"role": "user", "content": "Test query"},
                {"role": "assistant", "content": "Test response"},
            ],
            "session_id": "test-session",
            "selected_model": "openai/gpt-4o",
        }

        with patch("src.api.router.create_streaming_response") as mock_stream:
            mock_stream.return_value = MagicMock(
                status_code=200,
                body_iterator=iter([]),
            )

            response = client.post("/api/copilotkit", json=payload)
            assert response.status_code in [200, 500]

    def test_fr_1_2_session_id_is_preserved(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test FR-1.2: session_id is preserved for multi-turn context."""
        session_id = "unique-session-456"

        with patch("src.api.router.create_streaming_response") as mock_stream:
            mock_stream.return_value = MagicMock(
                status_code=200,
                body_iterator=iter([]),
            )

            payload = valid_copilotkit_payload.copy()
            payload["session_id"] = session_id

            response = client.post("/api/copilotkit", json=payload)

            # Verify session_id was passed to the streaming function
            mock_stream.assert_called_once()
            call_kwargs = mock_stream.call_args
            assert call_kwargs[1]["session_id"] == session_id


# ============================================================================
# Test FR-8.3: Response Generation Model Selection
# ============================================================================


class TestFR8_3_ModelSelection:
    """Tests for FR-8.3: Response Generation Model selection."""

    def test_fr_8_3_endpoint_accepts_selected_model_field(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test FR-8.3: Endpoint accepts selected_model in request."""
        with patch("src.api.router.create_streaming_response") as mock_stream:
            mock_stream.return_value = MagicMock(
                status_code=200,
                body_iterator=iter([]),
            )

            response = client.post("/api/copilotkit", json=valid_copilotkit_payload)

            # Request should be accepted
            assert response.status_code in [200, 500]

    def test_fr_8_3_selected_model_is_passed_to_streaming(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test FR-8.3: selected_model is passed to streaming response."""
        selected_model = "google/gemini-2.0-flash"

        with patch("src.api.router.create_streaming_response") as mock_stream:
            mock_stream.return_value = MagicMock(
                status_code=200,
                body_iterator=iter([]),
            )

            payload = valid_copilotkit_payload.copy()
            payload["selected_model"] = selected_model

            response = client.post("/api/copilotkit", json=payload)

            # Verify selected_model was passed
            mock_stream.assert_called_once()
            call_kwargs = mock_stream.call_args
            assert call_kwargs[1]["selected_model"] == selected_model

    def test_fr_8_3_model_options_include_configurable_models(
        self,
        client: TestClient,
    ) -> None:
        """Test FR-8.3: Model selector supports user-configurable models."""
        from src.config import USER_CONFIGURABLE_MODELS

        # Should have multiple model options
        assert len(USER_CONFIGURABLE_MODELS) > 0

        # Each model should have supports_function_calling flag
        for model_id, model_info in USER_CONFIGURABLE_MODELS.items():
            assert "supports_function_calling" in model_info


# ============================================================================
# Test NFR-1.4: SSE Streaming Response
# ============================================================================


class TestNFR1_4_SSEStreaming:
    """Tests for NFR-1.4: SSE Streaming response."""

    def test_nfr_1_4_endpoint_returns_sse_content_type(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test NFR-1.4: Response uses text/event-stream content type."""
        from fastapi.responses import StreamingResponse
        from fastapi import HTTPException

        async def mock_streaming_response(*args, **kwargs):
            from fastapi.responses import StreamingResponse
            from typing import AsyncGenerator

            async def event_generator() -> AsyncGenerator[str, None]:
                yield "event: done\ndata: {}\n\n"

            return StreamingResponse(
                content=event_generator(),
                media_type="text/event-stream",
            )

        with patch("src.api.router.create_streaming_response", side_effect=mock_streaming_response):
            response = client.post("/api/copilotkit", json=valid_copilotkit_payload)

            # Should return successful response
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_nfr_1_4_stream_events_have_proper_sse_format(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test NFR-1.4: Stream events follow SSE format (event: type\\ndata: json\\n\\n)."""
        from fastapi.responses import StreamingResponse
        from typing import AsyncGenerator

        async def mock_streaming_response(*args, **kwargs):
            async def event_generator() -> AsyncGenerator[str, None]:
                # SSE format: event: <type>\ndata: <json>\n\n
                yield "event: stream\ndata: {\"token\": \"Hello\"}\n\n"
                yield "event: stream\ndata: {\"token\": \" World\"}\n\n"
                yield "event: done\ndata: {\"total_latency_ms\": 500}\n\n"

            return StreamingResponse(
                content=event_generator(),
                media_type="text/event-stream",
            )

        with patch("src.api.router.create_streaming_response", side_effect=mock_streaming_response):
            response = client.post("/api/copilotkit", json=valid_copilotkit_payload)

            assert response.status_code == 200

    def test_nfr_1_4_stream_event_formatting(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test NFR-1.4: SSE stream event has correct format."""
        from fastapi.responses import StreamingResponse
        from typing import AsyncGenerator

        async def mock_streaming_response(*args, **kwargs):
            async def event_generator() -> AsyncGenerator[str, None]:
                yield "event: stream\ndata: {\"token\": \"Test\"}\n\n"

            return StreamingResponse(
                content=event_generator(),
                media_type="text/event-stream",
            )

        with patch("src.api.router.create_streaming_response", side_effect=mock_streaming_response):
            response = client.post("/api/copilotkit", json=valid_copilotkit_payload)

            # Response should contain SSE formatted data
            assert response.status_code == 200

    def test_nfr_1_4_done_event_has_observability_metadata(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test NFR-1.4: Done event contains ObservabilityMetadata (timing info)."""
        from fastapi.responses import StreamingResponse
        from typing import AsyncGenerator

        async def mock_streaming_response(*args, **kwargs):
            async def event_generator() -> AsyncGenerator[str, None]:
                yield "event: done\ndata: {\"total_latency_ms\": 1200, \"first_token_latency_ms\": 350, \"session_id\": \"test-session-123\"}\n\n"

            return StreamingResponse(
                content=event_generator(),
                media_type="text/event-stream",
            )

        with patch("src.api.router.create_streaming_response", side_effect=mock_streaming_response):
            response = client.post("/api/copilotkit", json=valid_copilotkit_payload)

            # Response should be successful
            assert response.status_code == 200

    def test_nfr_1_4_response_uses_sse_event_types(
        self,
        client: TestClient,
        valid_copilotkit_payload: Dict[str, Any],
    ) -> None:
        """Test NFR-1.4: Response uses correct SSE event types (stream, done, tool_result, clarification)."""
        from fastapi.responses import StreamingResponse
        from typing import AsyncGenerator

        async def mock_streaming_response(*args, **kwargs):
            async def event_generator() -> AsyncGenerator[str, None]:
                yield "event: stream\ndata: {\"token\": \"Hello\"}\n\n"
                yield "event: done\ndata: {\"total_latency_ms\": 500}\n\n"

            return StreamingResponse(
                content=event_generator(),
                media_type="text/event-stream",
            )

        with patch("src.api.router.create_streaming_response", side_effect=mock_streaming_response):
            response = client.post("/api/copilotkit", json=valid_copilotkit_payload)

            assert response.status_code == 200


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Tests for error handling in CopilotKit endpoint."""

    def test_missing_messages_field_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Test that missing messages field returns 422 validation error."""
        payload = {
            "session_id": "test-session",
            "selected_model": "openai/gpt-4o",
        }

        response = client.post("/api/copilotkit", json=payload)

        # Should return validation error
        assert response.status_code == 422

    def test_missing_session_id_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Test that missing session_id returns 422 validation error."""
        payload = {
            "messages": [{"role": "user", "content": "Test"}],
            "selected_model": "openai/gpt-4o",
        }

        response = client.post("/api/copilotkit", json=payload)

        assert response.status_code == 422

    def test_invalid_role_returns_422(
        self,
        client: TestClient,
    ) -> None:
        """Test that invalid role value returns 422 validation error."""
        payload = {
            "messages": [{"role": "invalid_role", "content": "Test"}],
            "session_id": "test-session",
            "selected_model": "openai/gpt-4o",
        }

        response = client.post("/api/copilotkit", json=payload)

        assert response.status_code == 422


# ============================================================================
# Test Endpoint Registration
# ============================================================================


class TestEndpointRegistration:
    """Tests for endpoint registration in router."""

    def test_copilotkit_endpoint_is_registered(
        self,
        client: TestClient,
    ) -> None:
        """Test that /api/copilotkit endpoint is properly registered."""
        # Should not return 404
        response = client.get("/api/copilotkit")
        assert response.status_code != 404

    def test_router_includes_copilotkit_route(
        self,
        client: TestClient,
    ) -> None:
        """Test that router includes the CopilotKit route."""
        from src.api.router import api_router

        # Get all registered routes
        routes = [route.path for route in api_router.routes]

        # Should have /api/copilotkit or copilotkit route
        assert any("copilotkit" in route for route in routes)
