"""Provider response normalizers for model-agnostic pipeline.

This module provides a unified interface for parsing structured outputs
across different LLM providers (OpenAI, Anthropic, Google, Kimi, MiniMax, GLM).

FR-8.4: Model-Agnostic Pipeline - provider-agnostic normalization layer
FR-8.5: Provider Normalization - normalize structured output across providers
"""
from abc import ABC, abstractmethod
import json
from typing import Any, Dict, List


class ProviderResponseNormalizer(ABC):
    """Abstract base class for provider response normalizers.

    All provider normalizers must implement methods for parsing
    function calls and JSON mode responses.
    """

    @abstractmethod
    def parse_function_calls(self, raw_response: Any) -> List[Dict[str, Any]]:
        """Extract function calls from provider-specific response format.

        Args:
            raw_response: Provider-specific raw response object.

        Returns:
            List of dictionaries containing function call name and arguments.
        """
        pass

    @abstractmethod
    def normalize_json_mode(self, raw_response: str) -> Dict[str, Any]:
        """Normalize JSON mode response to consistent format.

        Args:
            raw_response: Raw JSON string from provider.

        Returns:
            Dictionary containing the parsed and normalized response.
        """
        pass


class OpenAINormalizer(ProviderResponseNormalizer):
    """Normalizer for OpenAI-compatible API responses.

    OpenAI uses tool_calls in the message object with function name
    and JSON arguments string.
    """

    def parse_function_calls(self, raw_response: Any) -> List[Dict[str, Any]]:
        """Parse OpenAI tool_calls format.

        Args:
            raw_response: OpenAI response with choices[0].message.tool_calls.

        Returns:
            List of dicts with 'name' and 'arguments' keys.
        """
        tool_calls = raw_response.choices[0].message.tool_calls or []
        result = []
        for tc in tool_calls:
            # Arguments are stored as JSON string
            arguments = json.loads(tc.function.arguments)
            result.append({
                "name": tc.function.name,
                "arguments": arguments
            })
        return result

    def normalize_json_mode(self, raw_response: str) -> Dict[str, Any]:
        """Parse OpenAI JSON mode response.

        Args:
            raw_response: JSON string from OpenAI.

        Returns:
            Parsed dictionary.
        """
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")


class AnthropicNormalizer(ProviderResponseNormalizer):
    """Normalizer for Anthropic API responses.

    Anthropic uses tool_use content blocks with name and input.
    """

    def parse_function_calls(self, raw_response: Any) -> List[Dict[str, Any]]:
        """Parse Anthropic tool_use format.

        Args:
            raw_response: Anthropic response with content blocks.

        Returns:
            List of dicts with 'name' and 'input' keys.
        """
        result = []
        for content in raw_response.content:
            if content.type == "tool_use":
                result.append({
                    "name": content.name,
                    "input": content.input
                })
        return result

    def normalize_json_mode(self, raw_response: str) -> Dict[str, Any]:
        """Parse Anthropic JSON mode response.

        Args:
            raw_response: JSON string from Anthropic.

        Returns:
            Parsed dictionary.
        """
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")


class GoogleNormalizer(ProviderResponseNormalizer):
    """Normalizer for Google AI API responses.

    Google uses function_calls in candidates with name and args.
    """

    def parse_function_calls(self, raw_response: Any) -> List[Dict[str, Any]]:
        """Parse Google function_call format.

        Args:
            raw_response: Google response with candidates[0].function_calls.

        Returns:
            List of dicts with 'name' and 'arguments' keys.
        """
        candidate = raw_response.candidates[0]
        if hasattr(candidate, 'function_calls') and candidate.function_calls:
            return [
                {"name": fc.name, "arguments": fc.args}
                for fc in candidate.function_calls
            ]
        return []

    def normalize_json_mode(self, raw_response: str) -> Dict[str, Any]:
        """Parse Google JSON mode response.

        Args:
            raw_response: JSON string from Google.

        Returns:
            Parsed dictionary.
        """
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")


class KimiNormalizer(OpenAINormalizer):
    """Normalizer for Kimi API responses.

    Kimi is compatible with OpenAI format.
    """
    pass


class MiniMaxNormalizer(OpenAINormalizer):
    """Normalizer for MiniMax API responses.

    MiniMax is compatible with OpenAI format.
    """
    pass


class GLMNormalizer(GoogleNormalizer):
    """Normalizer for GLM API responses.

    GLM is compatible with Google format.
    """
    pass


class NormalizerRegistry:
    """Registry for provider response normalizers.

    Provides access to the appropriate normalizer for each provider.
    """

    _normalizers: Dict[str, ProviderResponseNormalizer] = {
        "openai": OpenAINormalizer(),
        "anthropic": AnthropicNormalizer(),
        "google": GoogleNormalizer(),
        "kimi": OpenAINormalizer(),  # Compatible with OpenAI format
        "minimax": OpenAINormalizer(),
        "glm": GoogleNormalizer(),  # Compatible with Google format
    }

    @classmethod
    def get_normalizer(cls, provider: str) -> ProviderResponseNormalizer:
        """Get the normalizer for a given provider.

        Args:
            provider: Provider name (case-insensitive).

        Returns:
            ProviderResponseNormalizer instance for the provider.
            Defaults to OpenAINormalizer if provider is unknown.
        """
        return cls._normalizers.get(provider.lower(), OpenAINormalizer())
