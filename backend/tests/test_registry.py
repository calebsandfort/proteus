"""Tests for FR-2.1: Tool Registry.

This module tests the ToolRegistry class for the Tool Registry & RAG Retrieval system.

FR Requirements:
- The system SHALL maintain a registry of 12-15 core data retrieval tools
- Tool definitions SHALL be stored as embeddings for semantic retrieval
- Tools SHALL be addable, modifiable, or deprecated without pipeline changes
- FR-2.2 Core Tool Set (14 tools):
  - P0: market_share_trend, brand_comparison, yoy_growth_analysis, same_store_sales, category_trends, wallet_share
  - P1: cross_shopping_overlap, demographic_breakdown, geographic_breakdown, customer_retention
  - P2: top_n_rankings, channel_analysis, basket_analysis, promotional_sensitivity

Interface Contract:
    class ToolRegistry:
        def register(self, tool: ToolDefinition) -> None
        def get(self, tool_id: str) -> Optional[ToolDefinition]
        def list_active(self) -> List[ToolDefinition]
        def search_by_embedding(self, query_embedding: np.ndarray, top_k: int = 8) -> List[RetrievedTool]

Test Requirements:
- Name each test after the FR it verifies: test_fr_2_1_...
- Test ToolRegistry initialization
- Test register() method - can register a tool definition
- Test get() method - can retrieve registered tool by id
- Test get() returns None for non-existent tool
- Test list_active() - returns all registered tools
- Test search_by_embedding() - returns list of RetrievedTool sorted by similarity
- Test search_by_embedding() respects top_k parameter
- Test search_by_embedding() respects similarity threshold (0.70)
- Mock OpenRouterClient for embedding generation
- Tests must be deterministic — no random values
"""

from pathlib import Path
import tempfile
from typing import List, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.api.models.tool import (
    ToolDefinition,
    ToolOutputSchema,
    ToolParameter,
    RetrievedTool,
    OutputField,
)
from src.api.openrouter import SIMILARITY_THRESHOLD, DEFAULT_TOP_K


@pytest.fixture
def empty_tools_dir():
    """Provides a temporary empty directory for tool loading tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_test_tool(
    tool_id: str,
    name: str,
    description: str,
    capabilities: List[str],
    required_dimensions: List[str],
    optional_dimensions: Optional[List[str]] = None,
    parameters: Optional[List[ToolParameter]] = None,
    example_queries: Optional[List[str]] = None,
    aliases: Optional[List[str]] = None,
    version: str = "1.0.0",
) -> ToolDefinition:
    """Helper to create a test tool definition."""
    return ToolDefinition(
        id=tool_id,
        name=name,
        description=description,
        capabilities=capabilities,
        required_dimensions=required_dimensions,
        optional_dimensions=optional_dimensions or [],
        parameters=parameters or [],
        output_schema=ToolOutputSchema(
            format="json",
            description=f"Output schema for {name}",
            fields=[
                OutputField(name="result", type="string", description="Result data"),
            ],
        ),
        example_queries=example_queries or [],
        aliases=aliases or [],
        version=version,
    )


class TestFr21ToolRegistryInitialization:
    """FR-2.1: ToolRegistry initialization tests."""

    def test_fr_2_1_registry_can_be_instantiated(self, empty_tools_dir) -> None:
        """ToolRegistry can be instantiated."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)
            assert registry is not None

    def test_fr_2_1_registry_starts_empty(self, empty_tools_dir) -> None:
        """ToolRegistry starts with no tools registered."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)
            active_tools = registry.list_active()
            assert active_tools == []


class TestFr21ToolRegistryRegister:
    """FR-2.1: ToolRegistry register() method tests."""

    def test_fr_2_1_register_adds_tool_to_registry(self, empty_tools_dir) -> None:
        """register() adds a tool definition to the registry."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)
            tool = create_test_tool(
                tool_id="market_share_trend",
                name="Market Share Trend",
                description="Analyzes market share trends",
                capabilities=["Calculate market share", "Track trends"],
                required_dimensions=["category", "time_period"],
                aliases=["market_share", "share_trend"],
            )

            registry.register(tool)

            retrieved = registry.get("market_share_trend")
            assert retrieved is not None
            assert retrieved.id == "market_share_trend"
            assert retrieved.name == "Market Share Trend"

    def test_fr_2_1_register_stores_embedding(self, empty_tools_dir) -> None:
        """register() generates and stores embedding for the tool."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            # Mock embed_texts to return a deterministic embedding
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3, 0.4, 0.5])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)
            tool = create_test_tool(
                tool_id="test_tool",
                name="Test Tool",
                description="A test tool",
                capabilities=["Test capability"],
                required_dimensions=["category"],
            )

            registry.register(tool)

            # Verify embed_texts was called
            mock_client.embed_texts.assert_called_once()

    def test_fr_2_1_register_multiple_tools(self, empty_tools_dir) -> None:
        """register() can add multiple tools to the registry."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            tool1 = create_test_tool(
                tool_id="tool_1",
                name="Tool One",
                description="First tool",
                capabilities=["Do thing 1"],
                required_dimensions=["category"],
            )
            tool2 = create_test_tool(
                tool_id="tool_2",
                name="Tool Two",
                description="Second tool",
                capabilities=["Do thing 2"],
                required_dimensions=["category"],
            )

            registry.register(tool1)
            registry.register(tool2)

            assert registry.get("tool_1") is not None
            assert registry.get("tool_2") is not None
            assert len(registry.list_active()) == 2


