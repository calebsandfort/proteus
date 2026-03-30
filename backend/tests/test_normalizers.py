"""Tests for provider response normalizers."""
import pytest

from src.api.normalizers import (
    NormalizerRegistry,
    OpenAINormalizer,
    AnthropicNormalizer,
    GoogleNormalizer,
)


class TestNormalizerRegistry:
    """Tests for NormalizerRegistry class."""

    def test_normalizer_registry_returns_openai_for_openai(self) -> None:
        """get_normalizer('openai') returns OpenAINormalizer."""
        normalizer = NormalizerRegistry.get_normalizer("openai")
        assert isinstance(normalizer, OpenAINormalizer)

    def test_normalizer_registry_returns_anthropic_for_anthropic(self) -> None:
        """get_normalizer('anthropic') returns AnthropicNormalizer."""
        normalizer = NormalizerRegistry.get_normalizer("anthropic")
        assert isinstance(normalizer, AnthropicNormalizer)

    def test_normalizer_registry_returns_google_for_google(self) -> None:
        """get_normalizer('google') returns GoogleNormalizer."""
        normalizer = NormalizerRegistry.get_normalizer("google")
        assert isinstance(normalizer, GoogleNormalizer)

    def test_normalizer_registry_returns_kimi_as_openai(self) -> None:
        """get_normalizer('kimi') returns OpenAINormalizer (compatible with OpenAI format)."""
        normalizer = NormalizerRegistry.get_normalizer("kimi")
        assert isinstance(normalizer, OpenAINormalizer)

    def test_normalizer_registry_returns_minimax_as_openai(self) -> None:
        """get_normalizer('minimax') returns OpenAINormalizer (compatible with OpenAI format)."""
        normalizer = NormalizerRegistry.get_normalizer("minimax")
        assert isinstance(normalizer, OpenAINormalizer)

    def test_normalizer_registry_returns_glm_as_google(self) -> None:
        """get_normalizer('glm') returns GoogleNormalizer (compatible with Google format)."""
        normalizer = NormalizerRegistry.get_normalizer("glm")
        assert isinstance(normalizer, GoogleNormalizer)

    def test_normalizer_registry_case_insensitive(self) -> None:
        """get_normalizer('OpenAI') works (case insensitive)."""
        normalizer = NormalizerRegistry.get_normalizer("OpenAI")
        assert isinstance(normalizer, OpenAINormalizer)

    def test_normalizer_registry_unknown_provider_defaults_to_openai(self) -> None:
        """Unknown provider returns OpenAINormalizer as default."""
        normalizer = NormalizerRegistry.get_normalizer("unknown_provider")
        assert isinstance(normalizer, OpenAINormalizer)


class TestOpenAINormalizer:
    """Tests for OpenAINormalizer class."""

    def test_parse_function_calls_empty(self) -> None:
        """Returns empty list when no tool calls."""
        # Mock raw response with no tool_calls
        class MockMessage:
            tool_calls = None

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]

        normalizer = OpenAINormalizer()
        result = normalizer.parse_function_calls(MockResponse())
        assert result == []


class TestGoogleNormalizer:
    """Tests for GoogleNormalizer class."""

    def test_parse_function_calls_empty(self) -> None:
        """Returns empty list when no function calls."""
        # Mock raw response with no function_calls
        class MockCandidate:
            function_calls = None

        class MockResponse:
            candidates = [MockCandidate()]

        normalizer = GoogleNormalizer()
        result = normalizer.parse_function_calls(MockResponse())
        assert result == []
