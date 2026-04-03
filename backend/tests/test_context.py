"""TDD Tests for Session Context Management (FR-1.2).

Tests the SessionContext management for multi-turn conversations.

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
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest


# ============================================================================
# Test Constants (from FR-1.2)
# ============================================================================

MAX_CONTEXT_RATIO = 0.75
MIN_TURNS_TO_KEEP = 4
SUMMARIZATION_THRESHOLD = 0.80


# ============================================================================
# Test Data Factories
# ============================================================================


def create_conversation_turn(
    content: str,
    role: str = "user",
    tool_results: Optional[List[Dict[str, Any]]] = None,
    extracted_dimensions: Optional[Dict[str, Any]] = None,
    is_session_anchor: bool = False,
    reference_id: Optional[str] = None,
):
    """Create a ConversationTurn Pydantic model for testing.

    Returns a ConversationTurn model instance (not a dict) to match
    the type signature of add_turn() and SessionContext.
    """
    from src.agent.context import ConversationTurn

    return ConversationTurn(
        id=str(uuid.uuid4()),
        role=role,
        content=content,
        tool_results=tool_results,
        extracted_dimensions=extracted_dimensions,
        timestamp=datetime.now(),
        is_sessionAnchor=is_session_anchor,
        referenceId=reference_id,
    )


def create_dimension_values(
    brand: Optional[List[str]] = None,
    merchant_category: Optional[List[str]] = None,
    generation: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create dimension values for testing."""
    return {
        "brand": brand or [],
        "merchant_category": merchant_category or [],
        "generation": generation or [],
    }


# ============================================================================
# Tests for ConversationTurn Model (FR-1.2)
# ============================================================================


class TestConversationTurnModel:
    """Tests for ConversationTurn model structure."""

    def test_fr_1_2_conversation_turn_has_required_fields(self) -> None:
        """Test ConversationTurn has all required fields per interface contract."""
        from src.agent.context import ConversationTurn

        turn = ConversationTurn(
            id="test-id",
            role="user",
            content="Show spending by generation",
            timestamp=datetime.now(),
        )

        assert turn.id == "test-id"
        assert turn.role == "user"
        assert turn.content == "Show spending by generation"
        assert turn.tool_results is None
        assert turn.extracted_dimensions is None
        assert turn.is_sessionAnchor is False
        assert turn.referenceId is None

    def test_fr_1_2_conversation_turn_with_tool_results(self) -> None:
        """Test ConversationTurn with tool results tagged with reference IDs."""
        from src.agent.context import ConversationTurn

        tool_results = [
            {
                "referenceId": "ref_123",
                "tool_name": "spending_by_generation",
                "data": {"generation": "gen_z", "spending": 1500},
            }
        ]

        turn = ConversationTurn(
            id="test-id",
            role="assistant",
            content="Here are the results",
            tool_results=tool_results,
            timestamp=datetime.now(),
        )

        assert turn.tool_results is not None
        assert len(turn.tool_results) == 1
        assert turn.tool_results[0].referenceId == "ref_123"

    def test_fr_1_2_conversation_turn_with_session_anchor(self) -> None:
        """Test ConversationTurn marked as session anchor."""
        from src.agent.context import ConversationTurn

        turn = ConversationTurn(
            id="anchor-id",
            role="user",
            content="Show Gen Z spending trends",
            timestamp=datetime.now(),
            is_sessionAnchor=True,
        )

        assert turn.is_sessionAnchor is True


# ============================================================================
# Tests for SessionContext Model (FR-1.2)
# ============================================================================


class TestSessionContextModel:
    """Tests for SessionContext model structure."""

    def test_fr_1_2_session_context_has_required_fields(self) -> None:
        """Test SessionContext has all required fields per interface contract."""
        from src.agent.context import SessionContext

        context = SessionContext(
            session_id="test-session",
            session_anchor="Show Gen Z spending trends",
        )

        assert context.session_id == "test-session"
        assert context.session_anchor == "Show Gen Z spending trends"
        assert context.recent_turns == []
        assert context.extracted_dimensions == {}
        assert context.topic_tracker == []
        assert context.model_context_limit == 128000

    def test_fr_1_2_session_context_custom_model_limit(self) -> None:
        """Test SessionContext with custom model context limit."""
        from src.agent.context import SessionContext

        context = SessionContext(
            session_id="test-session",
            session_anchor="Test query",
            model_context_limit=200000,
        )

        assert context.model_context_limit == 200000


# ============================================================================
# Tests for Token Estimation (FR-1.2)
# ============================================================================


