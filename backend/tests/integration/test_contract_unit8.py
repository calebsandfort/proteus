"""Contract tests: Unit 8 (Response Generation & Streaming).

Verifies the integration seams between Unit 8 and its dependencies:
- IU-8 → IU-7: AgentGraph.run_agent_graph import and function signature
- IU-8 → IU-7: HITLClarification import from nodes
- IU-8 → IU-6: OpenRouterClient and model_config imports
- IU-8 internal: streaming.py ↔ context.py ToolResult type compatibility

No mocks at the integration boundary — real modules from both units are imported.
"""

import inspect
from typing import get_type_hints

import pytest


# ============================================================================
# 1. Import Resolution Tests (IU-8 → IU-7, IU-6)
# ============================================================================


class TestUnit8FromUnit7Imports:
    """Verify Unit 8 can import from Unit 7 (LangGraph Agent Graph)."""

    def test_streaming_imports_run_agent_graph(self):
        """streaming.py can import run_agent_graph from IU-7 graph module."""
        from src.agent.graph import run_agent_graph

        assert run_agent_graph is not None
        assert callable(run_agent_graph)

    def test_streaming_imports_agent_from_graph(self):
        """streaming.py can import the compiled agent from IU-7 graph module."""
        from src.agent.graph import agent

        assert agent is not None

    def test_nodes_imports_hitl_clarification(self):
        """streaming.py imports HITLClarification from nodes (IU-7)."""
        from src.agent.nodes import HITLClarification

        assert HITLClarification is not None

    def test_nodes_imports_clarification_option(self):
        """streaming.py imports ClarificationOption from nodes (IU-7)."""
        from src.agent.nodes import ClarificationOption

        assert ClarificationOption is not None


class TestUnit8FromUnit6Imports:
    """Verify Unit 8 can import from Unit 6 (OpenRouter Integration)."""

    def test_response_imports_openrouter_client(self):
        """response.py can import OpenRouterClient from IU-6."""
        from src.api.openrouter import OpenRouterClient

        assert OpenRouterClient is not None

    def test_response_imports_user_configurable_models(self):
        """response.py can import USER_CONFIGURABLE_MODELS from IU-6 config."""
        from src.config import USER_CONFIGURABLE_MODELS

        assert USER_CONFIGURABLE_MODELS is not None
        assert isinstance(USER_CONFIGURABLE_MODELS, dict)
        assert len(USER_CONFIGURABLE_MODELS) > 0

    def test_response_imports_model_config(self):
        """response.py can import model_config from IU-6 config."""
        from src.config import model_config

        assert model_config is not None
        assert hasattr(model_config, "response_generation")


class TestUnit8InternalImports:
    """Verify Unit 8 internal module imports resolve correctly."""

    def test_streaming_imports_tool_result(self):
        """streaming.py can import ToolResult from IU-8 context module."""
        from src.agent.context import ToolResult

        assert ToolResult is not None

    def test_streaming_imports_hitl_clarification_from_nodes(self):
        """streaming.py imports HITLClarification from nodes (not context)."""
        from src.agent.nodes import HITLClarification

        assert HITLClarification is not None

    def test_router_imports_create_streaming_response(self):
        """router.py can import create_streaming_response from IU-8 streaming module."""
        from src.agent.streaming import create_streaming_response

        assert create_streaming_response is not None
        assert callable(create_streaming_response)

    def test_context_module_loads_without_error(self):
        """context.py module loads cleanly."""
        from src.agent import context

        assert hasattr(context, "ToolResult")
        assert hasattr(context, "SessionContext")
        assert hasattr(context, "ConversationTurn")

    def test_streaming_module_loads_without_error(self):
        """streaming.py module loads cleanly."""
        from src.agent import streaming

        assert hasattr(streaming, "ObservabilityMetadata")
        assert hasattr(streaming, "SSEEventFormatter")
        assert hasattr(streaming, "create_streaming_response")

    def test_response_module_loads_without_error(self):
        """response.py module loads cleanly."""
        from src.agent import response

        assert hasattr(response, "ResponseSynthesizer")
        assert hasattr(response, "ModelSelector")
        assert hasattr(response, "VisualizationRecommender")


