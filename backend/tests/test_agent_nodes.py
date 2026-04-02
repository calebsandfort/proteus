"""Tests for FR-2.4-2.6: Agent Nodes and Models.

This module tests the Pydantic models and node functions for:
- FR-2.4: Tool Selection LLM (ToolSelectionResult, compute_overall_confidence)
- FR-2.5: HITL Clarification (HITLClarification, ClarificationOption, clarification_node)
- FR-2.6: Multi-Tool Query Handling (ExecutionPlan, PlannedTool, planner_node, execution_node)

Test Requirements:
- Test Pydantic model validation
- Test helper functions (compute_overall_confidence, parse_json_response)
- Test node functions with mocked external dependencies
- Mock OpenRouterClient for LLM calls
- Mock httpx.AsyncClient for HTTP calls
"""

import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.api.models.dimensions import ExtractedDimensions
from src.api.models.tool import RetrievedTool, ToolDefinition, ToolOutputSchema, ToolParameter, OutputField


# ============================================================================
# Test Data: Mock Retrieved Tools
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


# ============================================================================
# Test FR-2.5: HITL Clarification Models
# ============================================================================

class TestClarificationOption:
    """Test ClarificationOption Pydantic model."""

    def test_clarification_option_valid(self) -> None:
        """ClarificationOption can be created with required fields."""
        from src.agent.nodes import ClarificationOption

        option = ClarificationOption(
            id="opt_1",
            label="Nike Brand Spending",
            interpreted_params={"brand": ["Nike"], "time_range": "last_quarter"},
            reasoning="Based on explicit mention of Nike brand",
        )
        assert option.id == "opt_1"
        assert option.label == "Nike Brand Spending"
        assert option.interpreted_params == {"brand": ["Nike"], "time_range": "last_quarter"}
        assert option.reasoning == "Based on explicit mention of Nike brand"

    def test_clarification_option_requires_id(self) -> None:
        """ClarificationOption requires id field."""
        from src.agent.nodes import ClarificationOption

        with pytest.raises(ValidationError) as exc_info:
            ClarificationOption(
                label="Test",
                interpreted_params={},
                reasoning="Test reasoning",
            )
        assert "id" in str(exc_info.value)

    def test_clarification_option_requires_label(self) -> None:
        """ClarificationOption requires label field."""
        from src.agent.nodes import ClarificationOption

        with pytest.raises(ValidationError) as exc_info:
            ClarificationOption(
                id="opt_1",
                interpreted_params={},
                reasoning="Test reasoning",
            )
        assert "label" in str(exc_info.value)

    def test_clarification_option_requires_interpreted_params(self) -> None:
        """ClarificationOption requires interpreted_params field."""
        from src.agent.nodes import ClarificationOption

        with pytest.raises(ValidationError) as exc_info:
            ClarificationOption(
                id="opt_1",
                label="Test",
                reasoning="Test reasoning",
            )
        assert "interpreted_params" in str(exc_info.value)

    def test_clarification_option_requires_reasoning(self) -> None:
        """ClarificationOption requires reasoning field."""
        from src.agent.nodes import ClarificationOption

        with pytest.raises(ValidationError) as exc_info:
            ClarificationOption(
                id="opt_1",
                label="Test",
                interpreted_params={},
            )
        assert "reasoning" in str(exc_info.value)