class TestTokenEstimation:
    """Tests for token counting estimation."""

    def test_fr_1_2_estimate_tokens_simple_text(self) -> None:
        """Test token estimation for simple text."""
        from src.agent.context import estimate_tokens

        text = "Hello world"
        tokens = estimate_tokens(text)

        # Simple estimation: ~4 chars per token
        expected = len(text) // 4
        assert tokens == expected

    def test_fr_1_2_estimate_tokens_empty_string(self) -> None:
        """Test token estimation for empty string."""
        from src.agent.context import estimate_tokens

        tokens = estimate_tokens("")
        assert tokens == 0

    def test_fr_1_2_estimate_tokens_long_text(self) -> None:
        """Test token estimation for longer text."""
        from src.agent.context import estimate_tokens

        text = "Show me spending by generation for the last year"
        tokens = estimate_tokens(text)

        # Should be positive
        assert tokens > 0
        # Should be less than character count
        assert tokens < len(text)


# ============================================================================
# Tests for Topic Detection (FR-1.2)
# ============================================================================


class TestTopicDetection:
    """Tests for detecting topic changes in conversation."""

    def test_fr_1_2_detect_topic_change_different_brand(self) -> None:
        """Test topic change detection when brand changes."""
        from src.agent.context import detect_topic_change

        prev_dims = create_dimension_values(brand=["nike"])
        curr_dims = create_dimension_values(brand=["adidas"])

        result = detect_topic_change(prev_dims, curr_dims)
        assert result is True

    def test_fr_1_2_detect_topic_change_different_category(self) -> None:
        """Test topic change detection when category changes."""
        from src.agent.context import detect_topic_change

        prev_dims = create_dimension_values(merchant_category=["electronics"])
        curr_dims = create_dimension_values(merchant_category=["clothing"])

        result = detect_topic_change(prev_dims, curr_dims)
        assert result is True

    def test_fr_1_2_no_topic_change_same_dimensions(self) -> None:
        """Test no topic change when dimensions are same."""
        from src.agent.context import detect_topic_change

        dims = create_dimension_values(brand=["nike"], generation=["gen_z"])

        result = detect_topic_change(dims, dims)
        assert result is False

    def test_fr_1_2_no_topic_change_subset_dimensions(self) -> None:
        """Test no topic change when new dimensions are subset."""
        from src.agent.context import detect_topic_change

        prev_dims = create_dimension_values(brand=["nike"], generation=["gen_z"])
        curr_dims = create_dimension_values(brand=["nike"])

        # Nike still present, so not a topic change
        result = detect_topic_change(prev_dims, curr_dims)
        assert result is False

    def test_fr_1_2_topic_change_new_dimension_type(self) -> None:
        """Test topic change when new dimension type introduced."""
        from src.agent.context import detect_topic_change

        prev_dims = create_dimension_values(brand=["nike"])
        curr_dims = create_dimension_values(brand=["nike"], generation=["gen_z"])

        # New dimension type introduced - could be topic change
        result = detect_topic_change(prev_dims, curr_dims)
        assert result is True


# ============================================================================
# Tests for Context Limit Checking (FR-1.2)
# ============================================================================


class TestContextLimitChecking:
    """Tests for checking context limits."""

    def test_fr_1_2_is_within_context_limit_empty(self) -> None:
        """Test empty context is within limit."""
        from src.agent.context import SessionContext, is_within_context_limit

        context = SessionContext(
            session_id="test",
            session_anchor="Test",
            recent_turns=[],
        )

        result = is_within_context_limit(context)
        assert result is True

    def test_fr_1_2_is_within_context_limit_small(self) -> None:
        """Test small context is within 75% limit."""
        from src.agent.context import SessionContext, is_within_context_limit

        # Create a few small turns
        turns = [
            create_conversation_turn(f"Query {i}: Show spending data")
            for i in range(3)
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Initial query",
            recent_turns=turns,
        )

        result = is_within_context_limit(context)
        assert result is True

    def test_fr_1_2_is_within_context_limit_at_threshold(self) -> None:
        """Test context at exactly 75% threshold."""
        from src.agent.context import SessionContext, is_within_context_limit

        # Create enough turns to reach ~75% of context limit
        # Each turn with ~1000 chars = ~250 tokens
        # 128000 * 0.75 / 250 = ~384 turns to reach limit
        large_content = "x" * 4000  # ~1000 tokens
        turns = [
            create_conversation_turn(large_content)
            for _ in range(300)
        ]

        context = SessionContext(
            session_id="test",
            session_anchor=large_content,
            recent_turns=turns,
            model_context_limit=128000,
        )

        result = is_within_context_limit(context)
        # Should be False since we exceed 75%
        assert result is False

    def test_fr_1_2_needs_summarization_at_threshold(self) -> None:
        """Test summarization needed at 80% threshold."""
        from src.agent.context import SessionContext, needs_summarization

        # Create enough turns to exceed 80% of context limit
        large_content = "x" * 4000  # ~1000 tokens
        turns = [
            create_conversation_turn(large_content)
            for _ in range(350)
        ]

        context = SessionContext(
            session_id="test",
            session_anchor=large_content,
            recent_turns=turns,
            model_context_limit=128000,
        )

        result = needs_summarization(context)
        assert result is True

    def test_fr_1_2_no_summarization_below_threshold(self) -> None:
        """Test no summarization needed below 80% threshold."""
        from src.agent.context import SessionContext, needs_summarization

        turns = [
            create_conversation_turn(f"Query {i}: Show spending data")
            for i in range(10)
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Initial query",
            recent_turns=turns,
            model_context_limit=128000,
        )

        result = needs_summarization(context)
        assert result is False