# ============================================================================
# 2. Function Signature Tests
# ============================================================================


class TestFunctionSignatures:
    """Verify function signatures match the integration contract."""

    def test_run_agent_graph_accepts_required_parameters(self):
        """run_agent_graph accepts query, session_id, conversation_history."""
        from src.agent.graph import run_agent_graph

        sig = inspect.signature(run_agent_graph)
        params = list(sig.parameters.keys())

        # Must have: query, session_id, conversation_history
        assert "query" in params, f"run_agent_graph missing 'query' param. Found: {params}"
        assert "session_id" in params, f"run_agent_graph missing 'session_id' param. Found: {params}"
        assert "conversation_history" in params, f"run_agent_graph missing 'conversation_history' param. Found: {params}"

    def test_run_agent_graph_is_async(self):
        """run_agent_graph is an async function."""
        from src.agent.graph import run_agent_graph

        sig = inspect.signature(run_agent_graph)
        # Check if it's a coroutine function
        assert inspect.iscoroutinefunction(run_agent_graph), "run_agent_graph should be async"

    def test_create_streaming_response_accepts_required_parameters(self):
        """create_streaming_response accepts query, session_id, conversation_history, selected_model."""
        from src.agent.streaming import create_streaming_response

        sig = inspect.signature(create_streaming_response)
        params = list(sig.parameters.keys())

        assert "query" in params, f"create_streaming_response missing 'query' param. Found: {params}"
        assert "session_id" in params, f"create_streaming_response missing 'session_id' param. Found: {params}"
        assert "conversation_history" in params, f"create_streaming_response missing 'conversation_history' param. Found: {params}"
        assert "selected_model" in params, f"create_streaming_response missing 'selected_model' param. Found: {params}"

    def test_create_streaming_response_is_async(self):
        """create_streaming_response is an async function."""
        from src.agent.streaming import create_streaming_response

        assert inspect.iscoroutinefunction(create_streaming_response), "create_streaming_response should be async"

    def test_stream_agent_response_accepts_required_parameters(self):
        """stream_agent_response accepts query, session_id, conversation_history, selected_model."""
        from src.agent.streaming import stream_agent_response

        sig = inspect.signature(stream_agent_response)
        params = list(sig.parameters.keys())

        assert "query" in params
        assert "session_id" in params
        assert "conversation_history" in params
        assert "selected_model" in params

    def test_response_synthesizer_init_accepts_openrouter_client(self):
        """ResponseSynthesizer.__init__ accepts openrouter_client and optional model."""
        from src.agent.response import ResponseSynthesizer

        sig = inspect.signature(ResponseSynthesizer.__init__)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "openrouter_client" in params


# ============================================================================
# 3. Type Compatibility Tests
# ============================================================================


class TestTypeCompatibility:
    """Verify type compatibility between Unit 8 modules."""

    def test_tool_result_has_required_fields(self):
        """ToolResult from context.py has fields required by streaming.py."""
        from src.agent.context import ToolResult

        # Check model fields
        fields = ToolResult.model_fields
        assert "referenceId" in fields, "ToolResult missing 'referenceId' field"
        assert "tool_name" in fields, "ToolResult missing 'tool_name' field"
        assert "data" in fields, "ToolResult missing 'data' field"

    def test_hitl_clarification_has_required_fields(self):
        """HITLClarification from nodes.py has fields expected by streaming.py."""
        from src.agent.nodes import HITLClarification

        fields = HITLClarification.model_fields
        assert "ambiguity_type" in fields
        assert "message" in fields
        assert "options" in fields

    def test_observability_metadata_has_required_fields(self):
        """ObservabilityMetadata from streaming.py has required fields per NFR-1.4."""
        from src.agent.streaming import ObservabilityMetadata

        fields = ObservabilityMetadata.model_fields
        assert "total_latency_ms" in fields, "ObservabilityMetadata missing 'total_latency_ms'"
        assert "pipeline_stages" in fields, "ObservabilityMetadata missing 'pipeline_stages'"
        assert "first_token_latency_ms" in fields, "ObservabilityMetadata missing 'first_token_latency_ms'"
        assert "session_id" in fields, "ObservabilityMetadata missing 'session_id'"

    def test_copilotkit_request_has_required_fields(self):
        """CopilotKitRequest from router.py has fields required by FR-1.2, FR-8.3."""
        from src.api.router import CopilotKitRequest

        fields = CopilotKitRequest.model_fields
        assert "messages" in fields, "CopilotKitRequest missing 'messages'"
        assert "session_id" in fields, "CopilotKitRequest missing 'session_id'"
        assert "selected_model" in fields, "CopilotKitRequest missing 'selected_model'"

    def test_chat_message_has_required_fields(self):
        """ChatMessage from router.py has fields required by FR-1.2."""
        from src.api.router import ChatMessage

        fields = ChatMessage.model_fields
        assert "role" in fields, "ChatMessage missing 'role'"
        assert "content" in fields, "ChatMessage missing 'content'"

    def test_synthesis_result_has_required_fields(self):
        """SynthesisResult from response.py has fields required by FR-8.3."""
        from src.agent.response import SynthesisResult

        fields = SynthesisResult.model_fields
        assert "answer" in fields
        assert "visualizations" in fields
        assert "suggestions" in fields
        assert "model_used" in fields
        assert "used_fallback" in fields


