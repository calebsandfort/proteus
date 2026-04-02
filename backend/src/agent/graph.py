"""FR-2.4-2.6: AgentGraph - Complete LangGraph Agent Implementation.

This module implements the complete AgentGraph that wires together all nodes
for the consumer analytics agent system.

Graph Architecture (FR-2.4-2.6):
1. init — Initial state
2. retrieval — RAG retrieval of tools
3. dimension_extraction — Extract dimensions from query
4. tool_selection — Select best tool(s) using LLM
5. clarification — HITL clarification needed
6. awaiting_clarification — Waiting for user clarification response
7. planning — Create execution plan (planner node)
8. execution — Execute selected tool(s)
9. response — Generate natural language response
10. done — Complete

FR Requirements:
- FR-2.4: Tool Selection LLM with MiniMax-Text-01 via OpenRouter
- FR-2.5: HITL Clarification for confidence < 0.70
- FR-2.6: Multi-Tool Query Handling with planner node
"""

import asyncio
from typing import Any, Dict, List, Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agent.dimension_graph import DimensionExtractionGraph
from src.agent.nodes import (
    AgentOutput,
    ExecutionPlan,
    HITLClarification,
    ToolSelectionResult,
    clarification_node,
    execution_node,
    planner_node,
    tool_selection_node,
)
from src.agent.retrieval import EmbeddingRetriever
from src.agent.state import AgentState
from src.api.models.dimensions import ExtractedDimensions
from src.api.models.tool import RetrievedTool
from src.api.openrouter import OpenRouterClient


# ============================================================================
# Node Functions
# ============================================================================


async def retrieve_node(state: AgentState) -> Dict[str, Any]:
    """Retrieve relevant tools using RAG retrieval.

    FR-2.3: RAG retrieval with top-8 candidate tools based on semantic similarity.
    Similarity threshold: 0.70

    Args:
        state: Current agent state with query.

    Returns:
        Updated state with retrieved_tools and current_stage="retrieval".
    """
    try:
        query = state["query"]
        retriever = EmbeddingRetriever()
        openrouter_client = OpenRouterClient()

        # Generate embedding for the query
        query_embedding = openrouter_client.embed_texts([query])[0]

        # Retrieve tools
        retrieved_tools = retriever.retrieve(
            query=query,
            query_embedding=query_embedding,
            top_k=8,
            similarity_threshold=0.70,
        )

        return {
            "retrieved_tools": retrieved_tools,
            "current_stage": "retrieval",
            "error": None,
        }

    except Exception as e:
        return {
            "retrieved_tools": [],
            "current_stage": "error",
            "error": f"Retrieval failed: {str(e)}",
        }


async def extract_dimensions_node(state: AgentState) -> Dict[str, Any]:
    """Extract dimensions from user query using DimensionExtractionGraph.

    FR-3.2: Parallel dimension extraction across all dimension types.
    Target latency: 600-1200ms total.

    Args:
        state: Current agent state with query and conversation history.

    Returns:
        Updated state with extracted_dimensions and current_stage="dimension_extraction".
    """
    try:
        query = state["query"]
        messages = state.get("messages", [])

        # Build conversation history from messages
        conversation_history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                conversation_history.append({"role": "user", "content": msg.content})
            elif hasattr(msg, "content") and hasattr(msg, "type"):
                conversation_history.append({"role": msg.type, "content": msg.content})

        # Extract dimensions
        dimension_graph = DimensionExtractionGraph()
        result = await dimension_graph.extract_all(
            query=query,
            conversation_history=conversation_history,
        )

        return {
            "extracted_dimensions": result.extracted_dimensions,
            "current_stage": "dimension_extraction",
            "error": None,
        }

    except Exception as e:
        return {
            "extracted_dimensions": ExtractedDimensions(),
            "current_stage": "error",
            "error": f"Dimension extraction failed: {str(e)}",
        }


async def respond_node(state: AgentState) -> Dict[str, Any]:
    """Generate natural language response from execution results.

    FR-2.6: Synthesize tool execution results into natural language response.

    Args:
        state: Current agent state with execution_results.

    Returns:
        Updated state with final_output, messages, and current_stage="response".
    """
    try:
        query = state["query"]
        execution_results = state.get("execution_results", {})
        execution_plan = state.get("execution_plan")

        # Build context from execution results
        results_summary = []
        for tool_id, result in execution_results.items():
            results_summary.append(f"Tool {tool_id}: {result}")

        # Simple response synthesis - in production, this would use an LLM
        if execution_results:
            answer = f"Based on your query '{query}', I found the following insights: "
            answer += " ".join(str(r) for r in execution_results.values())
        else:
            answer = f"I couldn't find any data matching your query '{query}'."

        # Build AgentOutput
        final_output = AgentOutput(
            answer=answer,
            tool_results=execution_results,
            visualizations=[],
            suggestions=[
                "Try specifying a different time range",
                "Broaden your category search",
            ],
            session_context={
                "session_id": state.get("session_id"),
                "stage": "completed",
            },
        )

        # Add assistant message to conversation
        assistant_message = HumanMessage(content=answer)

        return {
            "final_output": final_output.model_dump(),
            "messages": [assistant_message],
            "current_stage": "done",
            "error": None,
        }

    except Exception as e:
        return {
            "final_output": None,
            "current_stage": "error",
            "error": f"Response generation failed: {str(e)}",
        }