# ============================================================================
# Tests for Adding Turns (FR-1.2)
# ============================================================================


class TestAddingTurns:
    """Tests for adding conversation turns."""

    def test_fr_1_2_add_turn_empty_context(self) -> None:
        """Test adding first turn to empty context."""
        from src.agent.context import SessionContext, add_turn

        context = SessionContext(
            session_id="test",
            session_anchor="Initial query",
        )

        turn = create_conversation_turn(
            content="Show Gen Z spending",
            role="user",
        )

        updated = add_turn(context, turn)

        assert len(updated.recent_turns) == 1
        assert updated.recent_turns[0].content == "Show Gen Z spending"

    def test_fr_1_2_add_turn_updates_topic_tracker(self) -> None:
        """Test adding turn updates topic tracker."""
        from src.agent.context import SessionContext, add_turn

        context = SessionContext(
            session_id="test",
            session_anchor="Initial query",
            topic_tracker=["nike"],
        )

        turn = create_conversation_turn(
            content="Now show Adidas spending",
            role="user",
            extracted_dimensions=create_dimension_values(brand=["adidas"]),
        )

        updated = add_turn(context, turn)

        assert "adidas" in updated.topic_tracker

    def test_fr_1_2_add_turn_preserves_session_anchor_reference(self) -> None:
        """Test that session anchor turn is preserved."""
        from src.agent.context import SessionContext, add_turn

        anchor_turn = create_conversation_turn(
            content="Show Nike spending",
            role="user",
            is_session_anchor=True,
        )

        context = SessionContext(
            session_id="test",
            session_anchor="Show Nike spending",
        )

        updated = add_turn(context, anchor_turn)

        # The anchor should be in the turns
        anchor_in_turns = [t for t in updated.recent_turns if t.is_sessionAnchor]
        assert len(anchor_in_turns) >= 1


# ============================================================================
# Tests for Sliding Window (FR-1.2)
# ============================================================================


class TestSlidingWindow:
    """Tests for maintaining minimum turns with sliding window."""

    def test_fr_1_2_enforce_minimum_turns_small_context(self) -> None:
        """Test minimum turns enforced even with small context."""
        from src.agent.context import SessionContext, enforce_minimum_turns

        turns = [
            create_conversation_turn(f"Query {i}")
            for i in range(2)
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Anchor",
            recent_turns=turns,
        )

        result = enforce_minimum_turns(context)

        # Should keep all turns since we have fewer than MIN_TURNS_TO_KEEP
        assert len(result.recent_turns) == 2

    def test_fr_1_2_enforce_minimum_turns_large_context(self) -> None:
        """Test minimum turns enforced with sliding window."""
        from src.agent.context import SessionContext, enforce_minimum_turns

        turns = [
            create_conversation_turn(f"Query {i}")
            for i in range(10)
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Anchor",
            recent_turns=turns,
        )

        result = enforce_minimum_turns(context)

        # Should keep at least MIN_TURNS_TO_KEEP turns
        assert len(result.recent_turns) >= MIN_TURNS_TO_KEEP

    def test_fr_1_2_enforce_minimum_turns_preserves_recent(self) -> None:
        """Test sliding window preserves most recent turns."""
        from src.agent.context import SessionContext, enforce_minimum_turns

        turns = [
            create_conversation_turn(f"Query {i}")
            for i in range(10)
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Anchor",
            recent_turns=turns,
        )

        result = enforce_minimum_turns(context)

        # Most recent turns should be preserved (last ones in list)
        # Query 9 and Query 8 should be in the result
        recent_contents = [t.content for t in result.recent_turns]
        assert "Query 9" in recent_contents
        assert "Query 8" in recent_contents