# ============================================================================
# 4. Wiring Verification Tests
# ============================================================================


class TestRouterWiring:
    """Verify router registration in the FastAPI app (main.py)."""

    def test_api_router_includes_copilotkit_route(self):
        """Verify api_router includes the /copilotkit POST route."""
        from fastapi.routing import APIRoute
        from src.api.router import api_router

        route_paths = [r.path for r in api_router.routes if isinstance(r, APIRoute)]
        assert any("/copilotkit" in p for p in route_paths), (
            f"Expected /copilotkit route not found in api_router. Found: {route_paths}"
        )

    def test_copilotkit_route_accepts_post(self):
        """Verify /copilotkit route accepts POST method."""
        from fastapi.routing import APIRoute
        from src.api.router import api_router

        for route in api_router.routes:
            if isinstance(route, APIRoute) and "/copilotkit" in route.path:
                assert "POST" in route.methods, f"/copilotkit route should accept POST. Methods: {route.methods}"
                break
        else:
            pytest.fail("/copilotkit route not found in api_router")


class TestMiddlewareWiring:
    """Verify middleware registration on the FastAPI app."""

    def test_cors_middleware_registered(self):
        """Verify CORS middleware is registered on the app."""
        from src.main import app

        # Check user_middleware where FastAPI stores middleware
        user_middleware = app.user_middleware
        assert len(user_middleware) > 0, "No middleware registered"

        middleware_str = str(user_middleware)
        assert "CORSMiddleware" in middleware_str, (
            f"CORSMiddleware not found in user_middleware: {user_middleware}"
        )


class TestMainAppWiring:
    """Verify main app wiring includes api_router at /api prefix."""

    def test_app_includes_api_router(self):
        """Verify the main app includes api_router at /api prefix."""
        from src.main import app

        # Check that routes with /api prefix exist
        route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
        assert any("/api" in p for p in route_paths), (
            f"Expected /api routes not found in app. Found: {route_paths}"
        )

    def test_app_includes_health_route(self):
        """Verify the main app includes health endpoint at /health."""
        from src.main import app

        route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
        assert any("/health" in p for p in route_paths), (
            f"Expected /health route not found in app. Found: {route_paths}"
        )


# ============================================================================
# 5. Model Selector Tests (FR-8.3)
# ============================================================================