async def done_node(state: AgentState) -> Dict[str, Any]:
    """Mark the graph execution as complete.

    This is a terminal node that sets the final stage.

    Args:
        state: Current agent state.

    Returns:
        Updated state with current_stage="done".
    """
    return {
        "current_stage": "done",
        "error": None,
    }


# ============================================================================
# Routing Functions for Conditional Edges
# ============================================================================


def tool_selection_routing(state: AgentState) -> Literal["planner", "clarification"]:
    """Route based on tool selection confidence.

    FR-2.4: Confidence thresholds:
    - >= 0.85: Proceed to execution
    - 0.70-0.84: Show competing, proceed
    - < 0.70: HITL clarification

    Args:
        state: Current agent state with tool_selection_result.

    Returns:
        "planner" if confidence >= 0.70, else "clarification".
    """
    tool_selection_result = state.get("tool_selection_result")

    if tool_selection_result is None:
        return "clarification"

    confidence = tool_selection_result.confidence

    # FR-2.4: confidence >= 0.70 proceed, < 0.70 clarification
    if confidence >= 0.70:
        return "planner"
    else:
        return "clarification"


def clarification_routing(state: AgentState) -> Literal["tool_selection"]:
    """Route after clarification is complete.

    After user responds to clarification, route back to tool_selection.

    Args:
        state: Current agent state with clarification.

    Returns:
        "tool_selection" to re-run tool selection with clarification.
    """
    return "tool_selection"


def planner_routing(state: AgentState) -> Literal["execution"]:
    """Route from planner to execution.

    FR-2.6: After planning, always proceed to execution.

    Args:
        state: Current agent state with execution_plan.

    Returns:
        "execution" - always proceed after planning.
    """
    return "execution"


def execution_routing(state: AgentState) -> Literal["respond"]:
    """Route from execution to response synthesis.

    FR-2.6: After execution, always proceed to response.

    Args:
        state: Current agent state with execution_results.

    Returns:
        "respond" - always proceed after execution.
    """
    return "respond"


# ============================================================================
# Graph Builder
# ============================================================================


def build_graph() -> StateGraph:
    """Build the complete AgentGraph.

    Graph Architecture:
    START -> retrieve -> extract_dimensions -> tool_selection
                                                |
                        +-----------+-----------+
                        |           |           |
                        v           v           v
                    planner    clarification   (if confidence >= 0.70)
                        |           |
                        v           v
                    execution <----+ (after clarification, back to tool_selection)
                        |
                        v
                    respond -> done -> END

    Returns:
        Compiled StateGraph with MemorySaver checkpointer.
    """
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("extract_dimensions", extract_dimensions_node)
    graph.add_node("tool_selection", tool_selection_node)
    graph.add_node("planner", planner_node)
    graph.add_node("execution", execution_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("respond", respond_node)
    graph.add_node("done", done_node)

    # Define edges
    # START -> retrieve
    graph.add_edge(START, "retrieve")

    # retrieve -> extract_dimensions
    graph.add_edge("retrieve", "extract_dimensions")

    # extract_dimensions -> tool_selection
    graph.add_edge("extract_dimensions", "tool_selection")

    # tool_selection -> planner OR clarification (conditional)
    graph.add_conditional_edges(
        "tool_selection",
        tool_selection_routing,
        {
            "planner": "planner",
            "clarification": "clarification",
        },
    )

    # clarification -> tool_selection (after user responds)
    graph.add_edge("clarification", "tool_selection")

    # planner -> execution (always)
    graph.add_edge("planner", "execution")

    # execution -> respond (always)
    graph.add_edge("execution", "respond")

    # respond -> done
    graph.add_edge("respond", "done")

    # done -> END
    graph.add_edge("done", END)

    # Compile with checkpointer
    return graph.compile(checkpointer=MemorySaver())


# Create the compiled agent
agent = build_graph()


# ============================================================================
# Agent Runner
# ============================================================================


async def run_agent_graph(
    query: str,
    session_id: str,
    conversation_history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Run the agent graph with the given query.

    Args:
        query: The user query string.
        session_id: Session identifier for tracking.
        conversation_history: List of conversation history dicts.

    Returns:
        Final state after graph execution.
    """
    # Build initial messages from conversation history
    messages: List[BaseMessage] = []
    for turn in conversation_history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            # Assume assistant message
            from langchain_core.messages import AIMessage
            messages.append(AIMessage(content=content))

    # Initial state
    initial_state: AgentState = {
        "messages": messages,
        "query": query,
        "session_id": session_id,
        "retrieved_tools": [],
        "extracted_dimensions": ExtractedDimensions(),
        "tool_selection_result": None,
        "clarification": None,
        "execution_plan": None,
        "execution_results": {},
        "final_output": None,
        "current_stage": "init",
        "error": None,
    }

    # Invoke the graph
    result = await agent.ainvoke(initial_state)

    return result
