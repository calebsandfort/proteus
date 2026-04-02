"""Tests for agent prompt templates (FR-7.2)."""

import pytest


class TestPlannerPrompt:
    """Tests for PLANNER_PROMPT template."""

    def test_planner_prompt_exists(self):
        """Test that PLANNER_PROMPT is defined as a module constant."""
        from src.agent.prompts import PLANNER_PROMPT
        assert PLANNER_PROMPT is not None
        assert isinstance(PLANNER_PROMPT, str)

    def test_planner_prompt_contains_query_placeholder(self):
        """Test that PLANNER_PROMPT has {query} placeholder."""
        from src.agent.prompts import PLANNER_PROMPT
        assert "{query}" in PLANNER_PROMPT

    def test_planner_prompt_contains_retrieved_tools_placeholder(self):
        """Test that PLANNER_PROMPT has {retrieved_tools} placeholder."""
        from src.agent.prompts import PLANNER_PROMPT
        assert "{retrieved_tools}" in PLANNER_PROMPT

    def test_planner_prompt_contains_extracted_dimensions_placeholder(self):
        """Test that PLANNER_PROMPT has {extracted_dimensions} placeholder."""
        from src.agent.prompts import PLANNER_PROMPT
        assert "{extracted_dimensions}" in PLANNER_PROMPT

    def test_planner_prompt_render_with_variables(self):
        """Test that PLANNER_PROMPT renders correctly with all variables."""
        from src.agent.prompts import PLANNER_PROMPT

        query = "Show me Walmart sales in California last quarter"
        retrieved_tools = "tool_1: sales_by_brand_geography"
        extracted_dimensions = "brand: Walmart, geography: CA, time_range: Q4 2024"

        rendered = PLANNER_PROMPT.format(
            query=query,
            retrieved_tools=retrieved_tools,
            extracted_dimensions=extracted_dimensions
        )

        assert query in rendered
        assert retrieved_tools in rendered
        assert extracted_dimensions in rendered

    def test_planner_prompt_contains_glm4_air_hint(self):
        """Test that PLANNER_PROMPT hints at using GLM-4-Air model."""
        from src.agent.prompts import PLANNER_PROMPT
        assert "GLM-4-Air" in PLANNER_PROMPT


class TestToolSelectionPrompt:
    """Tests for TOOL_SELECTION_PROMPT template."""

    def test_tool_selection_prompt_exists(self):
        """Test that TOOL_SELECTION_PROMPT is defined as a module constant."""
        from src.agent.prompts import TOOL_SELECTION_PROMPT
        assert TOOL_SELECTION_PROMPT is not None
        assert isinstance(TOOL_SELECTION_PROMPT, str)

    def test_tool_selection_prompt_contains_query_placeholder(self):
        """Test that TOOL_SELECTION_PROMPT has {query} placeholder."""
        from src.agent.prompts import TOOL_SELECTION_PROMPT
        assert "{query}" in TOOL_SELECTION_PROMPT

    def test_tool_selection_prompt_contains_retrieved_tools_placeholder(self):
        """Test that TOOL_SELECTION_PROMPT has {retrieved_tools} placeholder."""
        from src.agent.prompts import TOOL_SELECTION_PROMPT
        assert "{retrieved_tools}" in TOOL_SELECTION_PROMPT

    def test_tool_selection_prompt_contains_extracted_dimensions_placeholder(self):
        """Test that TOOL_SELECTION_PROMPT has {extracted_dimensions} placeholder."""
        from src.agent.prompts import TOOL_SELECTION_PROMPT
        assert "{extracted_dimensions}" in TOOL_SELECTION_PROMPT

    def test_tool_selection_prompt_contains_rag_scores_placeholder(self):
        """Test that TOOL_SELECTION_PROMPT has {rag_scores} placeholder."""
        from src.agent.prompts import TOOL_SELECTION_PROMPT
        assert "{rag_scores}" in TOOL_SELECTION_PROMPT

    def test_tool_selection_prompt_render_with_variables(self):
        """Test that TOOL_SELECTION_PROMPT renders correctly with all variables."""
        from src.agent.prompts import TOOL_SELECTION_PROMPT

        query = "Show me Walmart sales"
        retrieved_tools = "tool_1: sales_by_brand"
        extracted_dimensions = "brand: Walmart"
        rag_scores = "tool_1: 0.92"

        rendered = TOOL_SELECTION_PROMPT.format(
            query=query,
            retrieved_tools=retrieved_tools,
            extracted_dimensions=extracted_dimensions,
            rag_scores=rag_scores
        )

        assert query in rendered
        assert retrieved_tools in rendered
        assert extracted_dimensions in rendered
        assert rag_scores in rendered

    def test_tool_selection_prompt_contains_minimax_hint(self):
        """Test that TOOL_SELECTION_PROMPT hints at using MiniMax-Text-01 model."""
        from src.agent.prompts import TOOL_SELECTION_PROMPT
        assert "MiniMax-Text-01" in TOOL_SELECTION_PROMPT

    def test_tool_selection_prompt_contains_confidence_breakdown(self):
        """Test that TOOL_SELECTION_PROMPT includes confidence breakdown fields."""
        from src.agent.prompts import TOOL_SELECTION_PROMPT
        # Check for the specific breakdown components
        assert "confidence_breakdown" in TOOL_SELECTION_PROMPT
        assert "rag_similarity" in TOOL_SELECTION_PROMPT
        assert "llm_selection" in TOOL_SELECTION_PROMPT
        assert "dimension_match" in TOOL_SELECTION_PROMPT