class TestHITLClarification:
    """Test HITLClarification Pydantic model."""

    def test_hitl_clarification_valid(self) -> None:
        """HITLClarification can be created with required fields."""
        from src.agent.nodes import ClarificationOption, HITLClarification

        clarification = HITLClarification(
            ambiguity_type="tool_selection",
            message="I'm not sure which tool to use for this query.",
            options=[
                ClarificationOption(
                    id="opt_1",
                    label="Option 1",
                    interpreted_params={"param": "value"},
                    reasoning="Reasoning 1",
                ),
                ClarificationOption(
                    id="opt_2",
                    label="Option 2",
                    interpreted_params={"param": "value2"},
                    reasoning="Reasoning 2",
                ),
            ],
            suggested_question="Did you mean...?",
        )
        assert clarification.ambiguity_type == "tool_selection"
        assert clarification.message == "I'm not sure which tool to use for this query."
        assert len(clarification.options) == 2
        assert clarification.suggested_question == "Did you mean...?"

    def test_hitl_clarification_requires_ambiguity_type(self) -> None:
        """HITLClarification requires ambiguity_type field."""
        from src.agent.nodes import HITLClarification

        with pytest.raises(ValidationError) as exc_info:
            HITLClarification(
                message="Test message",
                options=[],
            )
        assert "ambiguity_type" in str(exc_info.value)

    def test_hitl_clarification_requires_message(self) -> None:
        """HITLClarification requires message field."""
        from src.agent.nodes import HITLClarification

        with pytest.raises(ValidationError) as exc_info:
            HITLClarification(
                ambiguity_type="tool_selection",
                options=[],
            )
        assert "message" in str(exc_info.value)

    def test_hitl_clarification_requires_options(self) -> None:
        """HITLClarification requires options field."""
        from src.agent.nodes import HITLClarification

        with pytest.raises(ValidationError) as exc_info:
            HITLClarification(
                ambiguity_type="tool_selection",
                message="Test message",
            )
        assert "options" in str(exc_info.value)

    def test_hitl_clarification_optional_suggested_question(self) -> None:
        """HITLClarification suggested_question is optional."""
        from src.agent.nodes import HITLClarification

        clarification = HITLClarification(
            ambiguity_type="dimension_value",
            message="What do you mean by 'spending'?",
            options=[],
        )
        assert clarification.suggested_question is None

    def test_hitl_clarification_max_3_options(self) -> None:
        """HITLClarification options should be 2-3 max (FR-2.5)."""
        from src.agent.nodes import ClarificationOption, HITLClarification

        # 3 options is valid
        clarification = HITLClarification(
            ambiguity_type="tool_selection",
            message="Test",
            options=[
                ClarificationOption(id=f"opt_{i}", label=f"Opt {i}", interpreted_params={}, reasoning="r")
                for i in range(3)
            ],
        )
        assert len(clarification.options) == 3


# ============================================================================
# Test FR-2.4: Tool Selection Models
# ============================================================================

class TestToolSelectionResult:
    """Test ToolSelectionResult Pydantic model."""

    def test_tool_selection_result_valid(self) -> None:
        """ToolSelectionResult can be created with required fields."""
        from src.agent.nodes import ToolSelectionResult

        result = ToolSelectionResult(
            selected_tools=["tool_1", "tool_2"],
            confidence=0.92,
            confidence_breakdown={
                "rag_similarity": 0.85,
                "llm_selection": 0.95,
                "dimension_match": 0.90,
            },
            reasoning="Tools selected based on high confidence scores",
        )
        assert result.selected_tools == ["tool_1", "tool_2"]
        assert result.confidence == 0.92
        assert result.confidence_breakdown["rag_similarity"] == 0.85
        assert result.reasoning == "Tools selected based on high confidence scores"

    def test_tool_selection_result_requires_selected_tools(self) -> None:
        """ToolSelectionResult requires selected_tools field."""
        from src.agent.nodes import ToolSelectionResult

        with pytest.raises(ValidationError) as exc_info:
            ToolSelectionResult(
                confidence=0.9,
                confidence_breakdown={},
                reasoning="Test",
            )
        assert "selected_tools" in str(exc_info.value)

    def test_tool_selection_result_requires_confidence(self) -> None:
        """ToolSelectionResult requires confidence field."""
        from src.agent.nodes import ToolSelectionResult

        with pytest.raises(ValidationError) as exc_info:
            ToolSelectionResult(
                selected_tools=["tool_1"],
                confidence_breakdown={},
                reasoning="Test",
            )
        assert "confidence" in str(exc_info.value)

    def test_tool_selection_result_optional_competing_candidates(self) -> None:
        """ToolSelectionResult competing_candidates is optional."""
        from src.agent.nodes import ToolSelectionResult

        result = ToolSelectionResult(
            selected_tools=["tool_1"],
            confidence=0.92,
            confidence_breakdown={"rag_similarity": 0.8, "llm_selection": 0.9, "dimension_match": 1.0},
            reasoning="High confidence selection",
        )
        assert result.competing_candidates is None

    def test_tool_selection_result_with_competing_candidates(self) -> None:
        """ToolSelectionResult can include competing_candidates."""
        from src.agent.nodes import ToolSelectionResult

        result = ToolSelectionResult(
            selected_tools=["tool_1"],
            confidence=0.78,
            confidence_breakdown={"rag_similarity": 0.7, "llm_selection": 0.8, "dimension_match": 0.85},
            competing_candidates=["tool_2", "tool_3"],
            reasoning="Multiple good options available",
        )
        assert result.competing_candidates == ["tool_2", "tool_3"]


# ============================================================================
# Test FR-2.6: Execution Plan Models
# ============================================================================

