"""Tests for FR-2.3: OpenRouter Embeddings Client.

This module tests the OpenRouterClient for the Tool Registry & RAG Retrieval system.

FR Requirements:
- The system SHALL use OpenAI's text-embedding-3-small via OpenRouter for embeddings
- The system SHALL retrieve top-8 candidate tools based on semantic similarity
- The RAG retrieval similarity threshold SHALL be 0.70

Test Requirements:
- Test OpenRouterClient initialization
- Test embed_texts method signature and return type
- Test similarity threshold constant (0.70)
- Test top_k default (8)
- Test model parameter default (openai/text-embedding-3-small)
- Mock ALL external API calls (don't make real HTTP requests)
- Test error handling for API failures
- Tests must be deterministic
"""

import os
from typing import List
from unittest.mock import patch, MagicMock

import numpy as np
import pytest


class TestFr23OpenRouterClientConstants:
    """FR-2.3: OpenRouterClient constants."""

    def test_fr_2_3_similarity_threshold_is_070(self) -> None:
        """RAG retrieval similarity threshold SHALL be 0.70."""
        from src.api.openrouter import SIMILARITY_THRESHOLD

        assert SIMILARITY_THRESHOLD == 0.70

    def test_fr_2_3_top_k_default_is_8(self) -> None:
        """System SHALL retrieve top-8 candidate tools by default."""
        from src.api.openrouter import DEFAULT_TOP_K

        assert DEFAULT_TOP_K == 8

    def test_fr_2_3_default_model(self) -> None:
        """System SHALL use text-embedding-3-small model."""
        from src.api.openrouter import DEFAULT_MODEL

        assert DEFAULT_MODEL == "openai/text-embedding-3-small"


class TestFr23OpenRouterClientInitialization:
    """FR-2.3: OpenRouterClient initialization."""

    def test_fr_2_3_client_requires_api_key(self) -> None:
        """OpenRouterClient requires an API key."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            client = OpenRouterClient()
            assert client.api_key == "test-key-123"

    def test_fr_2_3_client_initializes_without_error(self) -> None:
        """OpenRouterClient can be initialized with valid API key."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            client = OpenRouterClient()
            assert client is not None

    def test_fr_2_3_client_raises_without_api_key(self) -> None:
        """OpenRouterClient raises error when API key is missing."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            # Remove the key entirely to test
            original = os.environ.get("OPENROUTER_API_KEY")
            if "OPENROUTER_API_KEY" in os.environ:
                del os.environ["OPENROUTER_API_KEY"]

            try:
                from src.api.openrouter import OpenRouterClient
                with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                    OpenRouterClient()
            finally:
                if original is not None:
                    os.environ["OPENROUTER_API_KEY"] = original


class TestFr23EmbedTextsMethod:
    """FR-2.3: embed_texts method tests."""

    def test_fr_2_3_embed_texts_returns_list_of_ndarrays(self) -> None:
        """embed_texts SHALL return List[np.ndarray]."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            # Mock the HTTP request
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {"embedding": [0.1, 0.2, 0.3, 0.4, 0.5]},
                    {"embedding": [0.6, 0.7, 0.8, 0.9, 1.0]}
                ]
            }

            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = OpenRouterClient()
                result = client.embed_texts(["hello", "world"])

                assert isinstance(result, list)
                assert len(result) == 2
                assert all(isinstance(arr, np.ndarray) for arr in result)

    def test_fr_2_3_embed_texts_single_text(self) -> None:
        """embed_texts works with single text input."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3, 0.4, 0.5]}]
            }

            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = OpenRouterClient()
                result = client.embed_texts(["hello"])

                assert isinstance(result, list)
                assert len(result) == 1
                assert isinstance(result[0], np.ndarray)

    def test_fr_2_3_embed_texts_model_parameter(self) -> None:
        """embed_texts accepts custom model parameter."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }

            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = OpenRouterClient()
                result = client.embed_texts(
                    ["test"],
                    model="openai/text-embedding-3-small"
                )

                # Verify the model was passed in the request
                call_args = mock_client.post.call_args
                request_body = call_args.kwargs.get("json", {}) or call_args[1].get("json", {})
                assert request_body.get("model") == "openai/text-embedding-3-small"

    def test_fr_2_3_embed_texts_empty_list(self) -> None:
        """embed_texts handles empty list."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            client = OpenRouterClient()
            result = client.embed_texts([])

            assert result == []


class TestFr23EmbedTextsAPIIntegration:
    """FR-2.3: embed_texts API integration tests (mocked)."""

    def test_fr_2_3_embed_texts_calls_openrouter_endpoint(self) -> None:
        """embed_texts calls OpenRouter API endpoint."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }

            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = OpenRouterClient()
                client.embed_texts(["test text"])

                # Verify the endpoint was called
                mock_client.post.assert_called_once()
                call_args = mock_client.post.call_args
                url = call_args.args[0] if call_args.args else call_args.kwargs.get("url")
                assert "openrouter.ai" in url or "api.openrouter.ai" in url

    def test_fr_2_3_embed_texts_returns_correct_dimensions(self) -> None:
        """embed_texts returns embeddings with correct dimensions."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            expected_embedding = [0.1] * 1536  # text-embedding-3-small uses 1536 dims
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"embedding": expected_embedding}]
            }

            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = OpenRouterClient()
                result = client.embed_texts(["test"])

                assert len(result) == 1
                assert result[0].shape == (1536,)


class TestFr23ErrorHandling:
    """FR-2.3: Error handling tests."""

    def test_fr_2_3_embed_texts_handles_api_error(self) -> None:
        """embed_texts handles API error gracefully."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"

            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = OpenRouterClient()

                with pytest.raises(Exception):
                    client.embed_texts(["test"])

    def test_fr_2_3_embed_texts_handles_rate_limit(self) -> None:
        """embed_texts handles rate limit error."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"

            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = OpenRouterClient()

                with pytest.raises(Exception):
                    client.embed_texts(["test"])

    def test_fr_2_3_embed_texts_handles_invalid_json_response(self) -> None:
        """embed_texts handles invalid JSON response."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            from src.api.openrouter import OpenRouterClient

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")

            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = OpenRouterClient()

                with pytest.raises(Exception):
                    client.embed_texts(["test"])


class TestFr23Imports:
    """FR-2.3: Module import tests."""

    def test_fr_2_3_import_openrouter_client(self) -> None:
        """OpenRouterClient can be imported."""
        from src.api.openrouter import OpenRouterClient
        assert OpenRouterClient is not None

    def test_fr_2_3_import_constants(self) -> None:
        """Constants can be imported."""
        from src.api.openrouter import (
            SIMILARITY_THRESHOLD,
            DEFAULT_TOP_K,
            DEFAULT_MODEL
        )
        assert SIMILARITY_THRESHOLD is not None
        assert DEFAULT_TOP_K is not None
        assert DEFAULT_MODEL is not None