class TestExtractionPrompt:
    """Tests for EXTRACTION_PROMPT template."""

    def test_extraction_prompt_exists(self):
        """Test that EXTRACTION_PROMPT is defined as a module constant."""
        from src.agent.prompts import EXTRACTION_PROMPT
        assert EXTRACTION_PROMPT is not None
        assert isinstance(EXTRACTION_PROMPT, str)

    def test_extraction_prompt_contains_query_placeholder(self):
        """Test that EXTRACTION_PROMPT has {query} placeholder."""
        from src.agent.prompts import EXTRACTION_PROMPT
        assert "{query}" in EXTRACTION_PROMPT

    def test_extraction_prompt_render_with_query(self):
        """Test that EXTRACTION_PROMPT renders correctly with query variable."""
        from src.agent.prompts import EXTRACTION_PROMPT

        query = "Show me Target sales in Texas for millennials"

        rendered = EXTRACTION_PROMPT.format(query=query)

        assert query in rendered

    def test_extraction_prompt_contains_dimension_fields(self):
        """Test that EXTRACTION_PROMPT includes all required dimension fields."""
        from src.agent.prompts import EXTRACTION_PROMPT

        # Check for all required dimensions from FR-3.1-3.7
        required_dimensions = [
            "brand",
            "merchant_category",
            "geography",
            "time_range",
            "generation",
            "income_band",
            "card_type",
            "payment_network",
            "channel",
            "day_of_week"
        ]

        for dimension in required_dimensions:
            assert dimension in EXTRACTION_PROMPT, f"Missing dimension: {dimension}"


class TestExistingPromptsIntact:
    """Tests to verify existing prompts are not modified."""

    def test_system_prompt_still_exists(self):
        """Test that SYSTEM_PROMPT still exists."""
        from src.agent.prompts import SYSTEM_PROMPT
        assert SYSTEM_PROMPT is not None
        assert "helpful AI assistant" in SYSTEM_PROMPT

    def test_prompt_manager_still_exists(self):
        """Test that PromptManager class still exists."""
        from src.agent.prompts import PromptManager
        assert PromptManager is not None

    def test_prompt_version_still_exists(self):
        """Test that PromptVersion model still exists."""
        from src.agent.prompts import PromptVersion
        assert PromptVersion is not None