# ============================================================================
# Tests for Reference ID Tagging (FR-1.2)
# ============================================================================


class TestReferenceIdTagging:
    """Tests for tagging tool results with reference IDs."""

    def test_fr_1_2_tag_tool_result_generates_reference_id(self) -> None:
        """Test tagging tool result generates reference ID."""
        from src.agent.context import tag_tool_result

        tool_result = {
            "tool_name": "spending_by_generation",
            "data": {"generation": "gen_z", "spending": 1500},
        }

        result = tag_tool_result(tool_result)

        assert "referenceId" in result
        assert result["referenceId"].startswith("ref_")

    def test_fr_1_2_tag_tool_result_preserves_original_data(self) -> None:
        """Test tagging preserves original tool result data."""
        from src.agent.context import tag_tool_result

        tool_result = {
            "tool_name": "spending_by_generation",
            "data": {"generation": "gen_z", "spending": 1500},
        }

        result = tag_tool_result(tool_result)

        assert result["tool_name"] == "spending_by_generation"
        assert result["data"] == {"generation": "gen_z", "spending": 1500}

    def test_fr_1_2_tag_tool_result_unique_ids(self) -> None:
        """Test each tool result gets unique reference ID."""
        from src.agent.context import tag_tool_result

        tool_result = {
            "tool_name": "test_tool",
            "data": {},
        }

        result1 = tag_tool_result(tool_result)
        result2 = tag_tool_result(tool_result)

        assert result1["referenceId"] != result2["referenceId"]


# ============================================================================
# Tests for Summarization (FR-1.2)
# ============================================================================


class TestSummarization:
    """Tests for context summarization."""

    def test_fr_1_2_summarize_preserves_session_anchor(self) -> None:
        """Test summarization always preserves session anchor."""
        from src.agent.context import SessionContext, summarize_context

        turns = [
            create_conversation_turn("Query 1"),
            create_conversation_turn("Query 2"),
            create_conversation_turn("Query 3"),
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="This is the anchor",
            recent_turns=turns,
            extracted_dimensions={"brand": ["nike"]},
        )

        result = summarize_context(context)

        assert result.session_anchor == "This is the anchor"

    def test_fr_1_2_summarize_preserves_key_dimensions(self) -> None:
        """Test summarization preserves key extracted dimensions."""
        from src.agent.context import SessionContext, summarize_context

        turns = [
            create_conversation_turn("Query 1"),
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Anchor",
            recent_turns=turns,
            extracted_dimensions={
                "brand": ["nike"],
                "generation": ["gen_z"],
                "merchant_category": ["electronics"],
            },
        )

        result = summarize_context(context)

        # Key dimensions should be preserved
        assert "brand" in result.extracted_dimensions
        assert "generation" in result.extracted_dimensions

    def test_fr_1_2_summarize_preserves_minimum_turns(self) -> None:
        """Test summarization preserves minimum required turns."""
        from src.agent.context import SessionContext, summarize_context

        turns = [
            create_conversation_turn(f"Query {i}")
            for i in range(10)
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Anchor",
            recent_turns=turns,
        )

        result = summarize_context(context)

        # Should still have minimum turns
        assert len(result.recent_turns) >= MIN_TURNS_TO_KEEP

    def test_fr_1_2_summarize_adds_topic_summary(self) -> None:
        """Test summarization adds topic summary to session."""
        from src.agent.context import SessionContext, summarize_context

        turns = [
            create_conversation_turn(
                "Show Nike spending",
                extracted_dimensions=create_dimension_values(brand=["nike"]),
            ),
            create_conversation_turn(
                "Now Adidas",
                extracted_dimensions=create_dimension_values(brand=["adidas"]),
            ),
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Anchor",
            recent_turns=turns,
            topic_tracker=["nike", "adidas"],
        )

        result = summarize_context(context)

        # Topics should be preserved
        assert len(result.topic_tracker) >= 2


# ============================================================================
# Tests for Session Boundary Detection (FR-1.2)
# ============================================================================