class TestPlannedTool:
    """Test PlannedTool Pydantic model."""

    def test_planned_tool_valid(self) -> None:
        """PlannedTool can be created with required fields."""
        from src.agent.nodes import PlannedTool

        tool = PlannedTool(
            tool_id="spending_tool",
            order=0,
            parameters={"brand": "Nike", "time_range": "Q3 2024"},
            depends_on=[],
            can_parallelize=True,
        )
        assert tool.tool_id == "spending_tool"
        assert tool.order == 0
        assert tool.parameters == {"brand": "Nike", "time_range": "Q3 2024"}
        assert tool.depends_on == []
        assert tool.can_parallelize is True

    def test_planned_tool_requires_tool_id(self) -> None:
        """PlannedTool requires tool_id field."""
        from src.agent.nodes import PlannedTool

        with pytest.raises(ValidationError) as exc_info:
            PlannedTool(
                order=0,
                parameters={},
                can_parallelize=True,
            )
        assert "tool_id" in str(exc_info.value)

    def test_planned_tool_requires_order(self) -> None:
        """PlannedTool requires order field."""
        from src.agent.nodes import PlannedTool

        with pytest.raises(ValidationError) as exc_info:
            PlannedTool(
                tool_id="test_tool",
                parameters={},
                can_parallelize=True,
            )
        assert "order" in str(exc_info.value)

    def test_planned_tool_requires_parameters(self) -> None:
        """PlannedTool requires parameters field."""
        from src.agent.nodes import PlannedTool

        with pytest.raises(ValidationError) as exc_info:
            PlannedTool(
                tool_id="test_tool",
                order=0,
                can_parallelize=True,
            )
        assert "parameters" in str(exc_info.value)

    def test_planned_tool_default_depends_on(self) -> None:
        """PlannedTool depends_on defaults to empty list."""
        from src.agent.nodes import PlannedTool

        tool = PlannedTool(
            tool_id="test_tool",
            order=0,
            parameters={},
            can_parallelize=True,
        )
        assert tool.depends_on == []

    def test_planned_tool_with_dependencies(self) -> None:
        """PlannedTool can specify dependencies on other tools."""
        from src.agent.nodes import PlannedTool

        tool = PlannedTool(
            tool_id="detailed_spending",
            order=1,
            parameters={"brand": "Nike"},
            depends_on=["brand_lookup"],
            can_parallelize=False,
        )
        assert tool.depends_on == ["brand_lookup"]
        assert tool.can_parallelize is False


class TestExecutionPlan:
    """Test ExecutionPlan Pydantic model."""

    def test_execution_plan_valid(self) -> None:
        """ExecutionPlan can be created with required fields."""
        from src.agent.nodes import ExecutionPlan, PlannedTool

        plan = ExecutionPlan(
            plan_id="plan-123",
            is_multi_tool=True,
            tools=[
                PlannedTool(
                    tool_id="brand_lookup",
                    order=0,
                    parameters={},
                    depends_on=[],
                    can_parallelize=True,
                ),
                PlannedTool(
                    tool_id="spending_tool",
                    order=1,
                    parameters={"brand": "Nike"},
                    depends_on=["brand_lookup"],
                    can_parallelize=False,
                ),
            ],
            dimension_dependencies={"brand": [], "spending": ["brand"]},
            estimated_latency_ms=500,
            execution_mode="sequential",
            reasoning="Brand must be resolved before spending query",
        )
        assert plan.plan_id == "plan-123"
        assert plan.is_multi_tool is True
        assert len(plan.tools) == 2
        assert plan.estimated_latency_ms == 500
        assert plan.execution_mode == "sequential"

    def test_execution_plan_requires_plan_id(self) -> None:
        """ExecutionPlan requires plan_id field."""
        from src.agent.nodes import ExecutionPlan

        with pytest.raises(ValidationError) as exc_info:
            ExecutionPlan(
                is_multi_tool=False,
                tools=[],
                dimension_dependencies={},
                estimated_latency_ms=200,
                execution_mode="parallel",
            )
        assert "plan_id" in str(exc_info.value)

    def test_execution_plan_requires_is_multi_tool(self) -> None:
        """ExecutionPlan requires is_multi_tool field."""
        from src.agent.nodes import ExecutionPlan

        with pytest.raises(ValidationError) as exc_info:
            ExecutionPlan(
                plan_id="plan-123",
                tools=[],
                dimension_dependencies={},
                estimated_latency_ms=200,
                execution_mode="parallel",
            )
        assert "is_multi_tool" in str(exc_info.value)

    def test_execution_plan_single_tool_mode(self) -> None:
        """ExecutionPlan can represent single-tool queries."""
        from src.agent.nodes import ExecutionPlan, PlannedTool

        plan = ExecutionPlan(
            plan_id="plan-single",
            is_multi_tool=False,
            tools=[
                PlannedTool(
                    tool_id="spending_tool",
                    order=0,
                    parameters={"brand": "Nike"},
                    depends_on=[],
                    can_parallelize=True,
                ),
            ],
            dimension_dependencies={"brand": []},
            estimated_latency_ms=200,
            execution_mode="parallel",
            reasoning="Single tool query",
        )
        assert plan.is_multi_tool is False
        assert plan.execution_mode == "parallel"

    def test_execution_plan_optional_reasoning(self) -> None:
        """ExecutionPlan reasoning defaults to empty string."""
        from src.agent.nodes import ExecutionPlan

        plan = ExecutionPlan(
            plan_id="plan-123",
            is_multi_tool=False,
            tools=[],
            dimension_dependencies={},
            estimated_latency_ms=200,
            execution_mode="parallel",
        )
        assert plan.reasoning == ""


