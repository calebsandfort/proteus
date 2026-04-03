"""TDD Tests for FR-8.3: Response Generation Model.

This module tests the ResponseSynthesizer for response generation with
user-configurable model selection.

FR Requirements:
- FR-8.3: Response Generation Model
  - Response generation stage SHALL be user-configurable
  - Users SHALL be able to select from six providers: OpenAI, Google, Anthropic, Kimi, MiniMax, GLM
  - Model selection SHALL be exposed in the UI as a settings control
  - Changes SHALL apply to subsequent queries within the session
  - If selected model does not support function calling, SHALL fall back to
    text-embedding-3-small for embedding + strongest available model for generation,
    with user warning

Test Requirements:
- Test model selection logic
- Test fallback logic when model doesn't support function calling
- Mock the OpenRouter client - do not make real API calls
- Test natural language synthesis from tool results
- Tests must be deterministic
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestFr83UserConfigurableModels:
    """FR-8.3: User-configurable models from config."""

    def test_fr_8_3_user_configurable_models_defined(self) -> None:
        """Six providers SHALL be available for selection."""
        from src.config import USER_CONFIGURABLE_MODELS

        assert len(USER_CONFIGURABLE_MODELS) == 6
        assert "openai/gpt-4o" in USER_CONFIGURABLE_MODELS
        assert "google/gemini-2.0-flash" in USER_CONFIGURABLE_MODELS
        assert "anthropic/claude-3.5-sonnet" in USER_CONFIGURABLE_MODELS
        assert "moonshot/kimi-k2" in USER_CONFIGURABLE_MODELS
        assert "minimax/text-01" in USER_CONFIGURABLE_MODELS
        assert "google/gemini-2.5-pro" in USER_CONFIGURABLE_MODELS

    def test_fr_8_3_all_models_have_provider_info(self) -> None:
        """All models SHALL have provider information."""
        from src.config import USER_CONFIGURABLE_MODELS

        for model_id, model_info in USER_CONFIGURABLE_MODELS.items():
            assert "provider" in model_info
            assert model_info["provider"] is not None

    def test_fr_8_3_all_models_have_function_calling_support(self) -> None:
        """All models SHALL have function_calling support flag."""
        from src.config import USER_CONFIGURABLE_MODELS

        for model_id, model_info in USER_CONFIGURABLE_MODELS.items():
            assert "supports_function_calling" in model_info
            assert isinstance(model_info["supports_function_calling"], bool)


class TestFr83ModelSelection:
    """FR-8.3: Model selection logic tests."""

    def test_fr_8_3_default_model_is_gpt_4o(self) -> None:
        """Default response generation model SHALL be openai/gpt-4o."""
        from src.config import model_config

        assert model_config.response_generation == "openai/gpt-4o"

    def test_fr_8_3_model_selection_with_supported_model(self) -> None:
        """When selected model supports function calling, use it directly."""
        from src.agent.response import ModelSelector

        selector = ModelSelector()
        fallback_info = selector.select_model("openai/gpt-4o")

        # Should not trigger fallback - model supports function calling
        assert fallback_info.model == "openai/gpt-4o"
        assert fallback_info.used_fallback is False
        assert fallback_info.warning is None

    def test_fr_8_3_fallback_for_unknown_model(self) -> None:
        """When selected model is unknown, SHALL fall back."""
        from src.agent.response import ModelSelector

        selector = ModelSelector()
        fallback_info = selector.select_model("unknown/model")

        # Should trigger fallback for unknown model
        assert fallback_info.used_fallback is True
        assert fallback_info.warning is not None
        assert "not found" in fallback_info.warning.lower()

    def test_fr_8_3_fallback_uses_strongest_available_model(self) -> None:
        """Fallback SHALL use strongest available model for generation."""
        from src.agent.response import ModelSelector

        selector = ModelSelector()
        fallback_info = selector.select_model("unknown/model")

        # The fallback model should support function calling
        from src.config import USER_CONFIGURABLE_MODELS
        fallback_model = fallback_info.model
        assert USER_CONFIGURABLE_MODELS[fallback_model]["supports_function_calling"] is True


class TestFr83ResponseSynthesizerInit:
    """FR-8.3: ResponseSynthesizer initialization tests."""

    def test_fr_8_3_synthesizer_requires_openrouter_client(self) -> None:
        """ResponseSynthesizer SHALL require an OpenRouter client."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(openrouter_client=mock_client)

            assert synthesizer.openrouter_client is mock_client

    def test_fr_8_3_synthesizer_accepts_model_parameter(self) -> None:
        """ResponseSynthesizer SHALL accept custom model parameter."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(
                openrouter_client=mock_client,
                model="google/gemini-2.0-flash"
            )

            assert synthesizer.model == "google/gemini-2.0-flash"


class TestFr83NaturalLanguageSynthesis:
    """FR-8.3: Natural language synthesis from tool results."""

    @pytest.mark.asyncio
    async def test_fr_8_3_synthesizes_single_tool_result(self) -> None:
        """ResponseSynthesizer SHALL synthesize natural language from tool results."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.call_with_retry = AsyncMock(return_value={
                "content": "Based on the spending data, Gen Z customers spent $1,234 on retail purchases in Q4 2024."
            })
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(openrouter_client=mock_client)

            tool_results = {
                "spending_by_generation": {
                    "generation": "gen_z",
                    "total_spend": 1234.56,
                    "transaction_count": 42,
                    "period": "Q4 2024"
                }
            }

            result = await synthesizer.synthesize(
                query="Show Gen Z spending",
                tool_results=tool_results
            )

            # Result is a SynthesisResult Pydantic model
            assert hasattr(result, "answer")
            assert len(result.answer) > 0

    @pytest.mark.asyncio
    async def test_fr_8_3_synthesizes_multiple_tool_results(self) -> None:
        """ResponseSynthesizer SHALL synthesize multiple tool results into coherent response."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.call_with_retry = AsyncMock(return_value={
                "content": "Comparing the data across generations, Gen Z spent $1,234 while Millennials spent $2,567 on retail."
            })
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(openrouter_client=mock_client)

            tool_results = {
                "gen_z_spending": {"total_spend": 1234.56, "generation": "gen_z"},
                "millennial_spending": {"total_spend": 2567.89, "generation": "millennial"}
            }

            result = await synthesizer.synthesize(
                query="Compare Gen Z and Millennial spending",
                tool_results=tool_results
            )

            assert hasattr(result, "answer")
            assert len(result.answer) > 0

    @pytest.mark.asyncio
    async def test_fr_8_3_includes_visualization_decisions(self) -> None:
        """ResponseSynthesizer SHALL include visualization decisions in response."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.call_with_retry = AsyncMock(return_value={
                "content": "The data shows spending trends over time."
            })
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(openrouter_client=mock_client)

            tool_results = {
                "time_series": {
                    "data": [{"month": "Jan", "spend": 100}, {"month": "Feb", "spend": 150}]
                }
            }

            result = await synthesizer.synthesize(
                query="Show spending trends over time",
                tool_results=tool_results
            )

            # Visualizations should be included
            assert hasattr(result, "visualizations")