class TestSessionBoundaryDetection:
    """Tests for detecting new session boundaries."""

    def test_fr_1_2_is_new_session_no_history(self) -> None:
        """Test new session detection when no history exists."""
        from src.agent.context import SessionContext, is_new_session

        context = SessionContext(
            session_id="test",
            session_anchor="First query",
        )

        result = is_new_session(context)

        assert result is True

    def test_fr_1_2_is_new_session_with_history(self) -> None:
        """Test new session detection when history exists."""
        from src.agent.context import SessionContext, is_new_session

        turns = [
            create_conversation_turn("Previous query"),
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="First query",
            recent_turns=turns,
        )

        result = is_new_session(context)

        assert result is False

    def test_fr_1_2_is_new_session_topic_change(self) -> None:
        """Test new session detection on topic change."""
        from src.agent.context import SessionContext, is_new_session

        turns = [
            create_conversation_turn(
                "Show Nike spending",
                extracted_dimensions=create_dimension_values(brand=["nike"]),
            ),
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Nike query",
            recent_turns=turns,
            topic_tracker=["nike"],
            extracted_dimensions=create_dimension_values(brand=["nike"]),
        )

        # Check with different brand
        result = is_new_session(
            context,
            current_dimensions=create_dimension_values(brand=["adidas"]),
        )

        assert result is True

    def test_fr_1_2_is_new_session_same_topic(self) -> None:
        """Test no new session when topic remains same."""
        from src.agent.context import SessionContext, is_new_session

        turns = [
            create_conversation_turn(
                "Show Gen Z spending",
                extracted_dimensions=create_dimension_values(generation=["gen_z"]),
            ),
        ]

        context = SessionContext(
            session_id="test",
            session_anchor="Gen Z query",
            recent_turns=turns,
            topic_tracker=["gen_z"],
            extracted_dimensions=create_dimension_values(generation=["gen_z"]),
        )

        # Check with same generation
        result = is_new_session(
            context,
            current_dimensions=create_dimension_values(generation=["gen_z"]),
        )

        assert result is False


# ============================================================================
# Tests for Session Context Factory (FR-1.2)
# ============================================================================


class TestSessionContextFactory:
    """Tests for creating session contexts."""

    def test_fr_1_2_create_session_context(self) -> None:
        """Test creating new session context from query."""
        from src.agent.context import create_session_context

        query = "Show Gen Z spending trends"
        session_id = "test-session-123"

        result = create_session_context(query, session_id)

        assert result.session_id == session_id
        assert result.session_anchor == query
        # First turn is added as the initial turn
        assert len(result.recent_turns) == 1
        assert result.recent_turns[0].content == query
        assert result.recent_turns[0].role == "user"
        assert result.recent_turns[0].is_sessionAnchor is True
        assert result.topic_tracker == []
        assert result.model_context_limit == 128000

    def test_fr_1_2_create_session_context_custom_limit(self) -> None:
        """Test creating session context with custom model limit."""
        from src.agent.context import create_session_context

        result = create_session_context(
            query="Test",
            session_id="test",
            model_context_limit=200000,
        )

        assert result.model_context_limit == 200000

    def test_fr_1_2_create_session_context_first_turn_added(self) -> None:
        """Test that first turn is added as session anchor."""
        from src.agent.context import create_session_context

        query = "Show Gen Z spending"

        result = create_session_context(query, "test")

        # First turn should be added and marked as anchor
        assert len(result.recent_turns) == 1
        # Note: The implementation may or may not mark this as session anchor


# ============================================================================
# Tests for Serializable Format (FR-1.2)
# ============================================================================


class TestSerialization:
    """Tests for session context serialization."""

    def test_fr_1_2_session_context_to_dict(self) -> None:
        """Test SessionContext serializes to dict."""
        from src.agent.context import SessionContext

        context = SessionContext(
            session_id="test",
            session_anchor="Test query",
            topic_tracker=["topic1"],
        )

        result = context.model_dump()

        assert isinstance(result, dict)
        assert result["session_id"] == "test"
        assert result["session_anchor"] == "Test query"
        assert result["topic_tracker"] == ["topic1"]

    def test_fr_1_2_session_context_from_dict(self) -> None:
        """Test SessionContext deserializes from dict."""
        from src.agent.context import SessionContext

        data = {
            "session_id": "test",
            "session_anchor": "Test query",
            "recent_turns": [],
            "extracted_dimensions": {},
            "topic_tracker": ["topic1"],
            "model_context_limit": 128000,
        }

        result = SessionContext.model_validate(data)

        assert result.session_id == "test"
        assert result.session_anchor == "Test query"
        assert result.topic_tracker == ["topic1"]

    def test_fr_1_2_conversation_turn_serialization(self) -> None:
        """Test ConversationTurn serializes correctly."""
        from src.agent.context import ConversationTurn

        turn = ConversationTurn(
            id="turn-1",
            role="user",
            content="Test content",
            timestamp=datetime.now(),
        )

        result = turn.model_dump()

        assert isinstance(result, dict)
        assert result["id"] == "turn-1"
        assert result["role"] == "user"
