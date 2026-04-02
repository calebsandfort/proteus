"""Tests for FR-2.4-2.6: AgentState Schema and SessionContext.

This module tests the expanded AgentState TypedDict and SessionContext model
for the LangGraph Agent system.

FR Requirements:
- FR-2.4: Tool Selection LLM (dimension match scoring function)
- FR-2.5: HITL Clarification (clarification field in state)
- FR-2.6: Multi-Tool Query Handling (planner node output types)

Test Requirements:
- Test AgentState has all required keys
- Test SessionContext model validation
- Test state fields have correct types
- Test dimension match scoring function (compute_dimension_match_score)
- Mock all external dependencies
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.api.models.dimensions import ExtractedDimensions
from src.api.models.tool import RetrievedTool, ToolDefinition, ToolOutputSchema, ToolParameter, OutputField


class TestAgentStateKeys:
    """Test that AgentState has all required keys."""

    def test_agent_state_has_messages_key(self) -> None:
        """AgentState must have 'messages' key for chat history."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "messages" in state

    def test_agent_state_has_query_key(self) -> None:
        """AgentState must have 'query' key for original user query."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "query" in state
        assert state["query"] == "test query"

    def test_agent_state_has_session_id_key(self) -> None:
        """AgentState must have 'session_id' key for session tracking."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session-123",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "session_id" in state
        assert state["session_id"] == "test-session-123"

    def test_agent_state_has_retrieved_tools_key(self) -> None:
        """AgentState must have 'retrieved_tools' key for RAG results."""
        from src.agent.state import AgentState

        mock_tool = _create_mock_retrieved_tool("tool_1", "Test Tool", ["category"])

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[mock_tool],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "retrieved_tools" in state
        assert len(state["retrieved_tools"]) == 1

    def test_agent_state_has_extracted_dimensions_key(self) -> None:
        """AgentState must have 'extracted_dimensions' key."""
        from src.agent.state import AgentState

        dims = ExtractedDimensions(brand=["Nike"], generation=["gen_z"])

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=dims,
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "extracted_dimensions" in state
        assert state["extracted_dimensions"].brand == ["Nike"]

    def test_agent_state_has_tool_selection_result_key(self) -> None:
        """AgentState must have 'tool_selection_result' key."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "tool_selection_result" in state
        assert state["tool_selection_result"] is None

    def test_agent_state_has_clarification_key(self) -> None:
        """AgentState must have 'clarification' key for HITL."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "clarification" in state
        assert state["clarification"] is None

    def test_agent_state_has_execution_plan_key(self) -> None:
        """AgentState must have 'execution_plan' key for planner node."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "execution_plan" in state
        assert state["execution_plan"] is None

    def test_agent_state_has_execution_results_key(self) -> None:
        """AgentState must have 'execution_results' key."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={"tool_1": {"result": "data"}},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert "execution_results" in state
        assert state["execution_results"]["tool_1"]["result"] == "data"

    def test_agent_state_has_final_output_key(self) -> None:
        """AgentState must have 'final_output' key."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output={"answer": "final result"},
            current_stage="init",
            error=None,
        )
        assert "final_output" in state
        assert state["final_output"]["answer"] == "final result"

    def test_agent_state_has_current_stage_key(self) -> None:
        """AgentState must have 'current_stage' key."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="retrieval",
            error=None,
        )
        assert "current_stage" in state
        assert state["current_stage"] == "retrieval"

    def test_agent_state_has_error_key(self) -> None:
        """AgentState must have 'error' key."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test query",
            session_id="test-session",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error="Something went wrong",
        )
        assert "error" in state
        assert state["error"] == "Something went wrong"


class TestSessionContext:
    """Test SessionContext model validation."""

    def test_session_context_can_be_instantiated(self) -> None:
        """SessionContext can be created with required fields."""
        from src.agent.state import SessionContext

        ctx = SessionContext(
            session_id="sess-123",
            session_anchor="What were my spending trends last quarter?",
            topic_tracker=["spending", "trends", "quarter"],
        )
        assert ctx.session_id == "sess-123"
        assert ctx.session_anchor == "What were my spending trends last quarter?"
        assert ctx.topic_tracker == ["spending", "trends", "quarter"]

    def test_session_context_has_default_context_limit(self) -> None:
        """SessionContext has default model_context_limit of 128000."""
        from src.agent.state import SessionContext

        ctx = SessionContext(
            session_id="sess-456",
            session_anchor="First query",
            topic_tracker=[],
        )
        assert ctx.model_context_limit == 128000

    def test_session_context_accepts_custom_context_limit(self) -> None:
        """SessionContext accepts custom model_context_limit."""
        from src.agent.state import SessionContext

        ctx = SessionContext(
            session_id="sess-789",
            session_anchor="First query",
            topic_tracker=[],
            model_context_limit=256000,
        )
        assert ctx.model_context_limit == 256000

    def test_session_context_requires_session_id(self) -> None:
        """SessionContext requires session_id field."""
        from src.agent.state import SessionContext

        with pytest.raises(ValidationError) as exc_info:
            SessionContext(
                session_anchor="Query",
                topic_tracker=[],
            )
        assert "session_id" in str(exc_info.value)

    def test_session_context_requires_session_anchor(self) -> None:
        """SessionContext requires session_anchor field."""
        from src.agent.state import SessionContext

        with pytest.raises(ValidationError) as exc_info:
            SessionContext(
                session_id="sess-123",
                topic_tracker=[],
            )
        assert "session_anchor" in str(exc_info.value)

    def test_session_context_requires_topic_tracker(self) -> None:
        """SessionContext requires topic_tracker field."""
        from src.agent.state import SessionContext

        with pytest.raises(ValidationError) as exc_info:
            SessionContext(
                session_id="sess-123",
                session_anchor="Query",
            )
        assert "topic_tracker" in str(exc_info.value)

    def test_session_context_topic_tracker_can_append(self) -> None:
        """SessionContext topic_tracker can be extended."""
        from src.agent.state import SessionContext

        ctx = SessionContext(
            session_id="sess-123",
            session_anchor="First query about spending",
            topic_tracker=["spending"],
        )
        ctx.topic_tracker.append("retail")
        ctx.topic_tracker.append("credit_card")
        assert ctx.topic_tracker == ["spending", "retail", "credit_card"]


class TestComputeDimensionMatchScore:
    """Test the compute_dimension_match_score function from FR-2.4."""

    def test_compute_dimension_match_score_returns_float(self) -> None:
        """compute_dimension_match_score returns a float."""
        from src.agent.state import compute_dimension_match_score

        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool("tool_1", "Test", ["brand", "time_range"]),
            extracted_dimensions=ExtractedDimensions(brand=["Nike"], time_range={"start": "2024-01-01", "end": "2024-03-31"}),
        )
        assert isinstance(result, float)

    def test_compute_dimension_match_score_full_match(self) -> None:
        """compute_dimension_match_score returns 1.0 for full dimension match."""
        from src.agent.state import compute_dimension_match_score

        # Tool requires brand and time_range, query has both
        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool(
                "market_trend",
                "Market Trend Tool",
                ["brand", "time_range"],
                ["category"],  # optional
            ),
            extracted_dimensions=ExtractedDimensions(
                brand=["Nike"],
                time_range={"start": "2024-01-01", "end": "2024-03-31"},
            ),
        )
        # All required dimensions matched
        assert result == 1.0

    def test_compute_dimension_match_score_partial_match(self) -> None:
        """compute_dimension_match_score returns 0.5 for partial match."""
        from src.agent.state import compute_dimension_match_score

        # Tool requires brand and time_range, but only brand is extracted
        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool(
                "market_trend",
                "Market Trend Tool",
                ["brand", "time_range"],  # required
            ),
            extracted_dimensions=ExtractedDimensions(
                brand=["Nike"],
                # Missing time_range
            ),
        )
        # 50% match (1 of 2 required dimensions)
        assert result == 0.5

    def test_compute_dimension_match_score_no_match(self) -> None:
        """compute_dimension_match_score returns 0.0 for no match."""
        from src.agent.state import compute_dimension_match_score

        # Tool requires brand and time_range, but neither is extracted
        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool(
                "market_trend",
                "Market Trend Tool",
                ["brand", "time_range"],
            ),
            extracted_dimensions=ExtractedDimensions(
                generation=["gen_z"],  # Different dimension
            ),
        )
        assert result == 0.0

    def test_compute_dimension_match_score_empty_required_dimensions(self) -> None:
        """compute_dimension_match_score returns 1.0 when tool has no required dimensions."""
        from src.agent.state import compute_dimension_match_score

        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool(
                "generic_tool",
                "Generic Tool",
                [],  # No required dimensions
            ),
            extracted_dimensions=ExtractedDimensions(),
        )
        assert result == 1.0

    def test_compute_dimension_match_score_with_optional_dimensions(self) -> None:
        """compute_dimension_match_score considers optional dimensions but doesn't penalize for missing."""
        from src.agent.state import compute_dimension_match_score

        # Tool has required=brand, optional=category
        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool(
                "brand_tool",
                "Brand Tool",
                ["brand"],  # required
                ["category"],  # optional
            ),
            extracted_dimensions=ExtractedDimensions(
                brand=["Nike"],
                # category not provided - should still be 1.0 since optional
            ),
        )
        # Required dimension matched, optional not penalized
        assert result == 1.0

    def test_compute_dimension_match_score_multiple_required_all_present(self) -> None:
        """compute_dimension_match_score returns 1.0 when all required dimensions are present."""
        from src.agent.state import compute_dimension_match_score

        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool(
                "multi_tool",
                "Multi Tool",
                ["brand", "merchant_category", "time_range", "geography"],
            ),
            extracted_dimensions=ExtractedDimensions(
                brand=["Nike"],
                merchant_category=["retail"],
                time_range={"start": "2024-01-01", "end": "2024-03-31"},
                geography=["CA", "TX"],
            ),
        )
        assert result == 1.0

    def test_compute_dimension_match_score_multiple_required_some_missing(self) -> None:
        """compute_dimension_match_score returns correct fraction when some required missing."""
        from src.agent.state import compute_dimension_match_score

        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool(
                "multi_tool",
                "Multi Tool",
                ["brand", "merchant_category", "time_range", "geography"],
            ),
            extracted_dimensions=ExtractedDimensions(
                brand=["Nike"],
                merchant_category=["retail"],
                # Missing time_range and geography
            ),
        )
        # 2 of 4 required dimensions matched = 0.5
        assert result == 0.5

    def test_compute_dimension_match_score_empty_extracted_dimensions(self) -> None:
        """compute_dimension_match_score returns 0.0 when no dimensions extracted."""
        from src.agent.state import compute_dimension_match_score

        result = compute_dimension_match_score(
            retrieved_tool=_create_mock_retrieved_tool(
                "market_trend",
                "Market Trend Tool",
                ["brand", "time_range"],
            ),
            extracted_dimensions=ExtractedDimensions(),
        )
        assert result == 0.0


