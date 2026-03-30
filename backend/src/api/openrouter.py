"""OpenRouter client for routing all LLM calls through OpenRouter.

FR-8.1: All LLM calls SHALL route through OpenRouter. No direct provider API integrations.
FR-8.5: Provider Normalization - parse failures trigger retry once with same model.
FR-8.6: LLM Failure Handling - exponential backoff with jitter (max 3 retries),
        user-friendly error with request ID after exhaustion.
FR-2.3: OpenRouter Embeddings Client for RAG retrieval.

This module provides:
- OpenRouterClient: Main client for making LLM requests via OpenRouter
- UserFriendlyError: Exception with code, message, and request_id for user feedback

Interface Contract:
    class OpenRouterClient:
        def embed_texts(self, texts: List[str], model: str = "openai/text-embedding-3-small") -> List[np.ndarray]
        async def call_with_retry(self, model: str, messages: List[Dict[str, Any]], ...) -> Dict[str, Any]
"""

import asyncio
import json
import os
import random
import uuid
from typing import Any, Dict, List

import httpx
import numpy as np

from src.api.normalizers import NormalizerRegistry
from src.config import settings


# Constants for RAG retrieval (FR-2.3)
SIMILARITY_THRESHOLD: float = 0.70
"""RAG retrieval similarity threshold - tools below this score are filtered out."""

DEFAULT_TOP_K: int = 8
"""Default number of top candidate tools to retrieve."""

DEFAULT_MODEL: str = "openai/text-embedding-3-small"
"""Default embedding model for OpenRouter."""

OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/embeddings"
"""OpenRouter API endpoint for embeddings."""


class UserFriendlyError(Exception):
    """User-friendly error with code, message, and request_id.

    Used for presenting errors to users after retries have been exhausted.
    FR-8.6: Error messages must not leak sensitive data but should include
    a request ID for debugging.

    Attributes:
        code: Short error code for programmatic handling (e.g., "PARSE_FAILURE").
        message: User-friendly error message.
        request_id: Unique identifier for the failed request.
    """

    def __init__(self, code: str, message: str, request_id: str) -> None:
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(f"[{request_id}] {code}: {message}")


class OpenRouterClient:
    """Client for routing LLM calls through OpenRouter.

    All LLM calls in the system route through OpenRouter to provide
    provider-agnostic access to multiple LLM providers.

    Attributes:
        MAX_RETRIES: Maximum number of retry attempts (default: 3).
        RETRY_DELAY_BASE: Base delay for exponential backoff in seconds (default: 1.0).
        api_key: OpenRouter API key.
    """

    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1.0

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key. If not provided, reads from settings.

        Raises:
            ValueError: If no API key is available.
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenRouter client")

    def _get_provider(self, model: str) -> str:
        """Extract provider name from model string.

        Args:
            model: Model string in format 'provider/model-name' (e.g., 'openai/gpt-4o').

        Returns:
            Provider name (e.g., 'openai', 'google', 'anthropic').
        """
        return model.split("/")[0]

    async def _make_request(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> Any:
        """Make a request to the OpenRouter API.

        Args:
            model: Model identifier (e.g., 'openai/gpt-4o').
            messages: List of message dictionaries with 'role' and 'content'.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.

        Returns:
            Raw response from OpenRouter API.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(base_url="https://openrouter.ai/api/v1") as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def call_with_retry(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Make an LLM call with automatic retries on parse failure.

        FR-8.5: Parse failures trigger retry once with same model.
        FR-8.6: Exponential backoff with jitter (max 3 retries).

        Args:
            model: Model identifier (e.g., 'openai/gpt-4o').
            messages: List of message dictionaries.
            temperature: Sampling temperature (default: 0.0).
            max_tokens: Maximum tokens to generate (default: 2048).

        Returns:
            Dictionary containing parsed function calls.

        Raises:
            UserFriendlyError: After exhausting all retries with request_id for tracking.
        """
        provider = self._get_provider(model)
        normalizer = NormalizerRegistry.get_normalizer(provider)
        self._request_id = str(uuid.uuid4())[:8]

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._make_request(
                    model, messages, temperature, max_tokens
                )
                return normalizer.parse_function_calls(response)
            except (json.JSONDecodeError, ValueError, KeyError) as parse_error:
                if attempt == self.MAX_RETRIES - 1:
                    raise UserFriendlyError(
                        code="PARSE_FAILURE",
                        message="Unable to process model response. Please try again.",
                        request_id=self._request_id,
                    )
                # Exponential backoff with jitter
                delay = self.RETRY_DELAY_BASE * (2**attempt) + random.random()
                await asyncio.sleep(delay)

        # Should not reach here, but safety return
        raise UserFriendlyError(
            code="UNEXPECTED_ERROR",
            message="An unexpected error occurred.",
            request_id=self._request_id,
        )

    async def embed_texts(
        self, texts: List[str], model: str = "openai/text-embedding-3-small"
    ) -> List[Any]:
        """Generate embeddings for a list of texts.

        FR-8.1: All LLM calls route through OpenRouter.

        Args:
            texts: List of text strings to embed.
            model: Embedding model identifier (default: 'openai/text-embedding-3-small').

        Returns:
            List of embedding vectors (numpy arrays or lists).
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "input": texts,
        }

        async with httpx.AsyncClient(base_url="https://openrouter.ai/api/v1") as client:
            response = await client.post(
                "/embeddings", headers=headers, json=payload
            )
            response.raise_for_status()
            result = response.json()

            # Extract embeddings from response
            return [item["embedding"] for item in result["data"]]
