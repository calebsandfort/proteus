"""Tests for OpenRouter client implementation.

FR-8.1: All LLM calls SHALL route through OpenRouter
FR-8.5: Provider Normalization - parse failures trigger retry once with same model
FR-8.6: LLM Failure Handling - exponential backoff with jitter (max 3 retries)
"""
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.api.normalizers import NormalizerRegistry
from src.api.openrouter import OpenRouterClient, UserFriendlyError


class TestOpenRouterClientConstants:
    """Test class for OpenRouterClient class constants."""

    def test_openrouter_client_has_max_retries(self) -> None:
        """MAX_RETRIES equals 3."""
        assert OpenRouterClient.MAX_RETRIES == 3

    def test_openrouter_client_has_retry_delay_base(self) -> None:
        """RETRY_DELAY_BASE equals 1.0."""
        assert OpenRouterClient.RETRY_DELAY_BASE == 1.0


class TestOpenRouterClientInitialization:
    """Test class for OpenRouterClient initialization."""

    def test_openrouter_client_initialization(self) -> None:
        """Client initializes with default values."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            client = OpenRouterClient()
            assert client.api_key == "test-key"

    def test_openrouter_client_requires_api_key(self) -> None:
        """Should raise if no API key provided."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                OpenRouterClient()


class TestOpenRouterClientGetProvider:
    """Test class for _get_provider method."""

    def test_get_provider_extracts_provider_from_model(self) -> None:
        """_get_provider('openai/gpt-4o') returns 'openai'."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            client = OpenRouterClient()
            assert client._get_provider("openai/gpt-4o") == "openai"

    def test_get_provider_handles_google_model(self) -> None:
        """_get_provider('google/gemini-2.0-flash') returns 'google'."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            client = OpenRouterClient()
            assert client._get_provider("google/gemini-2.0-flash") == "google"

    def test_get_provider_handles_anthropic_model(self) -> None:
        """_get_provider('anthropic/claude-3.5-sonnet') returns 'anthropic'."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            client = OpenRouterClient()
            assert client._get_provider("anthropic/claude-3.5-sonnet") == "anthropic"


class TestOpenRouterClientEmbedTexts:
    """Test class for embed_texts method."""

    @pytest.mark.asyncio
    async def test_embed_texts_returns_list(self) -> None:
        """embed_texts returns a list (mocked)."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            client = OpenRouterClient()

            # Mock httpx client
            mock_response = MagicMock()
            mock_response.status_code = 200
            # httpx Response.json() is synchronous - set return_value directly
            mock_response.json.return_value = {
                "data": [
                    {"embedding": [0.1, 0.2, 0.3]},
                    {"embedding": [0.4, 0.5, 0.6]},
                ]
            }

            # httpx.AsyncClient() as context manager needs to return mock client
            mock_client = MagicMock()
            # post is async so must be AsyncMock to support await
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await client.embed_texts(["hello", "world"])

                assert isinstance(result, list)
                assert len(result) == 2


class TestOpenRouterClientCallWithRetry:
    """Test class for call_with_retry method."""

    @pytest.mark.asyncio
    async def test_call_with_retry_uses_normalizer(self) -> None:
        """Uses NormalizerRegistry.get_normalizer."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            client = OpenRouterClient()

            # Mock the normalizer
            mock_normalizer = MagicMock()
            mock_normalizer.parse_function_calls.return_value = [
                {"name": "test_function", "arguments": {"arg1": "value1"}}
            ]

            # Mock the response
            mock_response = MagicMock()

            with patch.object(
                client, "_make_request", new_callable=AsyncMock
            ) as mock_make_request:
                # Use lambda to return mock_response without recursion
                mock_make_request.side_effect = lambda *args, **kwargs: mock_response

                with patch(
                    "src.api.openrouter.NormalizerRegistry.get_normalizer",
                    return_value=mock_normalizer
                ):
                    result = await client.call_with_retry(
                        model="openai/gpt-4o",
                        messages=[{"role": "user", "content": "Hello"}]
                    )

                    # Verify normalizer was used
                    NormalizerRegistry.get_normalizer.assert_called_once_with("openai")
                    assert result == [{"name": "test_function", "arguments": {"arg1": "value1"}}]

    @pytest.mark.asyncio
    async def test_call_with_retry_retries_on_parse_failure(self) -> None:
        """Retries once on JSON parse failure with same model (FR-8.5)."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            client = OpenRouterClient()

            # Mock the normalizer to raise JSONDecodeError on first call
            mock_normalizer = MagicMock()
            mock_normalizer.parse_function_calls.side_effect = [
                json.JSONDecodeError("Expecting value", "", 0),
                {"name": "test_function", "arguments": {"arg1": "value1"}}
            ]

            # Mock the response
            mock_response = MagicMock()

            with patch.object(
                client, "_make_request", new_callable=AsyncMock
            ) as mock_make_request:
                mock_make_request.side_effect = lambda *args, **kwargs: mock_response

                with patch(
                    "src.api.openrouter.NormalizerRegistry.get_normalizer",
                    return_value=mock_normalizer
                ):
                    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                        result = await client.call_with_retry(
                            model="openai/gpt-4o",
                            messages=[{"role": "user", "content": "Hello"}]
                        )

                        # Should have made 2 requests (initial + 1 retry)
                        assert mock_make_request.call_count == 2
                        # Should have slept once for backoff
                        assert mock_sleep.call_count == 1

    @pytest.mark.asyncio
    async def test_call_with_retry_raises_after_max_retries(self) -> None:
        """Raises UserFriendlyError after exhausting retries (FR-8.6)."""
        with patch("src.api.openrouter.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            client = OpenRouterClient()

            # Mock the normalizer to always raise JSONDecodeError
            mock_normalizer = MagicMock()
            mock_normalizer.parse_function_calls.side_effect = json.JSONDecodeError(
                "Expecting value", "", 0
            )

            mock_response = MagicMock()

            with patch.object(
                client, "_make_request", new_callable=AsyncMock
            ) as mock_make_request:
                mock_make_request.return_value = mock_response

                with patch(
                    "src.api.openrouter.NormalizerRegistry.get_normalizer",
                    return_value=mock_normalizer
                ):
                    with patch("src.api.openrouter.uuid.uuid4") as mock_uuid:
                        mock_uuid.return_value = uuid.UUID("12345678-1234-1234-1234-123456789abc")
                        with pytest.raises(UserFriendlyError) as exc_info:
                            await client.call_with_retry(
                                model="openai/gpt-4o",
                                messages=[{"role": "user", "content": "Hello"}]
                            )

                        error = exc_info.value
                        assert error.code == "PARSE_FAILURE"
                        # request_id appears in str(error) via super().__init__
                        assert "12345678" in str(error)
                        assert error.request_id == "12345678"


class TestUserFriendlyError:
    """Test class for UserFriendlyError exception."""

    def test_user_friendly_error_attributes(self) -> None:
        """Error has code, message, and request_id attributes."""
        error = UserFriendlyError(
            code="PARSE_FAILURE",
            message="Unable to process model response",
            request_id="req-123"
        )
        assert error.code == "PARSE_FAILURE"
        assert error.message == "Unable to process model response"
        assert error.request_id == "req-123"

    def test_user_friendly_error_is_exception(self) -> None:
        """UserFriendlyError is an Exception subclass."""
        error = UserFriendlyError(
            code="TEST",
            message="Test error",
            request_id="test"
        )
        assert isinstance(error, Exception)