# ============================================================================
# Test AgentOutput Model
# ============================================================================

class TestAgentOutput:
    """Test AgentOutput Pydantic model."""

    def test_agent_output_valid(self) -> None:
        """AgentOutput can be created with required fields."""
        from src.agent.nodes import AgentOutput

        output = AgentOutput(
            answer="Your spending increased by 15% last quarter.",
            tool_results={"spending_tool": {"total": 5000, "change": 0.15}},
            visualizations=[{"type": "line_chart", "data": []}],
            suggestions=["Try comparing year-over-year trends", "Explore category breakdown"],
            session_context={"query_id": "q-123", "latency_ms": 250},
        )
        assert output.answer == "Your spending increased by 15% last quarter."
        assert output.tool_results["spending_tool"]["total"] == 5000
        assert len(output.visualizations) == 1
        assert len(output.suggestions) == 2
        assert output.session_context["query_id"] == "q-123"

    def test_agent_output_minimal(self) -> None:
        """AgentOutput can be created with only required fields."""
        from src.agent.nodes import AgentOutput

        output = AgentOutput(
            answer="Here is your answer.",
            tool_results={},
        )
        assert output.answer == "Here is your answer."
        assert output.tool_results == {}
        assert output.visualizations == []
        assert output.suggestions == []
        assert output.session_context == {}

    def test_agent_output_requires_answer(self) -> None:
        """AgentOutput requires answer field."""
        from src.agent.nodes import AgentOutput

        with pytest.raises(ValidationError) as exc_info:
            AgentOutput(
                tool_results={},
            )
        assert "answer" in str(exc_info.value)

    def test_agent_output_requires_tool_results(self) -> None:
        """AgentOutput requires tool_results field."""
        from src.agent.nodes import AgentOutput

        with pytest.raises(ValidationError) as exc_info:
            AgentOutput(
                answer="Test answer",
            )
        assert "tool_results" in str(exc_info.value)


# ============================================================================
# Test Helper Functions
# ============================================================================

class TestComputeOverallConfidence:
    """Test compute_overall_confidence helper function."""

    def test_compute_overall_confidence_import(self) -> None:
        """compute_overall_confidence can be imported."""
        from src.agent.nodes import compute_overall_confidence

        assert callable(compute_overall_confidence)

    def test_compute_overall_confidence_full_match(self) -> None:
        """compute_overall_confidence returns 1.0 for perfect scores."""
        from src.agent.nodes import compute_overall_confidence

        result = compute_overall_confidence(
            llm_confidence=1.0,
            rag_similarities=[1.0, 1.0],
            dim_match_score=1.0,
        )
        # 0.25 * 1.0 + 0.35 * 1.0 + 0.40 * 1.0 = 1.0
        assert result == 1.0

    def test_compute_overall_confidence_zero_match(self) -> None:
        """compute_overall_confidence returns 0.0 for all zero scores."""
        from src.agent.nodes import compute_overall_confidence

        result = compute_overall_confidence(
            llm_confidence=0.0,
            rag_similarities=[0.0, 0.0],
            dim_match_score=0.0,
        )
        # 0.25 * 0.0 + 0.35 * 0.0 + 0.40 * 0.0 = 0.0
        assert result == 0.0

    def test_compute_overall_confidence_weighted_calculation(self) -> None:
        """compute_overall_confidence uses correct weights: 0.25 RAG + 0.35 LLM + 0.40 dim."""
        from src.agent.nodes import compute_overall_confidence

        result = compute_overall_confidence(
            llm_confidence=0.8,
            rag_similarities=[0.6, 0.8],  # avg = 0.7
            dim_match_score=1.0,
        )
        # 0.25 * 0.7 + 0.35 * 0.8 + 0.40 * 1.0
        # = 0.175 + 0.28 + 0.4 = 0.855
        assert abs(result - 0.855) < 0.001

    def test_compute_overall_confidence_single_rag_score(self) -> None:
        """compute_overall_confidence handles single RAG score."""
        from src.agent.nodes import compute_overall_confidence

        result = compute_overall_confidence(
            llm_confidence=0.5,
            rag_similarities=[0.7],  # single score, avg = 0.7
            dim_match_score=0.5,
        )
        # 0.25 * 0.7 + 0.35 * 0.5 + 0.40 * 0.5
        # = 0.175 + 0.175 + 0.2 = 0.55
        assert abs(result - 0.55) < 0.001

    def test_compute_overall_confidence_empty_rag_scores(self) -> None:
        """compute_overall_confidence handles empty RAG scores."""
        from src.agent.nodes import compute_overall_confidence

        result = compute_overall_confidence(
            llm_confidence=0.5,
            rag_similarities=[],  # empty, avg treated as 0
            dim_match_score=0.5,
        )
        # 0.25 * 0 + 0.35 * 0.5 + 0.40 * 0.5 = 0.375
        assert abs(result - 0.375) < 0.001


