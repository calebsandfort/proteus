"""FR-2.3: Tool Retriever Tests.

Tests for the ToolRetriever abstract class and EmbeddingRetriever implementation.

FR Requirements:
- The system SHALL use OpenAI's text-embedding-3-small via OpenRouter for embeddings
- The system SHALL retrieve top-8 candidate tools based on semantic similarity
- The RAG retrieval similarity threshold SHALL be 0.70
- If the top candidate's similarity is below 0.70, the system SHALL route to HITL clarification

Test Requirements:
- Test EmbeddingRetriever initialization
- Test retrieve() method returns list of RetrievedTool
- Test retrieve() respects top_k parameter
- Test retrieve() respects similarity_threshold parameter
- Test retrieve() handles case when no tools meet threshold (returns empty list)
- Test that query is converted to embedding via OpenRouterClient
- Mock all external dependencies (ToolRegistry, OpenRouterClient)
- Tests must be deterministic — no random values
"""

from typing import List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.api.models.tool import (
    OutputField,
    RetrievedTool,
    ToolDefinition,
    ToolOutputSchema,
    ToolParameter,
)
from src.api.openrouter import DEFAULT_TOP_K, SIMILARITY_THRESHOLD


# Test fixtures

def _make_tool(
    tool_id: str,
    name: str,
    description: str,
    capabilities: List[str],
    required_dimensions: List[str],
    optional_dimensions: List[str],
    example_queries: List[str],
    aliases: List[str],
) -> ToolDefinition:
    """Factory helper to create a ToolDefinition for testing."""
    return ToolDefinition(
        id=tool_id,
        name=name,
        description=description,
        capabilities=capabilities,
        required_dimensions=required_dimensions,
        optional_dimensions=optional_dimensions,
        parameters=[
            ToolParameter(
                name="dimension",
                type="string",
                description="The dimension to query",
                required=True,
            )
        ],
        output_schema=ToolOutputSchema(
            format="json",
            description="JSON formatted output",
            fields=[
                OutputField(
                    name="value",
                    type="number",
                    description="The retrieved value",
                )
            ],
        ),
        example_queries=example_queries,
        aliases=aliases,
        version="1.0.0",
    )


TOOL_A = _make_tool(
    tool_id="tool-a",
    name="Brand Performance",
    description="Retrieves brand performance metrics including awareness, consideration, and sentiment",
    capabilities=["brand awareness", "sentiment analysis", "consideration metrics"],
    required_dimensions=["brand", "time"],
    optional_dimensions=["region", "demographic"],
    example_queries=["brand awareness trends", "consumer sentiment for brand"],
    aliases=["brand metrics", "brand health"],
)

TOOL_B = _make_tool(
    tool_id="tool-b",
    name="Competitor Analysis",
    description="Analyzes competitor performance and market share data",
    capabilities=["market share", "competitive benchmarking", "positioning analysis"],
    required_dimensions=["competitor", "time"],
    optional_dimensions=["region", "category"],
    example_queries=["competitor market share", "competitive landscape"],
    aliases=["competitive analysis", "market competitor"],
)

TOOL_C = _make_tool(
    tool_id="tool-c",
    name="Ad Spend Analytics",
    description="Tracks advertising spend across channels and campaigns",
    capabilities=["ad spend tracking", "channel attribution", "campaign performance"],
    required_dimensions=["advertiser", "time", "channel"],
    optional_dimensions=["campaign", "region"],
    example_queries=["ad spend by channel", "campaign ROI"],
    aliases=["advertising analytics", "media spend"],
)


class TestFr2_3_EmbeddingRetrieverInit:
    """Test EmbeddingRetriever initialization."""

    def test_fr_2_3_retriever_initialization_default(self):
        """Test EmbeddingRetriever initializes with correct defaults."""
        from src.agent.retrieval import EmbeddingRetriever

        with patch("src.agent.retrieval.ToolRegistry") as mock_registry_class, \
             patch("src.agent.retrieval.OpenRouterClient") as mock_client_class:
            retriever = EmbeddingRetriever()

            mock_registry_class.assert_called_once()
            mock_client_class.assert_called_once()

    def test_fr_2_3_retriever_initialization_with_custom_clients(self):
        """Test EmbeddingRetriever initializes with custom clients."""
        from src.agent.retrieval import EmbeddingRetriever

        mock_registry = MagicMock()
        mock_client = MagicMock()

        retriever = EmbeddingRetriever(
            registry=mock_registry,
            openrouter_client=mock_client,
        )

        assert retriever.registry is mock_registry
        assert retriever.openrouter_client is mock_client