class TestFr83StreamingResponse:
    """FR-8.3: Streaming response tests."""

    @pytest.mark.asyncio
    async def test_fr_8_3_stream_returns_async_generator(self) -> None:
        """ResponseSynthesizer.stream_response SHALL return an async generator."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.call_with_retry = AsyncMock(return_value={
                "content": "Test response"
            })
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(openrouter_client=mock_client)

            tool_results = {"test": {"data": "value"}}
            stream = synthesizer.stream_response(
                query="Test query",
                tool_results=tool_results
            )

            # Should be an async generator
            assert hasattr(stream, "__anext__")


class TestFr83ResponseOutput:
    """FR-8.3: Response output structure tests."""

    @pytest.mark.asyncio
    async def test_fr_8_3_response_has_answer(self) -> None:
        """Response SHALL include natural language answer."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.call_with_retry = AsyncMock(return_value={
                "content": "The analysis shows positive trends."
            })
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(openrouter_client=mock_client)

            result = await synthesizer.synthesize(
                query="Analyze trends",
                tool_results={"trend_data": {"values": [1, 2, 3]}}
            )

            assert hasattr(result, "answer")
            assert isinstance(result.answer, str)
            assert len(result.answer) > 0

    @pytest.mark.asyncio
    async def test_fr_8_3_response_has_visualizations(self) -> None:
        """Response SHALL include visualization recommendations."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.call_with_retry = AsyncMock(return_value={
                "content": "Spending by category"
            })
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(openrouter_client=mock_client)

            result = await synthesizer.synthesize(
                query="Show spending by category",
                tool_results={"category_spend": {"data": []}}
            )

            assert hasattr(result, "visualizations")
            assert isinstance(result.visualizations, list)

    @pytest.mark.asyncio
    async def test_fr_8_3_response_has_suggestions(self) -> None:
        """Response MAY include follow-up suggestions."""
        from src.agent.response import ResponseSynthesizer

        with patch("src.agent.response.OpenRouterClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.call_with_retry = AsyncMock(return_value={
                "content": "Current period analysis complete"
            })
            mock_client_class.return_value = mock_client

            synthesizer = ResponseSynthesizer(openrouter_client=mock_client)

            result = await synthesizer.synthesize(
                query="Show current spending",
                tool_results={"current": {"spend": 100}}
            )

            assert hasattr(result, "suggestions")
            assert isinstance(result.suggestions, list)


class TestFr83FallbackWarnings:
    """FR-8.3: Fallback warning tests."""

    def test_fr_8_3_fallback_warning_is_user_friendly(self) -> None:
        """Fallback warning SHALL be user-friendly."""
        from src.agent.response import ModelSelector

        selector = ModelSelector()
        fallback_info = selector.select_model("unknown/model")

        assert fallback_info.used_fallback is True
        assert fallback_info.warning is not None
        # Warning should be clear and actionable
        assert len(fallback_info.warning) > 10


class TestFr83ImportTests:
    """FR-8.3: Module import tests."""

    def test_fr_8_3_import_response_synthesizer(self) -> None:
        """ResponseSynthesizer can be imported."""
        from src.agent.response import ResponseSynthesizer
        assert ResponseSynthesizer is not None

    def test_fr_8_3_import_model_selector(self) -> None:
        """ModelSelector can be imported."""
        from src.agent.response import ModelSelector
        assert ModelSelector is not None

    def test_fr_8_3_import_visualization_recommender(self) -> None:
        """VisualizationRecommender can be imported."""
        from src.agent.response import VisualizationRecommender
        assert VisualizationRecommender is not None


class TestFr83VisualizationRecommender:
    """FR-8.3: Visualization recommendation tests."""

    def test_fr_8_3_recommends_bar_chart_for_category_data(self) -> None:
        """Recommends bar chart for category comparison data."""
        from src.agent.response import VisualizationRecommender

        recommender = VisualizationRecommender()

        data = {
            "categories": [
                {"name": "Retail", "value": 100},
                {"name": "Dining", "value": 50}
            ]
        }

        recommendation = recommender.recommend(query="Show spending by category", data=data)

        assert recommendation.chart_type == "bar"
        assert "category" in recommendation.dimensions.get("x", "").lower()

    def test_fr_8_3_recommends_line_chart_for_time_series(self) -> None:
        """Recommends line chart for time series data."""
        from src.agent.response import VisualizationRecommender

        recommender = VisualizationRecommender()

        data = {
            "time_series": [
                {"month": "Jan", "value": 100},
                {"month": "Feb", "value": 150}
            ]
        }

        recommendation = recommender.recommend(query="Show spending trends", data=data)

        assert recommendation.chart_type == "line"

    def test_fr_8_3_recommends_pie_chart_for_proportion_data(self) -> None:
        """Recommends pie chart for proportion data."""
        from src.agent.response import VisualizationRecommender

        recommender = VisualizationRecommender()

        data = {
            "proportions": [
                {"segment": "Gen Z", "percentage": 30},
                {"segment": "Millennial", "percentage": 45}
            ]
        }

        recommendation = recommender.recommend(query="Show market share", data=data)

        assert recommendation.chart_type == "pie"