class TestParseJsonResponse:
    """Test parse_json_response helper function."""

    def test_parse_json_response_import(self) -> None:
        """parse_json_response can be imported."""
        from src.agent.nodes import parse_json_response

        assert callable(parse_json_response)

    def test_parse_json_response_valid_json(self) -> None:
        """parse_json_response parses valid JSON."""
        from src.agent.nodes import parse_json_response

        result = parse_json_response('{"key": "value", "number": 42}')
        assert result == {"key": "value", "number": 42}

    def test_parse_json_response_with_whitespace(self) -> None:
        """parse_json_response handles extra whitespace."""
        from src.agent.nodes import parse_json_response

        result = parse_json_response('  {"key": "value"}  \n')
        assert result == {"key": "value"}

    def test_parse_json_response_invalid_json(self) -> None:
        """parse_json_response returns empty dict on invalid JSON."""
        from src.agent.nodes import parse_json_response

        result = parse_json_response("not valid json at all")
        assert result == {}

    def test_parse_json_response_partial_json(self) -> None:
        """parse_json_response extracts JSON object from mixed content."""
        from src.agent.nodes import parse_json_response

        # Content has text before and after JSON
        content = 'Here is the response: {"selected_tools": ["tool_1"], "confidence": 0.9} for you.'
        result = parse_json_response(content)
        assert result == {"selected_tools": ["tool_1"], "confidence": 0.9}

    def test_parse_json_response_empty_string(self) -> None:
        """parse_json_response returns empty dict for empty string."""
        from src.agent.nodes import parse_json_response

        result = parse_json_response("")
        assert result == {}

    def test_parse_json_response_json_array(self) -> None:
        """parse_json_response can parse JSON arrays."""
        from src.agent.nodes import parse_json_response

        result = parse_json_response('["tool_1", "tool_2", "tool_3"]')
        assert result == ["tool_1", "tool_2", "tool_3"]


# ============================================================================
# Test Node Functions
# ============================================================================