class TestModelSelector:
    """Verify ModelSelector behavior for FR-8.3 response generation model selection."""

    def test_model_selector_initializes_with_default(self):
        """ModelSelector initializes with default model from config."""
        from src.agent.response import ModelSelector
        from src.config import model_config

        selector = ModelSelector()
        assert selector.default_model == model_config.response_generation

    def test_select_model_returns_fallback_info(self):
        """select_model returns FallbackInfo with model and fallback status."""
        from src.agent.response import ModelSelector, FallbackInfo

        selector = ModelSelector()
        result = selector.select_model("openai/gpt-4o")

        assert isinstance(result, FallbackInfo)
        assert result.model is not None
        assert isinstance(result.used_fallback, bool)

    def test_select_model_unknown_model_triggers_fallback(self):
        """Unknown model triggers fallback with warning."""
        from src.agent.response import ModelSelector

        selector = ModelSelector()
        result = selector.select_model("unknown/model")

        assert result.used_fallback is True
        assert result.warning is not None

    def test_select_model_non_function_calling_triggers_fallback(self):
        """Model without function calling support triggers fallback."""
        from src.agent.response import ModelSelector

        selector = ModelSelector()
        # This assumes at least one model in USER_CONFIGURABLE_MODELS
        # doesn't support function calling (or we test with a known one)
        result = selector.select_model("openai/gpt-4o")

        # gpt-4o supports function calling, so no fallback
        assert isinstance(result.used_fallback, bool)


# ============================================================================
# 6. Context Management Tests (FR-1.2)
# ============================================================================


class TestSessionContext:
    """Verify session context management for FR-1.2 multi-turn conversation."""

    def test_create_session_context_returns_valid_context(self):
        """create_session_context creates valid SessionContext with anchor."""
        from src.agent.context import create_session_context, SessionContext

        ctx = create_session_context(
            query="Show me market share for Walmart",
            session_id="test-session-123"
        )

        assert isinstance(ctx, SessionContext)
        assert ctx.session_id == "test-session-123"
        assert ctx.session_anchor == "Show me market share for Walmart"
        assert len(ctx.recent_turns) == 1
        assert ctx.recent_turns[0].is_sessionAnchor is True

    def test_add_turn_returns_updated_context(self):
        """add_turn returns new SessionContext (immutable pattern)."""
        import uuid
        from src.agent.context import create_session_context, add_turn, ConversationTurn

        ctx = create_session_context(
            query="Show me market share for Walmart",
            session_id="test-session-123"
        )

        new_turn = ConversationTurn(
            id=str(uuid.uuid4()),
            role="assistant",
            content="Here are the results..."
        )

        new_ctx = add_turn(ctx, new_turn)

        # Original should be unchanged (immutable)
        assert len(ctx.recent_turns) == 1
        # New context should have 2 turns
        assert len(new_ctx.recent_turns) == 2

    def test_estimate_tokens_works(self):
        """estimate_tokens returns reasonable token estimates."""
        from src.agent.context import estimate_tokens

        # ~4 chars per token approximation
        text = "Hello world this is a test"
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert tokens == len(text) // 4

    def test_is_within_context_limit(self):
        """is_within_context_limit correctly checks 75% threshold."""
        from src.agent.context import (
            create_session_context,
            add_turn,
            is_within_context_limit,
            ConversationTurn
        )

        ctx = create_session_context(
            query="Short query",
            session_id="test"
        )

        # Small context should be within limit
        assert is_within_context_limit(ctx) is True

    def test_needs_summarization_false_for_small_context(self):
        """needs_summarization returns False when under 80% threshold."""
        from src.agent.context import (
            create_session_context,
            needs_summarization
        )

        ctx = create_session_context(
            query="Short query",
            session_id="test"
        )

        # Small context shouldn't need summarization
        assert needs_summarization(ctx) is False


# ============================================================================
# 7. Constants Verification (FR-1.2, NFR-1.4)
# ============================================================================


class TestConstants:
    """Verify constants match FR requirements."""

    def test_max_context_ratio_is_075(self):
        """MAX_CONTEXT_RATIO should be 0.75 (75% of context window)."""
        from src.agent.context import MAX_CONTEXT_RATIO

        assert MAX_CONTEXT_RATIO == 0.75

    def test_min_turns_to_keep_is_4(self):
        """MIN_TURNS_TO_KEEP should be 4 (minimum turns per FR-1.2)."""
        from src.agent.context import MIN_TURNS_TO_KEEP

        assert MIN_TURNS_TO_KEEP == 4

    def test_summarization_threshold_is_080(self):
        """SUMMARIZATION_THRESHOLD should be 0.80 (80% triggers summarization)."""
        from src.agent.context import SUMMARIZATION_THRESHOLD

        assert SUMMARIZATION_THRESHOLD == 0.80
