"""FR-2.4-2.6: AgentState Schema and SessionContext.

This module defines the state schema for the LangGraph Agent system.

FR Requirements:
- FR-2.4: Tool Selection LLM (dimension match scoring function)
- FR-2.5: HITL Clarification (clarification field in state)
- FR-2.6: Multi-Tool Query Handling (planner node output types)

Models:
    SessionContext: Session-level context for tracking
    ClarificationOption: Option for HITL clarification
    HITLClarification: Human-in-the-loop clarification structure
    ToolSelectionResult: Result from tool selection LLM
    PlannedTool: Tool planned for execution
    ExecutionPlan: Complete execution plan for multi-tool queries
    AgentOutput: Final result output from the agent
    AgentState: Main state TypedDict for the agent graph
    compute_dimension_match_score: Dimension matching function for tool selection
"""

from typing import Annotated, Any, Dict, List, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# Import from existing modules (IU-4, IU-5)
from src.api.models.dimensions import ExtractedDimensions
from src.api.models.tool import RetrievedTool


# ============================================================================
# FR-2.4-2.6: Pydantic Models for Agent State
# ============================================================================


class ClarificationOption(BaseModel):
    """Option for HITL clarification.

    FR-2.5: When confidence < 0.70, the system presents 2-3 options
    for the user to choose from to resolve ambiguity.

    Attributes:
        id: Unique identifier for this option.
        label: Short label for UI display.
        interpreted_params: The resolved parameters for this option.
        reasoning: Explanation of why this option was generated.
    """

    id: str = Field(..., description="Unique identifier for this option")
    label: str = Field(..., description="Short label for UI display")
    interpreted_params: Dict[str, Any] = Field(
        ..., description="The resolved parameters for this option"
    )
    reasoning: str = Field(..., description="Explanation of why this option was generated")


class HITLClarification(BaseModel):
    """Human-in-the-loop clarification structure.

    FR-2.5: When confidence < 0.70, the system generates a structured
    clarification with 2-3 options for the user to choose from.

    Attributes:
        ambiguity_type: Type of ambiguity (tool_selection, dimension_value, conflicting_dimensions).
        message: User-friendly explanation of the ambiguity.
        options: List of clarification options (2-3 max).
        suggested_question: Optional question to help resolve ambiguity.
    """

    ambiguity_type: str = Field(
        ...,
        description="Type of ambiguity: tool_selection, dimension_value, or conflicting_dimensions"
    )
    message: str = Field(..., description="User-friendly explanation of the ambiguity")
    options: List[ClarificationOption] = Field(
        ..., description="List of clarification options (2-3 max)"
    )
    suggested_question: Optional[str] = Field(
        default=None, description="Optional question to help resolve ambiguity"
    )


class ToolSelectionResult(BaseModel):
    """Result from tool selection LLM.

    FR-2.4: Tool selection uses MiniMax-Text-01 via OpenRouter.
    Confidence = 25% RAG similarity + 35% LLM selection + 40% dimension match.

    Attributes:
        selected_tools: List of selected tool IDs.
        confidence: Overall confidence score (0.0 - 1.0).
        confidence_breakdown: Individual confidence components.
        competing_candidates: Alternative tools if confidence 0.70-0.84.
        reasoning: Explanation of selection decision.
    """

    selected_tools: List[str] = Field(..., description="List of selected tool IDs")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score (0.0 - 1.0)")
    confidence_breakdown: Dict[str, float] = Field(
        ..., description="Individual confidence components: rag_similarity, llm_selection, dimension_match"
    )
    competing_candidates: Optional[List[str]] = Field(
        default=None, description="Alternative tools if confidence 0.70-0.84"
    )
    reasoning: str = Field(..., description="Explanation of selection decision")


class PlannedTool(BaseModel):
    """Tool planned for execution.

    FR-2.6: Represents a single tool execution with resolved parameters
    and dependency information.

    Attributes:
        tool_id: ID of the tool to execute.
        order: Execution order (0-based).
        parameters: Resolved parameters from dimension extraction.
        depends_on: List of tool IDs this depends on.
        can_parallelize: True if no dependencies on other planned tools.
    """

    tool_id: str = Field(..., description="ID of the tool to execute")
    order: int = Field(..., ge=0, description="Execution order (0-based)")
    parameters: Dict[str, Any] = Field(..., description="Resolved parameters from dimension extraction")
    depends_on: List[str] = Field(
        default_factory=list, description="List of tool IDs this depends on"
    )
    can_parallelize: bool = Field(
        ..., description="True if no dependencies on other planned tools"
    )


class ExecutionPlan(BaseModel):
    """Complete execution plan for multi-tool queries.

    FR-2.6: Planner node generates an execution plan that determines
    tool ordering, dependencies, and execution mode.

    Attributes:
        plan_id: Unique identifier for this plan.
        is_multi_tool: True if multiple tools need to be executed.
        tools: Ordered list of tools to execute.
        dimension_dependencies: Dimension-level dependencies.
        estimated_latency_ms: Estimated total execution time.
        execution_mode: "parallel" or "sequential".
        reasoning: Explanation of planning decision.
    """

    plan_id: str = Field(..., description="Unique identifier for this plan")
    is_multi_tool: bool = Field(..., description="True if multiple tools need to be executed")
    tools: List[PlannedTool] = Field(..., description="Ordered list of tools to execute")
    dimension_dependencies: Dict[str, List[str]] = Field(
        ..., description="Dimension-level dependencies: {dimension: [dependent_dimensions]}"
    )
    estimated_latency_ms: int = Field(..., ge=0, description="Estimated total execution time in ms")
    execution_mode: str = Field(..., description="Execution mode: parallel or sequential")
    reasoning: str = Field(default="", description="Explanation of planning decision")