class TestToolSelectionNode:
    """Test tool_selection_node function."""

    @pytest.mark.asyncio
    async def test_tool_selection_node_import(self) -> None:
        """tool_selection_node can be imported."""
        from src.agent.nodes import tool_selection_node

        assert callable(tool_selection_node)

    @pytest.mark.asyncio
    async def test_tool_selection_node_high_confidence(self) -> None:
        """tool_selection_node proceeds to execution when confidence >= 0.85."""
        from src.agent.nodes import tool_selection_node

        mock_tool = _create_mock_retrieved_tool("spending_tool", "Spending Analysis", ["brand", "time_range"])

        # Mock OpenRouterClient
        with patch("src.agent.nodes.OpenRouterClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.call_with_retry = AsyncMock(
                return_value={
                    "tool_calls": [
                        {
                            "parsed": {
                                "selected_tools": ["spending_tool"],
                                "confidence": 0.92,
                                "confidence_breakdown": {
                                    "rag_similarity": 0.85,
                                    "llm_selection": 0.95,
                                    "dimension_match": 0.90,
                                },
                                "reasoning": "High confidence match",
                            }
                        }
                    ]
                }
            )

            state = {
                "messages": [],
                "query": "Show me Nike spending last quarter",
                "session_id": "test-session",
                "retrieved_tools": [mock_tool],
                "extracted_dimensions": ExtractedDimensions(
                    brand=["Nike"],
                    time_range={"start": "2024-07-01", "end": "2024-09-30"},
                ),
                "tool_selection_result": None,
                "clarification": None,
                "execution_plan": None,
                "execution_results": {},
                "final_output": None,
                "current_stage": "retrieval",
                "error": None,
            }

            result = await tool_selection_node(state)

            assert result["current_stage"] == "execution"
            assert result["tool_selection_result"] is not None
            assert result["tool_selection_result"].confidence >= 0.85
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_tool_selection_node_low_confidence_triggers_clarification(self) -> None:
        """tool_selection_node sets clarification when confidence < 0.70."""
        from src.agent.nodes import tool_selection_node

        mock_tool = _create_mock_retrieved_tool("ambiguous_tool", "Ambiguous Tool", ["category"])

        with patch("src.agent.nodes.OpenRouterClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.call_with_retry = AsyncMock(
                return_value={
                    "tool_calls": [
                        {
                            "parsed": {
                                "selected_tools": [],
                                "confidence": 0.45,
                                "confidence_breakdown": {
                                    "rag_similarity": 0.5,
                                    "llm_selection": 0.4,
                                    "dimension_match": 0.5,
                                },
                                "reasoning": "Low confidence - need clarification",
                            }
                        }
                    ]
                }
            )

            state = {
                "messages": [],
                "query": "Show me spending",
                "session_id": "test-session",
                "retrieved_tools": [mock_tool],
                "extracted_dimensions": ExtractedDimensions(),
                "tool_selection_result": None,
                "clarification": None,
                "execution_plan": None,
                "execution_results": {},
                "final_output": None,
                "current_stage": "retrieval",
                "error": None,
            }

            result = await tool_selection_node(state)

            assert result["current_stage"] == "clarification"
            assert result["clarification"] is not None
            assert result["clarification"].ambiguity_type == "tool_selection"

    @pytest.mark.asyncio
    async def test_tool_selection_node_medium_confidence_with_candidates(self) -> None:
        """tool_selection_node shows competing candidates when confidence 0.70-0.84."""
        from src.agent.nodes import tool_selection_node

        mock_tool_1 = _create_mock_retrieved_tool("spending_tool", "Spending Tool", ["brand"])
        mock_tool_2 = _create_mock_retrieved_tool("category_tool", "Category Tool", ["category"])

        with patch("src.agent.nodes.OpenRouterClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.call_with_retry = AsyncMock(
                return_value={
                    "tool_calls": [
                        {
                            "parsed": {
                                "selected_tools": ["spending_tool"],
                                "confidence": 0.78,
                                "confidence_breakdown": {
                                    "rag_similarity": 0.7,
                                    "llm_selection": 0.8,
                                    "dimension_match": 0.85,
                                },
                                "competing_candidates": ["category_tool"],
                                "reasoning": "Multiple tools could work",
                            }
                        }
                    ]
                }
            )

            state = {
                "messages": [],
                "query": "Show me Nike spending",
                "session_id": "test-session",
                "retrieved_tools": [mock_tool_1, mock_tool_2],
                "extracted_dimensions": ExtractedDimensions(brand=["Nike"]),
                "tool_selection_result": None,
                "clarification": None,
                "execution_plan": None,
                "execution_results": {},
                "final_output": None,
                "current_stage": "retrieval",
                "error": None,
            }

            result = await tool_selection_node(state)

            assert result["current_stage"] == "execution"
            assert result["tool_selection_result"] is not None
            assert result["tool_selection_result"].confidence == 0.78
            assert result["tool_selection_result"].competing_candidates == ["category_tool"]


