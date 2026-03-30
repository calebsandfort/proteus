"""FR-2.3: Tool Retriever.

This module provides the ToolRetriever abstract class and EmbeddingRetriever
implementation for the Tool Registry & RAG Retrieval system.

FR Requirements:
- The system SHALL use OpenAI's text-embedding-3-small via OpenRouter for embeddings
- The system SHALL retrieve top-8 candidate tools based on semantic similarity
- The RAG retrieval similarity threshold SHALL be 0.70
- If the top candidate's similarity is below 0.70, the system SHALL route to HITL clarification

Interface Contract:
    class ToolRetriever(ABC):
        @abstractmethod
        def retrieve(
            self,
            query: str,
            query_embedding: np.ndarray,
            top_k: int = 8,
            similarity_threshold: float = 0.70
        ) -> List[RetrievedTool]

Dependencies:
    - backend/src/api/models/tool.py -- ToolDefinition, RetrievedTool
    - backend/src/api/openrouter.py -- OpenRouterClient, SIMILARITY_THRESHOLD, DEFAULT_TOP_K
    - backend/src/agent/registry.py -- ToolRegistry
"""

from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np

from src.agent.registry import ToolRegistry
from src.api.models.tool import RetrievedTool
from src.api.openrouter import DEFAULT_TOP_K, SIMILARITY_THRESHOLD, OpenRouterClient


class ToolRetriever(ABC):
    """Abstract base class for tool retrieval strategies.

    Defines the interface for retrieving relevant tools based on a query
    and semantic similarity search.

    Attributes:
        registry: ToolRegistry for accessing tool definitions.
        openrouter_client: OpenRouterClient for generating embeddings.
    """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        top_k: int = 8,
        similarity_threshold: float = 0.70,
    ) -> List[RetrievedTool]:
        """Retrieve relevant tools based on semantic similarity.

        Args:
            query: The user query string (used to generate embedding if needed).
            query_embedding: Pre-computed embedding vector for the query.
            top_k: Maximum number of tools to retrieve.
            similarity_threshold: Minimum similarity score for inclusion.

        Returns:
            List of RetrievedTool objects sorted by similarity descending,
            filtered to exclude results below similarity_threshold.
        """
        pass


class EmbeddingRetriever(ToolRetriever):
    """Tool retriever using embedding-based semantic similarity.

    Uses OpenRouter embeddings to compute semantic similarity between
    the query and registered tools, returning the top-k most similar
    tools that meet the similarity threshold.

    Attributes:
        registry: ToolRegistry for accessing tool definitions with embeddings.
        openrouter_client: OpenRouterClient for generating embeddings.
    """

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        openrouter_client: Optional[OpenRouterClient] = None,
    ) -> None:
        """Initialize the EmbeddingRetriever.

        Args:
            registry: Optional ToolRegistry instance. If not provided,
                creates a new one.
            openrouter_client: Optional OpenRouterClient instance.
                If not provided, creates a new one.
        """
        self.registry = registry if registry is not None else ToolRegistry()
        self.openrouter_client = openrouter_client if openrouter_client is not None else OpenRouterClient()

    def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        top_k: int = DEFAULT_TOP_K,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
    ) -> List[RetrievedTool]:
        """Retrieve relevant tools using embedding-based similarity.

        First converts the query to an embedding, then searches the registry
        for tools with similar embeddings, filtering by the similarity threshold
        and returning at most top_k results.

        Args:
            query: The user query string (used for embedding generation).
            query_embedding: Pre-computed embedding vector for the query.
            top_k: Maximum number of tools to retrieve (default: 8).
            similarity_threshold: Minimum similarity score (default: 0.70).

        Returns:
            List of RetrievedTool objects sorted by similarity descending,
            filtered to exclude results below similarity_threshold.
        """
        # Generate embedding for the query via OpenRouter
        query_embedding = self.openrouter_client.embed_texts([query])[0]

        # Search registry for similar tools
        candidates = self.registry.search_by_embedding(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        # Filter by similarity threshold
        filtered_candidates = [
            candidate for candidate in candidates
            if candidate.similarity >= similarity_threshold
        ]

        # Apply top_k limit after filtering
        return filtered_candidates[:top_k]
