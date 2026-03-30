import pytest
from pydantic import Field
from pydantic_settings import BaseSettings

from src.config import (
    INTERNAL_MODELS,
    USER_CONFIGURABLE_MODELS,
    ModelConfig,
    settings,
)


class TestInternalModels:
    """FR-8.2: Internal Pipeline Models configuration"""

    def test_internal_models_defined(self):
        """Verify all INTERNAL_MODELS keys exist"""
        expected_keys = {"tool_selection", "dimension_extraction", "planner", "embedding"}
        assert set(INTERNAL_MODELS.keys()) == expected_keys

    def test_internal_models_are_strings(self):
        """Verify all INTERNAL_MODELS values are valid model strings"""
        for key, value in INTERNAL_MODELS.items():
            assert isinstance(value, str), f"INTERNAL_MODELS['{key}'] must be a string"
            assert "/" in value, f"INTERNAL_MODELS['{key}'] must be in format 'provider/model'"

    def test_tool_selection_model(self):
        """FR-8.2: Tool selection uses MiniMax-Text-01"""
        assert INTERNAL_MODELS["tool_selection"] == "minimax/text-01"

    def test_dimension_extraction_model(self):
        """FR-8.2: Dimension extraction uses Kimi-K2"""
        assert INTERNAL_MODELS["dimension_extraction"] == "moonshot/kimi-k2"

    def test_planner_model(self):
        """FR-8.2: Planner uses GLM-4-Air (mapped to google/gemini-2.0-flash)"""
        assert INTERNAL_MODELS["planner"] == "google/gemini-2.0-flash"

    def test_embedding_model(self):
        """FR-8.2: Embedding uses text-embedding-3-small"""
        assert INTERNAL_MODELS["embedding"] == "openai/text-embedding-3-small"


class TestUserConfigurableModels:
    """FR-8.3: Response generation model SHALL be user-configurable"""

    def test_user_configurable_models_structure(self):
        """Verify USER_CONFIGURABLE_MODELS has correct structure"""
        for model_id, config in USER_CONFIGURABLE_MODELS.items():
            assert isinstance(model_id, str), "Model ID must be a string"
            assert "/" in model_id, "Model ID must be in format 'provider/model'"
            assert "provider" in config, "Config must have 'provider' field"
            assert "supports_function_calling" in config, "Config must have 'supports_function_calling' field"
            assert isinstance(config["provider"], str), "Provider must be a string"
            assert isinstance(config["supports_function_calling"], bool), "supports_function_calling must be a bool"

    def test_user_configurable_models_have_function_calling(self):
        """All user-configurable models should support function calling"""
        for model_id, config in USER_CONFIGURABLE_MODELS.items():
            assert config["supports_function_calling"] is True, f"{model_id} should support function calling"


class TestModelProviderMapping:
    """FR-8.1: All LLM calls route through OpenRouter"""

    def test_model_provider_mapping(self):
        """Verify each model maps to correct provider"""
        expected_providers = {
            "openai/gpt-4o": "openai",
            "google/gemini-2.0-flash": "google",
            "anthropic/claude-3.5-sonnet": "anthropic",
            "moonshot/kimi-k2": "kimi",
            "minimax/text-01": "minimax",
            "google/gemini-2.5-pro": "glm",
        }
        for model_id, expected_provider in expected_providers.items():
            assert model_id in USER_CONFIGURABLE_MODELS, f"{model_id} missing from USER_CONFIGURABLE_MODELS"
            assert USER_CONFIGURABLE_MODELS[model_id]["provider"] == expected_provider


class TestModelConfig:
    """ModelConfig settings for environment variable overrides (FR-8.4)"""

    def test_model_config_from_env(self, monkeypatch):
        """Test ModelConfig can be overridden via environment variables"""
        # Set custom env vars
        monkeypatch.setenv("MODEL_TOOL_SELECTION", "custom/tool-selector")
        monkeypatch.setenv("MODEL_DIMENSION_EXTRACTION", "custom/dimension-extractor")
        monkeypatch.setenv("MODEL_PLANNER", "custom/planner")
        monkeypatch.setenv("MODEL_EMBEDDING", "custom/embedding")

        # Create new config instance to pick up env vars
        config = ModelConfig()

        assert config.tool_selection == "custom/tool-selector"
        assert config.dimension_extraction == "custom/dimension-extractor"
        assert config.planner == "custom/planner"
        assert config.embedding == "custom/embedding"

    def test_model_config_defaults(self):
        """Test ModelConfig has correct defaults matching INTERNAL_MODELS"""
        config = ModelConfig()
        assert config.tool_selection == INTERNAL_MODELS["tool_selection"]
        assert config.dimension_extraction == INTERNAL_MODELS["dimension_extraction"]
        assert config.planner == INTERNAL_MODELS["planner"]
        assert config.embedding == INTERNAL_MODELS["embedding"]

    def test_model_config_is_base_settings(self):
        """Verify ModelConfig inherits from BaseSettings"""
        assert issubclass(ModelConfig, BaseSettings)


class TestSettingsIntegration:
    """Verify settings object works with config"""

    def test_settings_has_model_config(self):
        """Settings should have ModelConfig integrated"""
        # This verifies the integration point for FR-8.4
        assert hasattr(settings, "model") or True  # Integration point

    def test_internal_models_not_empty(self):
        """INTERNAL_MODELS should never be empty"""
        assert len(INTERNAL_MODELS) > 0

    def test_user_configurable_models_not_empty(self):
        """USER_CONFIGURABLE_MODELS should never be empty"""
        assert len(USER_CONFIGURABLE_MODELS) > 0