class TestPlannerNode:
    """Test planner_node function."""

    @pytest.mark.asyncio
    async def test_planner_node_import(self) -> None:
        """planner_node can be imported."""
        from src.agent.nodes import planner_node

        assert callable(planner_node)

    @pytest.mark.asyncio
    async def test_planner_node_single_tool(self) -> None:
        """planner_node handles single-tool query."""
        from src.agent.nodes import planner_node, ToolSelectionResult

        with patch("src.agent.nodes.OpenRouterClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.call_with_retry = AsyncMock(
                return_value={
                    "tool_calls": [
                        {
                            "parsed": {
                                "plan_id": "plan-123",
                                "is_multi_tool": False,
                                "tools": [
                                    {
                                        "tool_id": "spending_tool",
                                        "order": 0,
                                        "parameters": {"brand": "Nike"},
                                        "depends_on": [],
                                        "can_parallelize": True,
                                    }
                                ],
                                "dimension_dependencies": {"brand": []},
                                "estimated_latency_ms": 200,
                                "execution_mode": "parallel",
                                "reasoning": "Single tool query",
                            }
                        }
                    ]
                }
            )

            tool_selection = ToolSelectionResult(
                selected_tools=["spending_tool"],
                confidence=0.92,
                confidence_breakdown={"rag_similarity": 0.85, "llm_selection": 0.95, "dimension_match": 0.90},
                reasoning="High confidence",
            )

            state = {
                "messages": [],
                "query": "Show me Nike spending last quarter",
                "session_id": "test-session",
                "retrieved_tools": [],
                "extracted_dimensions": ExtractedDimensions(brand=["Nike"]),
                "tool_selection_result": tool_selection,
                "clarification": None,
                "execution_plan": None,
                "execution_results": {},
                "final_output": None,
                "current_stage": "tool_selection",
                "error": None,
            }

            result = await planner_node(state)

            assert result["current_stage"] == "execution"
            assert result["execution_plan"] is not None
            assert result["execution_plan"].is_multi_tool is False
            assert result["execution_plan"].execution_mode == "parallel"

    @pytest.mark.asyncio
    async def test_planner_node_multi_tool_sequential(self) -> None:
        """planner_node handles multi-tool query with dependencies."""
        from src.agent.nodes import planner_node, ToolSelectionResult

        with patch("src.agent.nodes.OpenRouterClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.call_with_retry = AsyncMock(
                return_value={
                    "tool_calls": [
                        {
                            "parsed": {
                                "plan_id": "plan-456",
                                "is_multi_tool": True,
                                "tools": [
                                    {
                                        "tool_id": "brand_lookup",
                                        "order": 0,
                                        "parameters": {},
                                        "depends_on": [],
                                        "can_parallelize": True,
                                    },
                                    {
                                        "tool_id": "spending_tool",
                                        "order": 1,
                                        "parameters": {"brand_id": "brand_123"},
                                        "depends_on": ["brand_lookup"],
                                        "can_parallelize": False,
                                    },
                                ],
                                "dimension_dependencies": {"brand": [], "spending": ["brand"]},
                                "estimated_latency_ms": 500,
                                "execution_mode": "sequential",
                                "reasoning": "Brand must be resolved first",
                            }
                        }
                    ]
                }
            )

            tool_selection = ToolSelectionResult(
                selected_tools=["brand_lookup", "spending_tool"],
                confidence=0.88,
                confidence_breakdown={"rag_similarity": 0.8, "llm_selection": 0.9, "dimension_match": 0.95},
                reasoning="Multi-tool query",
            )

            state = {
                "messages": [],
                "query": "Compare Nike and Adidas spending trends",
                "session_id": "test-session",
                "retrieved_tools": [],
                "extracted_dimensions": ExtractedDimensions(brand=["Nike", "Adidas"]),
                "tool_selection_result": tool_selection,
                "clarification": None,
                "execution_plan": None,
                "execution_results": {},
                "final_output": None,
                "current_stage": "tool_selection",
                "error": None,
            }

            result = await planner_node(state)

            assert result["current_stage"] == "execution"
            assert result["execution_plan"] is not None
            assert result["execution_plan"].is_multi_tool is True
            assert result["execution_plan"].execution_mode == "sequential"
            assert len(result["execution_plan"].tools) == 2


class TestClarificationNode:
    """Test clarification_node function."""

    @pytest.mark.asyncio
    async def test_clarification_node_import(self) -> None:
        """clarification_node can be imported."""
        from src.agent.nodes import clarification_node

        assert callable(clarification_node)

    @pytest.mark.asyncio
    async def test_clarification_node_generates_options(self) -> None:
        """clarification_node generates clarification options."""
        from src.agent.nodes import clarification_node, HITLClarification

        with patch("src.agent.nodes.OpenRouterClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.call_with_retry = AsyncMock(
                return_value={
                    "tool_calls": [
                        {
                            "parsed": {
                                "ambiguity_type": "tool_selection",
                                "message": "I wasn't sure which tool to select.",
                                "options": [
                                    {
                                        "id": "opt_1",
                                        "label": "Spending Analysis",
                                        "interpreted_params": {"tool": "spending_tool"},
                                        "reasoning": "Most likely based on query",
                                    },
                                    {
                                        "id": "opt_2",
                                        "label": "Category Breakdown",
                                        "interpreted_params": {"tool": "category_tool"},
                                        "reasoning": "Query mentions category",
                                    },
                                ],
                                "suggested_question": "Did you want spending or category analysis?",
                            }
                        }
                    ]
                }
            )

            state = {
                "messages": [],
                "query": "Show me my spending",
                "session_id": "test-session",
                "retrieved_tools": [],
                "extracted_dimensions": ExtractedDimensions(),
                "tool_selection_result": None,
                "clarification": None,
                "execution_plan": None,
                "execution_results": {},
                "final_output": None,
                "current_stage": "clarification",
                "error": None,
            }

            result = await clarification_node(state)

            assert result["current_stage"] == "awaiting_clarification_response"
            assert result["clarification"] is not None
            assert isinstance(result["clarification"], HITLClarification)
            assert len(result["clarification"].options) == 2