class TestAgentStateFieldTypes:
    """Test that AgentState fields have correct types."""

    def test_agent_state_messages_is_list(self) -> None:
        """AgentState.messages is a list of BaseMessage."""
        from langchain_core.messages import HumanMessage
        from src.agent.state import AgentState

        state = AgentState(
            messages=[HumanMessage(content="Hello")],
            query="test",
            session_id="sess",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert isinstance(state["messages"], list)
        assert len(state["messages"]) == 1

    def test_agent_state_query_is_str(self) -> None:
        """AgentState.query is a string."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="What were my spending trends?",
            session_id="sess",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert isinstance(state["query"], str)

    def test_agent_state_session_id_is_str(self) -> None:
        """AgentState.session_id is a string."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test",
            session_id="session-abc-123",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert isinstance(state["session_id"], str)

    def test_agent_state_retrieved_tools_is_list(self) -> None:
        """AgentState.retrieved_tools is a list of RetrievedTool."""
        from src.agent.state import AgentState

        mock_tool = _create_mock_retrieved_tool("tool_1", "Test", ["category"])
        state = AgentState(
            messages=[],
            query="test",
            session_id="sess",
            retrieved_tools=[mock_tool],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert isinstance(state["retrieved_tools"], list)
        assert isinstance(state["retrieved_tools"][0], RetrievedTool)

    def test_agent_state_extracted_dimensions_is_extracted_dimensions(self) -> None:
        """AgentState.extracted_dimensions is an ExtractedDimensions instance."""
        from src.agent.state import AgentState

        dims = ExtractedDimensions(brand=["Nike"])
        state = AgentState(
            messages=[],
            query="test",
            session_id="sess",
            retrieved_tools=[],
            extracted_dimensions=dims,
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert isinstance(state["extracted_dimensions"], ExtractedDimensions)

    def test_agent_state_current_stage_is_str(self) -> None:
        """AgentState.current_stage is a string."""
        from src.agent.state import AgentState

        state = AgentState(
            messages=[],
            query="test",
            session_id="sess",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="dimension_extraction",
            error=None,
        )
        assert isinstance(state["current_stage"], str)

    def test_agent_state_error_is_optional_str(self) -> None:
        """AgentState.error is Optional[str]."""
        from src.agent.state import AgentState

        # None case
        state = AgentState(
            messages=[],
            query="test",
            session_id="sess",
            retrieved_tools=[],
            extracted_dimensions=ExtractedDimensions(),
            tool_selection_result=None,
            clarification=None,
            execution_plan=None,
            execution_results={},
            final_output=None,
            current_stage="init",
            error=None,
        )
        assert state["error"] is None

        # String case
        state["error"] = "Error message"
        assert state["error"] == "Error message"


class TestImports:
    """Test module imports."""

    def test_import_agent_state(self) -> None:
        """AgentState can be imported."""
        from src.agent.state import AgentState

        assert AgentState is not None

    def test_import_session_context(self) -> None:
        """SessionContext can be imported."""
        from src.agent.state import SessionContext

        assert SessionContext is not None

    def test_import_compute_dimension_match_score(self) -> None:
        """compute_dimension_match_score can be imported."""
        from src.agent.state import compute_dimension_match_score

        assert callable(compute_dimension_match_score)


# ============================================================================
# Helper Functions
# ============================================================================

def _create_mock_retrieved_tool(
    tool_id: str,
    name: str,
    required_dimensions: List[str],
    optional_dimensions: Optional[List[str]] = None,
) -> RetrievedTool:
    """Helper to create a mock RetrievedTool for testing."""
    return RetrievedTool(
        tool_id=tool_id,
        tool_definition=ToolDefinition(
            id=tool_id,
            name=name,
            description=f"Test tool: {name}",
            capabilities=[f"Capability for {name}"],
            required_dimensions=required_dimensions,
            optional_dimensions=optional_dimensions or [],
            parameters=[],
            output_schema=ToolOutputSchema(
                format="json",
                description=f"Output for {name}",
            ),
            example_queries=[f"Example query for {name}"],
            aliases=[name.lower().replace(" ", "_")],
            version="1.0.0",
        ),
        similarity=0.85,
        rank=1,
    )