class TestFr2_3_Retrieve:
    """Test retrieve() method."""

    def test_fr_2_3_retrieve_returns_list_of_retrieved_tool(self):
        """Test retrieve() returns a list of RetrievedTool objects."""
        from src.agent.retrieval import EmbeddingRetriever

        mock_registry = MagicMock()
        mock_client = MagicMock()

        # Setup mock embedding
        query_embedding = np.array([0.1] * 1536, dtype=np.float32)
        mock_client.embed_texts.return_value = [query_embedding]

        # Setup mock retrieved tools from registry
        mock_retrieved = RetrievedTool(
            tool_id="tool-a",
            tool_definition=TOOL_A,
            similarity=0.85,
            rank=1,
        )
        mock_registry.search_by_embedding.return_value = [mock_retrieved]

        retriever = EmbeddingRetriever(
            registry=mock_registry,
            openrouter_client=mock_client,
        )

        result = retriever.retrieve(query="brand performance", query_embedding=query_embedding)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], RetrievedTool)
        assert result[0].tool_id == "tool-a"
        assert result[0].similarity == 0.85

    def test_fr_2_3_retrieve_respects_top_k_parameter(self):
        """Test retrieve() returns at most top_k results."""
        from src.agent.retrieval import EmbeddingRetriever

        mock_registry = MagicMock()
        mock_client = MagicMock()

        query_embedding = np.array([0.1] * 1536, dtype=np.float32)
        mock_client.embed_texts.return_value = [query_embedding]

        # Create 5 mock retrieved tools
        mock_retrieved_tools = [
            RetrievedTool(
                tool_id=f"tool-{i}",
                tool_definition=_make_tool(
                    tool_id=f"tool-{i}",
                    name=f"Tool {i}",
                    description=f"Description {i}",
                    capabilities=[f"capability-{i}"],
                    required_dimensions=["dimension-a"],
                    optional_dimensions=[],
                    example_queries=[],
                    aliases=[],
                ),
                similarity=0.90 - (i * 0.05),
                rank=i + 1,
            )
            for i in range(5)
        ]
        mock_registry.search_by_embedding.return_value = mock_retrieved_tools

        retriever = EmbeddingRetriever(
            registry=mock_registry,
            openrouter_client=mock_client,
        )

        # Request only top 3
        result = retriever.retrieve(
            query="test query",
            query_embedding=query_embedding,
            top_k=3,
        )

        assert len(result) == 3
        mock_registry.search_by_embedding.assert_called_once_with(
            query_embedding=query_embedding,
            top_k=3,
        )

    def test_fr_2_3_retrieve_respects_similarity_threshold_parameter(self):
        """Test retrieve() filters by similarity_threshold parameter."""
        from src.agent.retrieval import EmbeddingRetriever

        mock_registry = MagicMock()
        mock_client = MagicMock()

        query_embedding = np.array([0.1] * 1536, dtype=np.float32)
        mock_client.embed_texts.return_value = [query_embedding]

        # Mock registry returns 3 tools with different similarities
        mock_retrieved_tools = [
            RetrievedTool(
                tool_id="tool-high",
                tool_definition=TOOL_A,
                similarity=0.95,
                rank=1,
            ),
            RetrievedTool(
                tool_id="tool-medium",
                tool_definition=TOOL_B,
                similarity=0.80,
                rank=2,
            ),
            RetrievedTool(
                tool_id="tool-low",
                tool_definition=TOOL_C,
                similarity=0.65,
                rank=3,
            ),
        ]
        mock_registry.search_by_embedding.return_value = mock_retrieved_tools

        retriever = EmbeddingRetriever(
            registry=mock_registry,
            openrouter_client=mock_client,
        )

        # Use threshold of 0.75 - should filter out tool-low
        result = retriever.retrieve(
            query="test query",
            query_embedding=query_embedding,
            similarity_threshold=0.75,
        )

        assert len(result) == 2
        assert all(r.similarity >= 0.75 for r in result)

    def test_fr_2_3_retrieve_returns_empty_list_when_no_tools_meet_threshold(self):
        """Test retrieve() returns empty list when no tools meet threshold."""
        from src.agent.retrieval import EmbeddingRetriever

        mock_registry = MagicMock()
        mock_client = MagicMock()

        query_embedding = np.array([0.1] * 1536, dtype=np.float32)
        mock_client.embed_texts.return_value = [query_embedding]

        # Mock registry returns only low-similarity tools
        mock_retrieved_tools = [
            RetrievedTool(
                tool_id="tool-low",
                tool_definition=TOOL_A,
                similarity=0.50,
                rank=1,
            ),
            RetrievedTool(
                tool_id="tool-lower",
                tool_definition=TOOL_B,
                similarity=0.45,
                rank=2,
            ),
        ]
        mock_registry.search_by_embedding.return_value = mock_retrieved_tools

        retriever = EmbeddingRetriever(
            registry=mock_registry,
            openrouter_client=mock_client,
        )

        result = retriever.retrieve(
            query="test query",
            query_embedding=query_embedding,
            similarity_threshold=0.70,
        )

        assert result == []

    def test_fr_2_3_retrieve_uses_openrouter_for_embedding(self):
        """Test that retrieve() converts query to embedding via OpenRouterClient."""
        from src.agent.retrieval import EmbeddingRetriever

        mock_registry = MagicMock()
        mock_client = MagicMock()

        expected_embedding = np.array([0.5] * 1536, dtype=np.float32)
        mock_client.embed_texts.return_value = [expected_embedding]

        mock_registry.search_by_embedding.return_value = []

        retriever = EmbeddingRetriever(
            registry=mock_registry,
            openrouter_client=mock_client,
        )

        query_text = "brand performance analysis"
        result = retriever.retrieve(query=query_text, query_embedding=expected_embedding)

        # Verify embed_texts was called with the query text
        mock_client.embed_texts.assert_called_once_with([query_text])

    def test_fr_2_3_retrieve_uses_default_top_k(self):
        """Test retrieve() uses DEFAULT_TOP_K when not specified."""
        from src.agent.retrieval import EmbeddingRetriever

        mock_registry = MagicMock()
        mock_client = MagicMock()

        query_embedding = np.array([0.1] * 1536, dtype=np.float32)
        mock_client.embed_texts.return_value = [query_embedding]
        mock_registry.search_by_embedding.return_value = []

        retriever = EmbeddingRetriever(
            registry=mock_registry,
            openrouter_client=mock_client,
        )

        retriever.retrieve(query="test", query_embedding=query_embedding)

        mock_registry.search_by_embedding.assert_called_once_with(
            query_embedding=query_embedding,
            top_k=DEFAULT_TOP_K,
        )

    def test_fr_2_3_retrieve_uses_default_similarity_threshold(self):
        """Test retrieve() uses SIMILARITY_THRESHOLD when not specified."""
        from src.agent.retrieval import EmbeddingRetriever

        mock_registry = MagicMock()
        mock_client = MagicMock()

        query_embedding = np.array([0.1] * 1536, dtype=np.float32)
        mock_client.embed_texts.return_value = [query_embedding]

        # Return a tool that meets the default threshold
        mock_retrieved = RetrievedTool(
            tool_id="tool-a",
            tool_definition=TOOL_A,
            similarity=0.85,
            rank=1,
        )
        mock_registry.search_by_embedding.return_value = [mock_retrieved]

        retriever = EmbeddingRetriever(
            registry=mock_registry,
            openrouter_client=mock_client,
        )

        result = retriever.retrieve(query="test", query_embedding=query_embedding)

        # Result should be filtered by SIMILARITY_THRESHOLD (0.70)
        assert len(result) == 1
        assert result[0].similarity >= SIMILARITY_THRESHOLD


class TestFr2_3_ToolRetrieverInterface:
    """Test that ToolRetriever abstract class is properly defined."""

    def test_fr_2_3_tool_retriever_is_abstract(self):
        """Test ToolRetriever cannot be instantiated directly."""
        from src.agent.retrieval import ToolRetriever

        with pytest.raises(TypeError) as exc_info:
            ToolRetriever()

        assert "abstract" in str(exc_info.value).lower()

    def test_fr_2_3_embedding_retriever_is_subclass(self):
        """Test EmbeddingRetriever is a subclass of ToolRetriever."""
        from src.agent.retrieval import EmbeddingRetriever, ToolRetriever

        assert issubclass(EmbeddingRetriever, ToolRetriever)