class TestExecutionNode:
    """Test execution_node function."""

    @pytest.mark.asyncio
    async def test_execution_node_import(self) -> None:
        """execution_node can be imported."""
        from src.agent.nodes import execution_node

        assert callable(execution_node)

    @pytest.mark.asyncio
    async def test_execution_node_parallel_execution(self) -> None:
        """execution_node executes independent tools in parallel."""
        from src.agent.nodes import execution_node, ExecutionPlan, PlannedTool

        plan = ExecutionPlan(
            plan_id="plan-123",
            is_multi_tool=True,
            tools=[
                PlannedTool(
                    tool_id="tool_1",
                    order=0,
                    parameters={},
                    depends_on=[],
                    can_parallelize=True,
                ),
                PlannedTool(
                    tool_id="tool_2",
                    order=1,
                    parameters={},
                    depends_on=[],
                    can_parallelize=True,
                ),
            ],
            dimension_dependencies={},
            estimated_latency_ms=300,
            execution_mode="parallel",
        )

        with patch("src.agent.nodes.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful responses
            async def mock_post(url, **kwargs):
                response = AsyncMock()
                if "tool_1" in str(url):
                    response.json = AsyncMock(return_value={"result": "data1"})
                else:
                    response.json = AsyncMock(return_value={"result": "data2"})
                response.raise_for_status = AsyncMock()
                return response

            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            state = {
                "messages": [],
                "query": "Test query",
                "session_id": "test-session",
                "retrieved_tools": [],
                "extracted_dimensions": ExtractedDimensions(),
                "tool_selection_result": None,
                "clarification": None,
                "execution_plan": plan,
                "execution_results": {},
                "final_output": None,
                "current_stage": "execution",
                "error": None,
            }

            result = await execution_node(state)

            assert "tool_1" in result["execution_results"]
            assert "tool_2" in result["execution_results"]
            assert result["current_stage"] == "response_synthesis"
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_execution_node_sequential_with_deps(self) -> None:
        """execution_node executes dependent tools sequentially."""
        from src.agent.nodes import execution_node, ExecutionPlan, PlannedTool

        plan = ExecutionPlan(
            plan_id="plan-456",
            is_multi_tool=True,
            tools=[
                PlannedTool(
                    tool_id="brand_lookup",
                    order=0,
                    parameters={"brand_name": "Nike"},
                    depends_on=[],
                    can_parallelize=False,
                ),
                PlannedTool(
                    tool_id="spending_tool",
                    order=1,
                    parameters={"brand_id": "brand_123"},
                    depends_on=["brand_lookup"],
                    can_parallelize=False,
                ),
            ],
            dimension_dependencies={"brand": [], "spending": ["brand"]},
            estimated_latency_ms=500,
            execution_mode="sequential",
        )

        with patch("src.agent.nodes.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock responses with dependency chain
            responses = {
                "brand_lookup": {"brand_id": "brand_123"},
                "spending_tool": {"total_spending": 5000},
            }

            async def mock_post(url, **kwargs):
                response = AsyncMock()
                tool_id = "brand_lookup" if "brand_lookup" in str(url) else "spending_tool"
                response.json = AsyncMock(return_value=responses[tool_id])
                response.raise_for_status = AsyncMock()
                return response

            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            state = {
                "messages": [],
                "query": "Test query",
                "session_id": "test-session",
                "retrieved_tools": [],
                "extracted_dimensions": ExtractedDimensions(brand=["Nike"]),
                "tool_selection_result": None,
                "clarification": None,
                "execution_plan": plan,
                "execution_results": {},
                "final_output": None,
                "current_stage": "execution",
                "error": None,
            }

            result = await execution_node(state)

            assert "brand_lookup" in result["execution_results"]
            assert "spending_tool" in result["execution_results"]
            # spending_tool should have access to brand_lookup results
            assert result["execution_results"]["spending_tool"]["brand_id"] == "brand_123"


# ============================================================================
# Test Model Imports
# ============================================================================

class TestModelImports:
    """Test that all models can be imported from nodes module."""

    def test_import_clarification_option(self) -> None:
        """ClarificationOption can be imported."""
        from src.agent.nodes import ClarificationOption

        assert ClarificationOption is not None

    def test_import_hitl_clarification(self) -> None:
        """HITLClarification can be imported."""
        from src.agent.nodes import HITLClarification

        assert HITLClarification is not None

    def test_import_tool_selection_result(self) -> None:
        """ToolSelectionResult can be imported."""
        from src.agent.nodes import ToolSelectionResult

        assert ToolSelectionResult is not None

    def test_import_planned_tool(self) -> None:
        """PlannedTool can be imported."""
        from src.agent.nodes import PlannedTool

        assert PlannedTool is not None

    def test_import_execution_plan(self) -> None:
        """ExecutionPlan can be imported."""
        from src.agent.nodes import ExecutionPlan

        assert ExecutionPlan is not None

    def test_import_agent_output(self) -> None:
        """AgentOutput can be imported."""
        from src.agent.nodes import AgentOutput

        assert AgentOutput is not None
