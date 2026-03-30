"""FR-2.3: OpenRouter Embeddings Client.

This module provides the OpenRouterClient for the Tool Registry & RAG Retrieval system.

FR Requirements:
- The system SHALL use OpenAI's text-embedding-3-small via OpenRouter for embeddings
- The system SHALL retrieve top-8 candidate tools based on semantic similarity
- The RAG retrieval similarity threshold SHALL be 0.70

Interface Contract:
    class OpenRouterClient:
        def embed_texts(self, texts: List[str], model: str = "openai/text-embedding-3-small") -> List[np.ndarray]
"""

import os
from typing import List

import httpx
import numpy as np


# Constants
SIMILARITY_THRESHOLD: float = 0.70
"""RAG retrieval similarity threshold - tools below this score are filtered out."""

DEFAULT_TOP_K: int = 8
"""Default number of top candidate tools to retrieve."""

DEFAULT_MODEL: str = "openai/text-embedding-3-small"
"""Default embedding model for OpenRouter."""

OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/embeddings"
"""OpenRouter API endpoint for embeddings."""


class OpenRouterClient:
    """Client for OpenRouter embeddings API.

    Uses OpenAI's text-embedding-3-small model via OpenRouter for generating
    text embeddings for semantic similarity calculations in the RAG retrieval system.

    Attributes:
        api_key: OpenRouter API key for authentication.
        model: Default embedding model to use.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL
    ) -> None:
        """Initialize the OpenRouterClient.

        Args:
            api_key: OpenRouter API key. If not provided, reads from OPENROUTER_API_KEY env var.
            model: Default embedding model. Defaults to openai/text-embedding-3-small.

        Raises:
            ValueError: If api_key is not provided and OPENROUTER_API_KEY is not set.
        """
        if api_key is None:
            api_key = os.environ.get("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        self.api_key = api_key
        self.model = model
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client.

        Returns:
            Configured httpx Client instance.
        """
        if self._client is None:
            self._client = httpx.Client(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    def embed_texts(
        self,
        texts: List[str],
        model: str | None = None
    ) -> List[np.ndarray]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.
            model: Model to use for embedding. If not provided, uses the client's default model.

        Returns:
            List of numpy arrays, each containing the embedding vector for the corresponding text.

        Raises:
            Exception: If the API request fails or returns an error.
        """
        if not texts:
            return []

        if model is None:
            model = self.model

        client = self._get_client()

        response = client.post(
            url=OPENROUTER_API_URL,
            json={
                "model": model,
                "input": texts,
            }
        )

        if response.status_code != 200:
            raise Exception(
                f"OpenRouter API error: {response.status_code} - {response.text}"
            )

        try:
            data = response.json()
        except ValueError as e:
            raise Exception(f"Invalid JSON response from OpenRouter: {e}")

        embeddings = []
        for item in data.get("data", []):
            embedding_vector = item.get("embedding", [])
            embeddings.append(np.array(embedding_vector, dtype=np.float32))

        return embeddings

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "OpenRouterClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