class TestFr21ToolRegistryGet:
    """FR-2.1: ToolRegistry get() method tests."""

    def test_fr_2_1_get_retrieves_registered_tool(self, empty_tools_dir) -> None:
        """get() retrieves a registered tool by id."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)
            tool = create_test_tool(
                tool_id="brand_comparison",
                name="Brand Comparison",
                description="Compare brands",
                capabilities=["Compare brand metrics"],
                required_dimensions=["category", "brands"],
            )

            registry.register(tool)
            retrieved = registry.get("brand_comparison")

            assert retrieved is not None
            assert retrieved.id == "brand_comparison"
            assert retrieved.name == "Brand Comparison"

    def test_fr_2_1_get_returns_none_for_nonexistent(self, empty_tools_dir) -> None:
        """get() returns None for tool that does not exist."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)
            result = registry.get("nonexistent_tool")

            assert result is None

    def test_fr_2_1_get_returns_none_after_deprecation(self, empty_tools_dir) -> None:
        """get() returns None for a deprecated tool (not in active list)."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)
            tool = create_test_tool(
                tool_id="old_tool",
                name="Old Tool",
                description="An old tool",
                capabilities=["Old capability"],
                required_dimensions=["category"],
            )

            registry.register(tool)
            assert registry.get("old_tool") is not None

            # Deprecate by removing from active
            registry._tools["old_tool"].is_active = False  # type: ignore

            assert registry.get("old_tool") is None


class TestFr21ToolRegistryListActive:
    """FR-2.1: ToolRegistry list_active() method tests."""

    def test_fr_2_1_list_active_returns_all_active_tools(self, empty_tools_dir) -> None:
        """list_active() returns all registered active tools."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            tool1 = create_test_tool(
                tool_id="tool_1",
                name="Tool One",
                description="First tool",
                capabilities=["Do thing 1"],
                required_dimensions=["category"],
            )
            tool2 = create_test_tool(
                tool_id="tool_2",
                name="Tool Two",
                description="Second tool",
                capabilities=["Do thing 2"],
                required_dimensions=["category"],
            )
            tool3 = create_test_tool(
                tool_id="tool_3",
                name="Tool Three",
                description="Third tool",
                capabilities=["Do thing 3"],
                required_dimensions=["category"],
            )

            registry.register(tool1)
            registry.register(tool2)
            registry.register(tool3)

            active = registry.list_active()
            assert len(active) == 3

    def test_fr_2_1_list_active_returns_empty_when_no_tools(self, empty_tools_dir) -> None:
        """list_active() returns empty list when no tools registered."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)
            active = registry.list_active()

            assert active == []


class TestFr21ToolRegistrySearchByEmbedding:
    """FR-2.1: ToolRegistry search_by_embedding() method tests."""

    def test_fr_2_1_search_by_embedding_returns_retrieved_tools(self, empty_tools_dir) -> None:
        """search_by_embedding() returns list of RetrievedTool objects."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            tool = create_test_tool(
                tool_id="market_share_trend",
                name="Market Share Trend",
                description="Analyzes market share trends",
                capabilities=["Calculate market share", "Track trends"],
                required_dimensions=["category", "time_period"],
            )
            registry.register(tool)

            # Query embedding - deterministic values
            query_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

            results = registry.search_by_embedding(query_embedding)

            assert isinstance(results, list)
            assert all(isinstance(r, RetrievedTool) for r in results)

    def test_fr_2_1_search_by_embedding_returns_sorted_by_similarity(self, empty_tools_dir) -> None:
        """search_by_embedding() returns results sorted by similarity descending."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            # Return different embeddings for different tools
            mock_client.embed_texts.side_effect = [
                [np.array([1.0, 0.0, 0.0, 0.0])],  # Tool 1 - high sim to [1,0,0,0]
                [np.array([0.0, 1.0, 0.0, 0.0])],  # Tool 2 - high sim to [0,1,0,0]
                [np.array([0.0, 0.0, 1.0, 0.0])],  # Tool 3 - high sim to [0,0,1,0]
            ]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            tool1 = create_test_tool(
                tool_id="exact_match",
                name="Exact Match Tool",
                description="This tool matches perfectly",
                capabilities=["Exact capability"],
                required_dimensions=["category"],
                aliases=["exact"],
            )
            tool2 = create_test_tool(
                tool_id="partial_match",
                name="Partial Match Tool",
                description="This tool partially matches",
                capabilities=["Partial capability"],
                required_dimensions=["category"],
                aliases=["partial"],
            )
            tool3 = create_test_tool(
                tool_id="no_match",
                name="No Match Tool",
                description="This tool does not match",
                capabilities=["No capability"],
                required_dimensions=["category"],
                aliases=["none"],
            )

            registry.register(tool1)
            registry.register(tool2)
            registry.register(tool3)

            # Query with embedding similar to tool1
            query_embedding = np.array([0.95, 0.05, 0.0, 0.0])

            results = registry.search_by_embedding(query_embedding)

            assert len(results) > 0
            # First result should have highest similarity
            assert results[0].similarity >= results[-1].similarity

    def test_fr_2_1_search_by_embedding_respects_top_k(self, empty_tools_dir) -> None:
        """search_by_embedding() respects the top_k parameter."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            # Return different embeddings for different tools
            mock_client.embed_texts.side_effect = [
                [np.array([0.9, 0.1, 0.0, 0.0])],
                [np.array([0.7, 0.3, 0.0, 0.0])],
                [np.array([0.5, 0.5, 0.0, 0.0])],
                [np.array([0.3, 0.7, 0.0, 0.0])],
                [np.array([0.1, 0.9, 0.0, 0.0])],
            ]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            for i in range(5):
                tool = create_test_tool(
                    tool_id=f"tool_{i}",
                    name=f"Tool {i}",
                    description=f"Tool number {i}",
                    capabilities=[f"Capability {i}"],
                    required_dimensions=["category"],
                )
                registry.register(tool)

            query_embedding = np.array([1.0, 0.0, 0.0, 0.0])

            # Request top 2
            results_top2 = registry.search_by_embedding(query_embedding, top_k=2)
            assert len(results_top2) == 2

            # Request top 3
            results_top3 = registry.search_by_embedding(query_embedding, top_k=3)
            assert len(results_top3) == 3

    def test_fr_2_1_search_by_embedding_respects_similarity_threshold(self, empty_tools_dir) -> None:
        """search_by_embedding() filters out results below SIMILARITY_THRESHOLD (0.70)."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            # For cosine similarity to equal a value v, embedding first component must be v
            # AND the embedding must be normalized (norm = 1.0)
            # To get 0.50 similarity: first_component / norm = 0.50 => norm must be 1.0
            # So embedding = [0.50, sqrt(1-0.50^2), 0, 0] = [0.50, 0.866, 0, 0]
            # To get 0.75 similarity: embedding = [0.75, sqrt(1-0.75^2), 0, 0] = [0.75, 0.661, 0, 0]
            # To get 0.95 similarity: embedding = [0.95, sqrt(1-0.95^2), 0, 0] = [0.95, 0.312, 0, 0]
            import math
            mock_client.embed_texts.side_effect = [
                [np.array([0.95, math.sqrt(1-0.95**2), 0.0, 0.0])],  # Tool 1 - 0.95 similarity
                [np.array([0.75, math.sqrt(1-0.75**2), 0.0, 0.0])],  # Tool 2 - 0.75 similarity (just above 0.70)
                [np.array([0.50, math.sqrt(1-0.50**2), 0.0, 0.0])],  # Tool 3 - 0.50 similarity (below 0.70)
            ]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            for i in range(3):
                tool = create_test_tool(
                    tool_id=f"tool_{i}",
                    name=f"Tool {i}",
                    description=f"Tool number {i}",
                    capabilities=[f"Capability {i}"],
                    required_dimensions=["category"],
                )
                registry.register(tool)

            query_embedding = np.array([1.0, 0.0, 0.0, 0.0])

            results = registry.search_by_embedding(query_embedding, top_k=8)

            # All returned results should have similarity >= 0.70
            assert all(r.similarity >= SIMILARITY_THRESHOLD for r in results)
            # Tool 3 (0.50 similarity) should not be in results
            tool_ids = [r.tool_id for r in results]
            assert "tool_2" not in tool_ids

    def test_fr_2_1_search_by_embedding_returns_empty_when_all_below_threshold(
        self,
        empty_tools_dir,
    ) -> None:
        """search_by_embedding() returns empty list when all tools below threshold."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            # All tools have similarity below 0.70 threshold
            # For 0.50 similarity: embedding = [0.50, sqrt(1-0.50^2), 0, 0] = [0.50, 0.866, 0, 0]
            # For 0.60 similarity: embedding = [0.60, sqrt(1-0.60^2), 0, 0] = [0.60, 0.80, 0, 0]
            import math
            mock_client.embed_texts.side_effect = [
                [np.array([0.50, math.sqrt(1-0.50**2), 0.0, 0.0])],  # 0.50 similarity
                [np.array([0.60, math.sqrt(1-0.60**2), 0.0, 0.0])],  # 0.60 similarity
            ]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            tool1 = create_test_tool(
                tool_id="low_match_1",
                name="Low Match 1",
                description="Low similarity tool",
                capabilities=["Low capability"],
                required_dimensions=["category"],
            )
            tool2 = create_test_tool(
                tool_id="low_match_2",
                name="Low Match 2",
                description="Low similarity tool 2",
                capabilities=["Low capability 2"],
                required_dimensions=["category"],
            )

            registry.register(tool1)
            registry.register(tool2)

            query_embedding = np.array([1.0, 0.0, 0.0, 0.0])

            results = registry.search_by_embedding(query_embedding)

            assert results == []

    def test_fr_2_1_search_by_embedding_uses_cosine_similarity(self, empty_tools_dir) -> None:
        """search_by_embedding() uses cosine similarity for ranking."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.5, 0.5, 0.5, 0.5])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            tool = create_test_tool(
                tool_id="test_tool",
                name="Test Tool",
                description="Test tool for cosine similarity",
                capabilities=["Test capability"],
                required_dimensions=["category"],
            )
            registry.register(tool)

            # Query with exact same embedding should give similarity of 1.0
            query_embedding = np.array([0.5, 0.5, 0.5, 0.5])

            results = registry.search_by_embedding(query_embedding)

            assert len(results) == 1
            assert results[0].similarity == pytest.approx(1.0, rel=0.01)

    def test_fr_2_1_search_by_embedding_includes_rank(self, empty_tools_dir) -> None:
        """search_by_embedding() returns results with correct rank values."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.side_effect = [
                [np.array([0.9, 0.1, 0.0, 0.0])],
                [np.array([0.8, 0.2, 0.0, 0.0])],
                [np.array([0.7, 0.3, 0.0, 0.0])],
            ]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            for i in range(3):
                tool = create_test_tool(
                    tool_id=f"tool_{i}",
                    name=f"Tool {i}",
                    description=f"Tool {i}",
                    capabilities=[f"Capability {i}"],
                    required_dimensions=["category"],
                )
                registry.register(tool)

            query_embedding = np.array([1.0, 0.0, 0.0, 0.0])

            results = registry.search_by_embedding(query_embedding, top_k=3)

            assert len(results) == 3
            # Ranks should be 1, 2, 3
            for i, result in enumerate(results):
                assert result.rank == i + 1