class AgentOutput(BaseModel):
    """Final result output from the agent.

    Attributes:
        answer: Natural language answer to the user's query.
        tool_results: Tool execution results keyed by tool_id.
        visualizations: Chart/table data for visualization.
        suggestions: Follow-up suggestions for the user.
        session_context: Session metadata for tracking.
    """

    answer: str = Field(..., description="Natural language answer to the user's query")
    tool_results: Dict[str, Any] = Field(..., description="Tool execution results keyed by tool_id")
    visualizations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Chart/table data for visualization"
    )
    suggestions: List[str] = Field(
        default_factory=list, description="Follow-up suggestions for the user"
    )
    session_context: Dict[str, Any] = Field(
        default_factory=dict, description="Session metadata for tracking"
    )


# ============================================================================
# Session Context
# ============================================================================


class SessionContext(BaseModel):
    """Session-level context for tracking session anchor and topic detection.

    FR Requirements:
    - Session anchor: First query, always preserved
    - Topic tracker: Detected topics for session boundary detection

    Attributes:
        session_id: Unique session identifier.
        session_anchor: The first query of the session, preserved throughout.
        topic_tracker: List of detected topics for session boundary detection.
        model_context_limit: Maximum context window (default 128000).
    """

    session_id: str = Field(..., description="Unique session identifier")
    session_anchor: str = Field(..., description="First query, always preserved throughout session")
    topic_tracker: List[str] = Field(
        ...,
        description="Detected topics for session boundary detection"
    )
    model_context_limit: int = Field(
        default=128000,
        description="Model context window limit in tokens"
    )


# ============================================================================
# Agent State TypedDict
# ============================================================================


class AgentState(TypedDict):
    """Main state TypedDict for the LangGraph agent.

    FR-2.4-2.6: Expanded state schema for tool selection, HITL clarification,
    and multi-tool query handling.

    Attributes:
        messages: Chat history using LangChain's add_messages reducer.
        query: Original user query string.
        session_id: Session identifier for tracking.
        retrieved_tools: List of tools retrieved from RAG retrieval.
        extracted_dimensions: Dimensions extracted from the query.
        tool_selection_result: Result from tool selection LLM (FR-2.4).
        clarification: HITL clarification response if needed (FR-2.5).
        execution_plan: Execution plan from planner node (FR-2.6).
        execution_results: Tool execution results keyed by tool_id.
        final_output: Final synthesized output after execution.
        current_stage: Current processing stage identifier.
        error: Error message if any stage failed.
    """

    # Existing field - must be preserved
    messages: Annotated[list[BaseMessage], add_messages]

    # New fields for FR-2.4-2.6
    query: str  # Original user query
    session_id: str  # Session identifier
    retrieved_tools: List[RetrievedTool]  # From RAG retrieval
    extracted_dimensions: ExtractedDimensions  # From dimension extraction
    tool_selection_result: Optional[ToolSelectionResult]  # From tool selection node
    clarification: Optional[HITLClarification]  # From HITL clarification
    execution_plan: Optional[ExecutionPlan]  # From planner node
    execution_results: Dict[str, Any]  # Tool execution results keyed by tool_id
    final_output: Optional[Dict[str, Any]]  # Final synthesized output
    current_stage: str  # Current processing stage
    error: Optional[str]  # Error message if any


# ============================================================================
# Dimension Match Score Function
# ============================================================================


def compute_dimension_match_score(
    retrieved_tool: RetrievedTool,
    extracted_dimensions: ExtractedDimensions,
) -> float:
    """Compute dimension match score for a retrieved tool.

    FR-2.4: Tool selection confidence includes 40% dimension match score.
    This function calculates how well the extracted dimensions match
    the tool's required dimensions.

    The score is calculated as:
        matched_required_dimensions / total_required_dimensions

    If the tool has no required dimensions, returns 1.0 (perfect match).

    Args:
        retrieved_tool: Tool retrieved from RAG with its definition.
        extracted_dimensions: Dimensions extracted from the user query.

    Returns:
        Float score between 0.0 and 1.0 representing dimension match quality.
        - 1.0: All required dimensions matched
        - 0.0: No required dimensions matched
        - Fractional values for partial matches
    """
    required_dims = retrieved_tool.tool_definition.required_dimensions

    # If no required dimensions, it's a universal tool - perfect match
    if not required_dims:
        return 1.0

    # Count how many required dimensions are present in extracted dimensions
    matched_count = 0
    total_required = len(required_dims)

    for dim_name in required_dims:
        # Check if dimension is present based on dimension type
        if _is_dimension_present(dim_name, extracted_dimensions):
            matched_count += 1

    return matched_count / total_required


def _is_dimension_present(dimension_name: str, extracted: ExtractedDimensions) -> bool:
    """Check if a dimension is present in the extracted dimensions.

    Args:
        dimension_name: Name of the dimension to check.
        extracted: ExtractedDimensions container.

    Returns:
        True if the dimension has non-empty values.
    """
    # Get the attribute value using getattr
    value = getattr(extracted, dimension_name, None)

    if value is None:
        return False

    # Check based on dimension type
    if isinstance(value, list):
        return len(value) > 0
    elif isinstance(value, dict):
        return len(value) > 0
    elif isinstance(value, str):
        return len(value) > 0

    return False
