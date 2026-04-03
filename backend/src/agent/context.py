"""FR-1.2: Session Context Management for Multi-Turn Conversation.

This module implements session context management for multi-turn conversations,
supporting follow-up questions and references to prior results.

FR Requirements:
- FR-1.2: Multi-Turn Conversation
  - Support multi-turn conversations with follow-up questions
  - Maintain messages up to 75% of model's context window limit
  - Minimum 4 recent turns + session anchor preserved
  - Preserve first query as "session anchor" always available
  - Tag tool results with internal reference ID for "that"/"those" resolution
  - Detect topic changes (different brand/category) as new session context
  - When context approaches 80% of limit, summarize/compress older messages
  - Summarization preserves key extracted dimensions and tool selections
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Constants from FR-1.2
# ============================================================================

MAX_CONTEXT_RATIO = 0.75  # 75% of context window
MIN_TURNS_TO_KEEP = 4  # Minimum turns to preserve
SUMMARIZATION_THRESHOLD = 0.80  # 80% triggers summarization


# ============================================================================
# FR-1.2: Pydantic Models
# ============================================================================


class ToolResult(BaseModel):
    """Tool result with reference ID for "that"/"those" resolution.

    Attributes:
        referenceId: Internal reference ID for tracking tool results.
        tool_name: Name of the executed tool.
        data: Tool execution result data.
    """

    referenceId: str = Field(..., description="Internal reference ID")
    tool_name: str = Field(..., description="Name of the executed tool")
    data: Dict[str, Any] = Field(default_factory=dict, description="Tool execution result data")


class ConversationTurn(BaseModel):
    """Single turn in a multi-turn conversation.

    FR-1.2: Each turn is tagged with reference IDs for "that"/"those" resolution.

    Attributes:
        id: Unique identifier for this turn.
        role: Role of the message sender ('user' or 'assistant').
        content: The message content.
        tool_results: Optional list of tool results from this turn.
        extracted_dimensions: Optional dimensions extracted from this turn.
        timestamp: When this turn occurred.
        is_sessionAnchor: True if this is the session anchor (first query).
        referenceId: Optional reference ID for this turn.
    """

    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique identifier for this turn")
    role: Literal["user", "assistant"] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="The message content")
    tool_results: Optional[List[ToolResult]] = Field(
        default=None,
        description="List of tool results from this turn"
    )
    extracted_dimensions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dimensions extracted from this turn"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="When this turn occurred")
    is_sessionAnchor: bool = Field(
        default=False,
        description="True if this is the session anchor (first query)"
    )
    referenceId: Optional[str] = Field(
        default=None,
        description="Optional reference ID for this turn"
    )


class SessionContext(BaseModel):
    """Session-level context for tracking multi-turn conversations.

    FR-1.2: Maintains session anchor, sliding window of recent turns,
    extracted dimensions, and topic tracking for session boundary detection.

    Attributes:
        session_id: Unique session identifier.
        session_anchor: The first query of the session, preserved throughout.
        recent_turns: Token-limited sliding window of conversation turns.
        extracted_dimensions: Key dimensions extracted across the session.
        topic_tracker: List of detected topics for session boundary detection.
        model_context_limit: Maximum context window in tokens (default 128000).
    """

    model_config = {"from_attributes": True}

    session_id: str = Field(..., description="Unique session identifier")
    session_anchor: str = Field(
        ...,
        description="First query, always preserved throughout session"
    )
    recent_turns: List[ConversationTurn] = Field(
        default_factory=list,
        description="Token-limited sliding window of conversation turns"
    )
    extracted_dimensions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key dimensions extracted across the session"
    )
    topic_tracker: List[str] = Field(
        default_factory=list,
        description="Detected topics for session boundary detection"
    )
    model_context_limit: int = Field(
        default=128000,
        description="Model context window limit in tokens"
    )


# ============================================================================
# Token Estimation Functions
# ============================================================================


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses a rough estimation of ~4 characters per token.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    return len(text) // 4


def estimate_turn_tokens(turn: ConversationTurn) -> int:
    """Estimate token count for a conversation turn.

    Args:
        turn: The conversation turn to estimate.

    Returns:
        Estimated token count for the turn.
    """
    # Base content tokens
    tokens = estimate_tokens(turn.content)

    # Add tokens for tool results if present
    if turn.tool_results:
        for result in turn.tool_results:
            tokens += estimate_tokens(str(result.data))

    # Add tokens for extracted dimensions if present
    if turn.extracted_dimensions:
        tokens += estimate_tokens(str(turn.extracted_dimensions))

    return tokens


def estimate_context_tokens(context: SessionContext) -> int:
    """Estimate total token count for session context.

    Includes session anchor and all recent turns.

    Args:
        context: The session context.

    Returns:
        Estimated total token count.
    """
    tokens = estimate_tokens(context.session_anchor)

    for turn in context.recent_turns:
        tokens += estimate_turn_tokens(turn)

    return tokens


# ============================================================================
# Context Limit Checking Functions
# ============================================================================


def is_within_context_limit(context: SessionContext) -> bool:
    """Check if context is within the 75% context limit.

    Args:
        context: The session context to check.

    Returns:
        True if context is within limit, False otherwise.
    """
    total_tokens = estimate_context_tokens(context)
    limit_tokens = int(context.model_context_limit * MAX_CONTEXT_RATIO)
    return total_tokens <= limit_tokens


def needs_summarization(context: SessionContext) -> bool:
    """Check if context needs summarization (80% threshold).

    Args:
        context: The session context to check.

    Returns:
        True if summarization is needed, False otherwise.
    """
    total_tokens = estimate_context_tokens(context)
    threshold_tokens = int(context.model_context_limit * SUMMARIZATION_THRESHOLD)
    return total_tokens > threshold_tokens


# ============================================================================
# Topic Detection Functions
# ============================================================================


def detect_topic_change(
    prev_dimensions: Dict[str, Any],
    current_dimensions: Dict[str, Any],
) -> bool:
    """Detect if there's a topic change between dimension sets.

    A topic change is detected when:
    - Different brand values appear
    - Different merchant_category values appear
    - A new dimension type is introduced

    Args:
        prev_dimensions: Previous turn's extracted dimensions.
        current_dimensions: Current turn's extracted dimensions.

    Returns:
        True if topic change detected, False otherwise.
    """
    # Check for brand changes
    prev_brands = set(prev_dimensions.get("brand", []))
    curr_brands = set(current_dimensions.get("brand", []))
    if prev_brands and curr_brands and prev_brands != curr_brands:
        return True

    # Check for category changes
    prev_cats = set(prev_dimensions.get("merchant_category", []))
    curr_cats = set(current_dimensions.get("merchant_category", []))
    if prev_cats and curr_cats and prev_cats != curr_cats:
        return True

    # Check for generation changes
    prev_gens = set(prev_dimensions.get("generation", []))
    curr_gens = set(current_dimensions.get("generation", []))
    # Only detect change if new generations were ADDED, not removed
    if curr_gens - prev_gens:
        return True

    # Check if new dimension type was introduced
    prev_keys = set(prev_dimensions.keys())
    curr_keys = set(current_dimensions.keys())
    new_keys = curr_keys - prev_keys
    if new_keys:
        # New dimension type introduced - could indicate topic change
        for key in new_keys:
            if current_dimensions.get(key):
                return True

    return False


def is_new_session(
    context: SessionContext,
    current_dimensions: Optional[Dict[str, Any]] = None,
) -> bool:
    """Determine if current query should start a new session.

    A new session is started when:
    - No conversation history exists
    - Topic change is detected (different brand/category)

    Args:
        context: Current session context.
        current_dimensions: Dimensions from the current query (optional).

    Returns:
        True if this should be a new session, False otherwise.
    """
    # No history = new session
    if not context.recent_turns:
        return True

    # Check for topic change if dimensions provided
    if current_dimensions and context.extracted_dimensions:
        if detect_topic_change(context.extracted_dimensions, current_dimensions):
            return True

    return False


# ============================================================================
# Turn Management Functions
# ============================================================================


def add_turn(
    context: SessionContext,
    turn: ConversationTurn,
) -> SessionContext:
    """Add a conversation turn to the session context.

    Also updates topic tracker if dimensions are present.

    Args:
        context: Current session context.
        turn: The turn to add.

    Returns:
        Updated session context with the new turn.
    """
    # Create a copy of recent turns
    updated_turns = context.recent_turns.copy()

    # Add the new turn
    updated_turns.append(turn)

    # Update topic tracker if dimensions present
    updated_topics = context.topic_tracker.copy()
    if turn.extracted_dimensions:
        # Extract brand topics
        for brand in turn.extracted_dimensions.get("brand", []):
            if brand not in updated_topics:
                updated_topics.append(brand)
        # Extract category topics
        for cat in turn.extracted_dimensions.get("merchant_category", []):
            if cat not in updated_topics:
                updated_topics.append(cat)

    return SessionContext(
        session_id=context.session_id,
        session_anchor=context.session_anchor,
        recent_turns=updated_turns,
        extracted_dimensions=context.extracted_dimensions,
        topic_tracker=updated_topics,
        model_context_limit=context.model_context_limit,
    )


def enforce_minimum_turns(context: SessionContext) -> SessionContext:
    """Enforce minimum turns with sliding window.

    Always keeps at least MIN_TURNS_TO_KEEP recent turns,
    while respecting the 75% context limit.

    Args:
        context: Current session context.

    Returns:
        Updated context with enforced minimum turns.
    """
    if len(context.recent_turns) <= MIN_TURNS_TO_KEEP:
        return context

    # Check if we need to trim to stay within limit
    if is_within_context_limit(context):
        return context

    # Trim oldest turns while keeping minimum
    trimmed_turns = context.recent_turns.copy()
    while len(trimmed_turns) > MIN_TURNS_TO_KEEP and not is_within_context_limit(
        SessionContext(
            session_id=context.session_id,
            session_anchor=context.session_anchor,
            recent_turns=trimmed_turns,
            extracted_dimensions=context.extracted_dimensions,
            topic_tracker=context.topic_tracker,
            model_context_limit=context.model_context_limit,
        )
    ):
        trimmed_turns.pop(0)

    return SessionContext(
        session_id=context.session_id,
        session_anchor=context.session_anchor,
        recent_turns=trimmed_turns,
        extracted_dimensions=context.extracted_dimensions,
        topic_tracker=context.topic_tracker,
        model_context_limit=context.model_context_limit,
    )


# ============================================================================
# Reference ID Tagging
# ============================================================================


def tag_tool_result(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    """Tag a tool result with a unique reference ID.

    Used for "that"/"those" resolution in follow-up questions.

    Args:
        tool_result: The tool result dict to tag.

    Returns:
        Tool result with added referenceId field.
    """
    tagged = tool_result.copy()
    tagged["referenceId"] = f"ref_{uuid.uuid4().hex[:8]}"
    return tagged


# ============================================================================
# Summarization Functions
# ============================================================================


def summarize_context(context: SessionContext) -> SessionContext:
    """Summarize older messages when context approaches limit.

    FR-1.2: Summarization preserves:
    - Session anchor (always)
    - Key extracted dimensions
    - Minimum required turns
    - Topic tracker

    Args:
        context: The session context to summarize.

    Returns:
        Summarized session context.
    """
    # Always preserve session anchor
    preserved_anchor = context.session_anchor

    # Preserve key dimensions
    preserved_dimensions = context.extracted_dimensions.copy()

    # Preserve topic tracker
    preserved_topics = context.topic_tracker.copy()

    # Keep minimum turns
    if len(context.recent_turns) <= MIN_TURNS_TO_KEEP:
        return SessionContext(
            session_id=context.session_id,
            session_anchor=preserved_anchor,
            recent_turns=context.recent_turns,
            extracted_dimensions=preserved_dimensions,
            topic_tracker=preserved_topics,
            model_context_limit=context.model_context_limit,
        )

    # Create summarized turn representing older conversation
    summarized_content = _create_summary_turn(context.recent_turns[:-MIN_TURNS_TO_KEEP])

    # Keep the most recent turns
    recent_turns = context.recent_turns[-MIN_TURNS_TO_KEEP:]

    # Prepend summarized turn if we had more than minimum
    if summarized_content:
        summarized_turn = ConversationTurn(
            id=f"summary_{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=summarized_content,
            timestamp=datetime.now(),
        )
        recent_turns = [summarized_turn] + recent_turns

    return SessionContext(
        session_id=context.session_id,
        session_anchor=preserved_anchor,
        recent_turns=recent_turns,
        extracted_dimensions=preserved_dimensions,
        topic_tracker=preserved_topics,
        model_context_limit=context.model_context_limit,
    )


def _create_summary_turn(older_turns: List[ConversationTurn]) -> str:
    """Create a summary string for older turns.

    Args:
        older_turns: List of turns to summarize.

    Returns:
        Summary string.
    """
    if not older_turns:
        return ""

    topics = []
    dimensions_seen = {}

    for turn in older_turns:
        if turn.extracted_dimensions:
            for dim, values in turn.extracted_dimensions.items():
                if dim not in dimensions_seen:
                    dimensions_seen[dim] = set()
                if isinstance(values, list):
                    for v in values:
                        dimensions_seen[dim].add(v)

    # Build summary
    parts = []
    if dimensions_seen:
        for dim, values in dimensions_seen.items():
            if values:
                parts.append(f"{dim}: {', '.join(sorted(values))}")

    if parts:
        return f"[Previous conversation covered: {'; '.join(parts)}]"
    return "[Previous conversation occurred]"


# ============================================================================
# Session Context Factory
# ============================================================================


def create_session_context(
    query: str,
    session_id: str,
    model_context_limit: int = 128000,
) -> SessionContext:
    """Create a new session context from the first query.

    Args:
        query: The first query of the session.
        session_id: Unique session identifier.
        model_context_limit: Model context window limit (default 128000).

    Returns:
        New session context with the query as session anchor.
    """
    # Create the first turn as a ConversationTurn
    first_turn = ConversationTurn(
        id=str(uuid.uuid4()),
        role="user",
        content=query,
        timestamp=datetime.now(),
        is_sessionAnchor=True,
    )

    return SessionContext(
        session_id=session_id,
        session_anchor=query,
        recent_turns=[first_turn],
        extracted_dimensions={},
        topic_tracker=[],
        model_context_limit=model_context_limit,
    )