class TestFr21ToolRegistryCoreToolSet:
    """FR-2.1: Verify all 14 core tools can be registered."""

    def test_fr_2_1_p0_tools_all_registerable(self, empty_tools_dir) -> None:
        """All P0 tools (6) can be registered in the registry."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            p0_tools = [
                ("market_share_trend", "Market Share Trend"),
                ("brand_comparison", "Brand Comparison"),
                ("yoy_growth_analysis", "YoY Growth Analysis"),
                ("same_store_sales", "Same Store Sales"),
                ("category_trends", "Category Trends"),
                ("wallet_share", "Wallet Share"),
            ]

            for tool_id, name in p0_tools:
                tool = create_test_tool(
                    tool_id=tool_id,
                    name=name,
                    description=f"{name} tool",
                    capabilities=["Analyze"],
                    required_dimensions=["category"],
                )
                registry.register(tool)

            assert len(registry.list_active()) == 6

    def test_fr_2_1_p1_tools_all_registerable(self, empty_tools_dir) -> None:
        """All P1 tools (4) can be registered in the registry."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            p1_tools = [
                ("cross_shopping_overlap", "Cross-Shopping Overlap"),
                ("demographic_breakdown", "Demographic Breakdown"),
                ("geographic_breakdown", "Geographic Breakdown"),
                ("customer_retention", "Customer Retention"),
            ]

            for tool_id, name in p1_tools:
                tool = create_test_tool(
                    tool_id=tool_id,
                    name=name,
                    description=f"{name} tool",
                    capabilities=["Analyze"],
                    required_dimensions=["category"],
                )
                registry.register(tool)

            assert len(registry.list_active()) == 4

    def test_fr_2_1_p2_tools_all_registerable(self, empty_tools_dir) -> None:
        """All P2 tools (4) can be registered in the registry."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            p2_tools = [
                ("top_n_rankings", "Top N Rankings"),
                ("channel_analysis", "Channel Analysis"),
                ("basket_analysis", "Basket Analysis"),
                ("promotional_sensitivity", "Promotional Sensitivity"),
            ]

            for tool_id, name in p2_tools:
                tool = create_test_tool(
                    tool_id=tool_id,
                    name=name,
                    description=f"{name} tool",
                    capabilities=["Analyze"],
                    required_dimensions=["category"],
                )
                registry.register(tool)

            assert len(registry.list_active()) == 4

    def test_fr_2_1_all_14_core_tools_registerable(self, empty_tools_dir) -> None:
        """All 14 core tools (P0 + P1 + P2) can be registered."""
        with patch("src.agent.registry.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.embed_texts.return_value = [np.array([0.1, 0.2, 0.3])]
            mock_client_class.return_value = mock_client

            from src.agent.registry import ToolRegistry

            registry = ToolRegistry(tools_dir=empty_tools_dir)

            all_tools = [
                # P0
                ("market_share_trend", "Market Share Trend"),
                ("brand_comparison", "Brand Comparison"),
                ("yoy_growth_analysis", "YoY Growth Analysis"),
                ("same_store_sales", "Same Store Sales"),
                ("category_trends", "Category Trends"),
                ("wallet_share", "Wallet Share"),
                # P1
                ("cross_shopping_overlap", "Cross-Shopping Overlap"),
                ("demographic_breakdown", "Demographic Breakdown"),
                ("geographic_breakdown", "Geographic Breakdown"),
                ("customer_retention", "Customer Retention"),
                # P2
                ("top_n_rankings", "Top N Rankings"),
                ("channel_analysis", "Channel Analysis"),
                ("basket_analysis", "Basket Analysis"),
                ("promotional_sensitivity", "Promotional Sensitivity"),
            ]

            for tool_id, name in all_tools:
                tool = create_test_tool(
                    tool_id=tool_id,
                    name=name,
                    description=f"{name} tool",
                    capabilities=["Analyze"],
                    required_dimensions=["category"],
                )
                registry.register(tool)

            assert len(registry.list_active()) == 14


class TestFr21Imports:
    """FR-2.1: Module import tests."""

    def test_fr_2_1_import_tool_registry(self) -> None:
        """ToolRegistry can be imported."""
        with patch("src.agent.registry.OpenRouterClient"):
            from src.agent.registry import ToolRegistry

            assert ToolRegistry is not None

    def test_fr_2_1_import_constants(self) -> None:
        """Constants can be imported from openrouter module."""
        from src.api.openrouter import SIMILARITY_THRESHOLD, DEFAULT_TOP_K

        assert SIMILARITY_THRESHOLD is not None
        assert DEFAULT_TOP_K is not None
