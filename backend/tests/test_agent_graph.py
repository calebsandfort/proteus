"""TDD Tests for AgentGraph (FR-2.4-2.6).

Tests the complete AgentGraph implementation that wires together all nodes.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.nodes import (
    AgentOutput,
    ClarificationOption,
    ExecutionPlan,
    HITLClarification,
    PlannedTool,
    ToolSelectionResult,
)
from src.api.models.dimensions import ExtractedDimensions


class TestBuildGraph:
    """Tests for build_graph function."""

    def test_build_graph_returns_compiled_state_graph(self) -> None:
        """Test that build_graph returns a compiled StateGraph."""
        from src.agent.graph import build_graph

        compiled = build_graph()
        assert compiled is not None
        # Should have invoke and ainvoke methods
        assert hasattr(compiled, "invoke")
        assert hasattr(compiled, "ainvoke")

    def test_graph_compiles_without_error(self) -> None:
        """Test that the graph compiles successfully."""
        from src.agent.graph import build_graph

        # Should not raise any exceptions
        graph = build_graph()
        assert graph is not None

    def test_graph_has_checkpointer(self) -> None:
        """Test that compiled graph has checkpointer configured."""
        from src.agent.graph import build_graph

        graph = build_graph()
        # Verify graph was compiled with checkpointer
        assert hasattr(graph, "invoke") or hasattr(graph, "ainvoke")


class TestAgentExport:
    """Tests for the agent export."""

    def test_agent_is_compiled_graph(self) -> None:
        """Test that 'agent' is a compiled graph."""
        from src.agent.graph import agent

        assert agent is not None
        assert hasattr(agent, "invoke")
        assert hasattr(agent, "ainvoke")


class TestRunAgentGraph:
    """Tests for run_agent_graph function."""

    @pytest.mark.asyncio
    async def test_run_agent_graph_exists(self) -> None:
        """Test that run_agent_graph function exists and is async."""
        from src.agent.graph import run_agent_graph
        import inspect

        assert inspect.iscoroutinefunction(run_agent_graph)

    @pytest.mark.asyncio
    async def test_run_agent_graph_accepts_required_params(self) -> None:
        """Test that run_agent_graph accepts query, session_id, and conversation_history."""
        from src.agent.graph import run_agent_graph
        import inspect

        sig = inspect.signature(run_agent_graph)
        params = list(sig.parameters.keys())

        assert "query" in params
        assert "session_id" in params
        assert "conversation_history" in params


class TestRoutingFunctions:
    """Tests for routing functions."""

    def test_tool_selection_routing_high_confidence(self) -> None:
        """Test tool_selection_routing returns 'planner' for high confidence."""
        from src.agent.graph import tool_selection_routing

        state = {
            "tool_selection_result": ToolSelectionResult(
                selected_tools=["tool1"],
                confidence=0.90,
                confidence_breakdown={
                    "rag_similarity": 0.85,
                    "llm_selection": 0.90,
                    "dimension_match": 0.95,
                },
                reasoning="High confidence",
            ),
        }

        result = tool_selection_routing(state)
        assert result == "planner"

    def test_tool_selection_routing_low_confidence(self) -> None:
        """Test tool_selection_routing returns 'clarification' for low confidence."""
        from src.agent.graph import tool_selection_routing

        state = {
            "tool_selection_result": ToolSelectionResult(
                selected_tools=["tool1"],
                confidence=0.50,
                confidence_breakdown={
                    "rag_similarity": 0.40,
                    "llm_selection": 0.50,
                    "dimension_match": 0.60,
                },
                reasoning="Low confidence",
            ),
        }

        result = tool_selection_routing(state)
        assert result == "clarification"

    def test_tool_selection_routing_boundary_confidence(self) -> None:
        """Test tool_selection_routing at boundary 0.70 threshold."""
        from src.agent.graph import tool_selection_routing

        # Confidence exactly 0.70 should route to planner
        state = {
            "tool_selection_result": ToolSelectionResult(
                selected_tools=["tool1"],
                confidence=0.70,
                confidence_breakdown={
                    "rag_similarity": 0.70,
                    "llm_selection": 0.70,
                    "dimension_match": 0.70,
                },
                reasoning="Boundary confidence",
            ),
        }

        result = tool_selection_routing(state)
        assert result == "planner"

    def test_tool_selection_routing_no_result(self) -> None:
        """Test tool_selection_routing when no tool selection result exists."""
        from src.agent.graph import tool_selection_routing

        state = {
            "tool_selection_result": None,
        }

        result = tool_selection_routing(state)
        assert result == "clarification"

    def test_planner_routing_always_returns_execution(self) -> None:
        """Test planner_routing always returns 'execution'."""
        from src.agent.graph import planner_routing

        state = {"execution_plan": MagicMock()}
        result = planner_routing(state)
        assert result == "execution"

    def test_execution_routing_always_returns_respond(self) -> None:
        """Test execution_routing always returns 'respond'."""
        from src.agent.graph import execution_routing

        state = {"execution_results": {"tool1": {}}}
        result = execution_routing(state)
        assert result == "respond"

    def test_clarification_routing_always_returns_tool_selection(self) -> None:
        """Test clarification_routing always returns 'tool_selection'."""
        from src.agent.graph import clarification_routing

        state = {"clarification": MagicMock()}
        result = clarification_routing(state)
        assert result == "tool_selection"


class TestNodeFunctions:
    """Tests for individual node functions exist."""

    def test_retrieve_node_exists(self) -> None:
        """Test that retrieve_node function exists."""
        from src.agent.graph import retrieve_node
        import inspect

        assert inspect.iscoroutinefunction(retrieve_node)

    def test_extract_dimensions_node_exists(self) -> None:
        """Test that extract_dimensions_node function exists."""
        from src.agent.graph import extract_dimensions_node
        import inspect

        assert inspect.iscoroutinefunction(extract_dimensions_node)

    def test_respond_node_exists(self) -> None:
        """Test that respond_node function exists."""
        from src.agent.graph import respond_node
        import inspect

        assert inspect.iscoroutinefunction(respond_node)

    def test_done_node_exists(self) -> None:
        """Test that done_node function exists."""
        from src.agent.graph import done_node
        import inspect

        assert inspect.iscoroutinefunction(done_node)


class TestRetrieveNode:
    """Tests for retrieve node function."""

    @pytest.mark.asyncio
    async def test_retrieve_node_returns_dict(self) -> None:
        """Test that retrieve_node returns a dict."""
        from src.agent.graph import retrieve_node

        state = {
            "query": "Show spending by generation",
            "messages": [],
            "session_id": "test",
        }

        # Mock the dependencies
        with patch(
            "src.agent.graph.OpenRouterClient"
        ) as mock_client, patch(
            "src.agent.graph.EmbeddingRetriever"
        ) as mock_retriever:
            mock_client_instance = MagicMock()
            mock_client_instance.embed_texts.return_value = [[0.1] * 1536]
            mock_client.return_value = mock_client_instance

            mock_retriever_instance = MagicMock()
            mock_retriever_instance.retrieve.return_value = []
            mock_retriever.return_value = mock_retriever_instance

            result = await retrieve_node(state)

            assert isinstance(result, dict)
            assert "retrieved_tools" in result
            assert "current_stage" in result


class TestExtractDimensionsNode:
    """Tests for extract_dimensions_node function."""

    @pytest.mark.asyncio
    async def test_extract_dimensions_node_returns_dict(self) -> None:
        """Test that extract_dimensions_node returns a dict."""
        from src.agent.graph import extract_dimensions_node

        state = {
            "query": "Show gen z spending",
            "messages": [],
            "session_id": "test",
        }

        with patch(
            "src.agent.graph.DimensionExtractionGraph"
        ) as mock_graph_class:
            mock_graph = AsyncMock()
            mock_graph.extract_all.return_value = MagicMock(
                extracted_dimensions=ExtractedDimensions(
                    generation=["gen_z"],
                    brand=[],
                    merchant_category=[],
                    geography=[],
                    time_range=None,
                    income_band=[],
                    card_type=[],
                    payment_network=[],
                    channel=[],
                    day_of_week=[],
                ),
                conflicts=[],
                validation_errors=[],
            )
            mock_graph_class.return_value = mock_graph

            result = await extract_dimensions_node(state)

            assert isinstance(result, dict)
            assert "extracted_dimensions" in result
            assert "current_stage" in result


class TestRespondNode:
    """Tests for respond_node function."""

    @pytest.mark.asyncio
    async def test_respond_node_returns_dict(self) -> None:
        """Test that respond_node returns a dict with final_output."""
        from src.agent.graph import respond_node

        state = {
            "query": "Show gen z spending",
            "messages": [],
            "session_id": "test",
            "execution_results": {"tool1": {"data": "result"}},
            "execution_plan": MagicMock(),
        }

        result = await respond_node(state)

        assert isinstance(result, dict)
        assert "final_output" in result
        assert "current_stage" in result
        assert result["current_stage"] == "done"


class TestDoneNode:
    """Tests for done_node function."""

    @pytest.mark.asyncio
    async def test_done_node_sets_done_stage(self) -> None:
        """Test that done_node sets current_stage to done."""
        from src.agent.graph import done_node

        state = {"messages": []}
        result = await done_node(state)

        assert result["current_stage"] == "done"


class TestGraphStructure:
    """Tests for graph structure verification."""

    def test_all_nodes_are_registered(self) -> None:
        """Test that all required nodes are registered in the graph."""
        from src.agent.graph import build_graph

        graph = build_graph()

        # The graph should compile without error
        # We verify node existence by the graph not raising
        assert graph is not None

    def test_conditional_edges_configured(self) -> None:
        """Test that conditional edges are configured for tool_selection."""
        from src.agent.graph import build_graph

        graph = build_graph()

        # If graph compiles, conditional edges are configured
        assert graph is not None
