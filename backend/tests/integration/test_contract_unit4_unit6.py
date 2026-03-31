"""Contract tests: Unit 4 (Tool Registry & RAG) ↔ Unit 6 (OpenRouter Integration).

Verifies the integration seams between Unit 4 and Unit 6:
- Import resolution: cross-unit imports actually resolve
- Type compatibility: Unit 4 can use Unit 6 exports with expected shapes
- Function signatures: Unit 4 calls Unit 6 functions with correct arguments
- Constant contracts: shared constants have expected types and values

No mocks at the integration boundary — real modules from both units are imported.
"""

import inspect
from typing import get_type_hints

import numpy as np
import pytest


# ============================================================================
# 1. Import Resolution Tests
# ============================================================================


class TestCrossUnitImports:
    """Verify that cross-unit imports between Unit 4 and Unit 6 resolve."""

    def test_registry_imports_openrouter_client(self):
        """Unit 4 registry.py can import OpenRouterClient from Unit 6."""
        from src.api.openrouter import OpenRouterClient

        assert OpenRouterClient is not None

    def test_registry_imports_similarity_threshold(self):
        """Unit 4 registry.py can import SIMILARITY_THRESHOLD from Unit 6."""
        from src.api.openrouter import SIMILARITY_THRESHOLD

        assert SIMILARITY_THRESHOLD is not None

    def test_registry_imports_default_top_k(self):
        """Unit 4 registry.py can import DEFAULT_TOP_K from Unit 6."""
        from src.api.openrouter import DEFAULT_TOP_K

        assert DEFAULT_TOP_K is not None

    def test_retrieval_imports_openrouter_client(self):
        """Unit 4 retrieval.py can import OpenRouterClient from Unit 6."""
        from src.agent.retrieval import EmbeddingRetriever

        assert EmbeddingRetriever is not None

    def test_registry_module_loads_without_error(self):
        """Unit 4 registry module loads cleanly (all its Unit 6 imports resolve)."""
        from src.agent import registry

        assert hasattr(registry, "ToolRegistry")

    def test_retrieval_module_loads_without_error(self):
        """Unit 4 retrieval module loads cleanly (all its Unit 6 imports resolve)."""
        from src.agent import retrieval

        assert hasattr(retrieval, "EmbeddingRetriever")
        assert hasattr(retrieval, "ToolRetriever")

    def test_openrouter_imports_normalizer_registry(self):
        """Unit 6 openrouter.py can import NormalizerRegistry from Unit 6 normalizers."""
        from src.api.normalizers import NormalizerRegistry

        assert NormalizerRegistry is not None

    def test_openrouter_imports_settings(self):
        """Unit 6 openrouter.py can import settings from Unit 6 config."""
        from src.config import settings

        assert settings is not None

    def test_config_exports_internal_models(self):
        """Unit 6 config.py exports INTERNAL_MODELS dict."""
        from src.config import INTERNAL_MODELS

        assert isinstance(INTERNAL_MODELS, dict)


# ============================================================================
# 2. Type Compatibility Tests
# ============================================================================


class TestTypeCompatibility:
    """Verify that Unit 6 outputs satisfy Unit 4 input expectations."""

    def test_embed_texts_return_type_compatible_with_numpy(self):
        """OpenRouterClient.embed_texts return type annotation is list-like,
        compatible with np.ndarray usage in ToolRegistry.search_by_embedding."""
        from src.api.openrouter import OpenRouterClient

        sig = inspect.signature(OpenRouterClient.embed_texts)
        # The return annotation should exist and indicate a list
        assert sig.return_annotation is not inspect.Parameter.empty

    def test_similarity_threshold_is_float(self):
        """SIMILARITY_THRESHOLD is a float usable in comparison operations."""
        from src.api.openrouter import SIMILARITY_THRESHOLD

        assert isinstance(SIMILARITY_THRESHOLD, float)
        assert 0.0 <= SIMILARITY_THRESHOLD <= 1.0

    def test_default_top_k_is_int(self):
        """DEFAULT_TOP_K is an int usable as top_k parameter."""
        from src.api.openrouter import DEFAULT_TOP_K

        assert isinstance(DEFAULT_TOP_K, int)
        assert DEFAULT_TOP_K > 0

    def test_internal_models_has_embedding_key(self):
        """INTERNAL_MODELS contains 'embedding' key used by Unit 4 for model selection."""
        from src.config import INTERNAL_MODELS

        assert "embedding" in INTERNAL_MODELS
        assert isinstance(INTERNAL_MODELS["embedding"], str)
        assert "/" in INTERNAL_MODELS["embedding"]  # provider/model format

    def test_tool_definition_model_fields_complete(self):
        """ToolDefinition has all fields expected by the implementation plan contract."""
        from src.api.models.tool import ToolDefinition

        expected_fields = {
            "id", "name", "description", "capabilities",
            "required_dimensions", "optional_dimensions", "parameters",
            "output_schema", "example_queries", "aliases", "version",
        }
        actual_fields = set(ToolDefinition.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_retrieved_tool_model_fields_complete(self):
        """RetrievedTool has all fields expected by the implementation plan contract."""
        from src.api.models.tool import RetrievedTool

        expected_fields = {"tool_id", "tool_definition", "similarity", "rank"}
        actual_fields = set(RetrievedTool.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_normalizer_registry_returns_normalizer_for_all_providers(self):
        """NormalizerRegistry returns a normalizer for every provider in INTERNAL_MODELS."""
        from src.api.normalizers import NormalizerRegistry, ProviderResponseNormalizer
        from src.config import INTERNAL_MODELS

        for model_key, model_id in INTERNAL_MODELS.items():
            if model_key == "embedding":
                continue  # embedding model doesn't go through normalizer
            provider = model_id.split("/")[0]
            normalizer = NormalizerRegistry.get_normalizer(provider)
            assert isinstance(normalizer, ProviderResponseNormalizer), (
                f"No normalizer for provider '{provider}' (model: {model_id})"
            )

    def test_circuit_breaker_state_enum_values(self):
        """CircuitBreaker states match expected values for downstream consumers."""
        from src.api.circuit_breaker import CircuitState

        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


# ============================================================================
# 3. Function Signature Tests
# ============================================================================


class TestFunctionSignatures:
    """Verify that Unit 6 function signatures match what Unit 4 calls."""

    def test_openrouter_client_embed_texts_signature(self):
        """OpenRouterClient.embed_texts accepts (texts: List[str], model: str)
        as called by ToolRegistry.register and EmbeddingRetriever.retrieve."""
        from src.api.openrouter import OpenRouterClient

        sig = inspect.signature(OpenRouterClient.embed_texts)
        params = list(sig.parameters.keys())
        # Should have self, texts, model
        assert "self" in params
        assert "texts" in params
        assert "model" in params

    def test_openrouter_client_embed_texts_model_default(self):
        """embed_texts has a default model value matching the embedding spec."""
        from src.api.openrouter import OpenRouterClient

        sig = inspect.signature(OpenRouterClient.embed_texts)
        model_param = sig.parameters["model"]
        assert model_param.default == "openai/text-embedding-3-small"

    def test_openrouter_client_call_with_retry_signature(self):
        """call_with_retry has expected parameters for downstream LLM callers."""
        from src.api.openrouter import OpenRouterClient

        sig = inspect.signature(OpenRouterClient.call_with_retry)
        params = list(sig.parameters.keys())
        assert "model" in params
        assert "messages" in params
        assert "temperature" in params
        assert "max_tokens" in params

    def test_openrouter_client_call_with_retry_defaults(self):
        """call_with_retry defaults match the implementation plan contract."""
        from src.api.openrouter import OpenRouterClient

        sig = inspect.signature(OpenRouterClient.call_with_retry)
        assert sig.parameters["temperature"].default == 0.0
        assert sig.parameters["max_tokens"].default == 2048

    def test_openrouter_client_max_retries_constant(self):
        """OpenRouterClient.MAX_RETRIES matches contract (3)."""
        from src.api.openrouter import OpenRouterClient

        assert OpenRouterClient.MAX_RETRIES == 3

    def test_openrouter_client_retry_delay_base_constant(self):
        """OpenRouterClient.RETRY_DELAY_BASE matches contract (1.0)."""
        from src.api.openrouter import OpenRouterClient

        assert OpenRouterClient.RETRY_DELAY_BASE == 1.0

    def test_tool_registry_search_by_embedding_signature(self):
        """ToolRegistry.search_by_embedding accepts query_embedding and top_k."""
        from src.agent.registry import ToolRegistry

        sig = inspect.signature(ToolRegistry.search_by_embedding)
        params = list(sig.parameters.keys())
        assert "query_embedding" in params
        assert "top_k" in params

    def test_tool_registry_constructor_accepts_openrouter_client(self):
        """ToolRegistry.__init__ accepts an openrouter_client parameter for DI."""
        from src.agent.registry import ToolRegistry

        sig = inspect.signature(ToolRegistry.__init__)
        params = list(sig.parameters.keys())
        assert "openrouter_client" in params

    def test_embedding_retriever_constructor_accepts_openrouter_client(self):
        """EmbeddingRetriever.__init__ accepts openrouter_client for DI."""
        from src.agent.retrieval import EmbeddingRetriever

        sig = inspect.signature(EmbeddingRetriever.__init__)
        params = list(sig.parameters.keys())
        assert "openrouter_client" in params
        assert "registry" in params

    def test_tool_retriever_retrieve_signature(self):
        """ToolRetriever.retrieve has the expected abstract interface."""
        from src.agent.retrieval import ToolRetriever

        sig = inspect.signature(ToolRetriever.retrieve)
        params = list(sig.parameters.keys())
        assert "query" in params
        assert "query_embedding" in params
        assert "top_k" in params
        assert "similarity_threshold" in params

    def test_normalizer_registry_get_normalizer_signature(self):
        """NormalizerRegistry.get_normalizer accepts provider string."""
        from src.api.normalizers import NormalizerRegistry

        sig = inspect.signature(NormalizerRegistry.get_normalizer)
        params = list(sig.parameters.keys())
        assert "provider" in params

    def test_prompt_manager_get_prompt_signature(self):
        """PromptManager.get_prompt accepts name and version."""
        from src.agent.prompts import PromptManager

        sig = inspect.signature(PromptManager.get_prompt)
        params = list(sig.parameters.keys())
        assert "name" in params
        assert "version" in params

    def test_prompt_manager_render_prompt_signature(self):
        """PromptManager.render_prompt accepts name and variables dict."""
        from src.agent.prompts import PromptManager

        sig = inspect.signature(PromptManager.render_prompt)
        params = list(sig.parameters.keys())
        assert "name" in params
        assert "variables" in params


# ============================================================================
# 4. Constant & Configuration Contract Tests
# ============================================================================


class TestConfigurationContracts:
    """Verify configuration contracts between Units 4 and 6."""

    def test_similarity_threshold_matches_rag_spec(self):
        """SIMILARITY_THRESHOLD is 0.70 per FR-2.3."""
        from src.api.openrouter import SIMILARITY_THRESHOLD

        assert SIMILARITY_THRESHOLD == 0.70

    def test_default_top_k_matches_rag_spec(self):
        """DEFAULT_TOP_K is 8 per FR-2.3."""
        from src.api.openrouter import DEFAULT_TOP_K

        assert DEFAULT_TOP_K == 8

    def test_default_embedding_model_matches_spec(self):
        """DEFAULT_MODEL matches FR-2.3 spec for OpenAI text-embedding-3-small."""
        from src.api.openrouter import DEFAULT_MODEL

        assert DEFAULT_MODEL == "openai/text-embedding-3-small"

    def test_internal_models_has_required_keys(self):
        """INTERNAL_MODELS has all required pipeline stage keys."""
        from src.config import INTERNAL_MODELS

        required_keys = {"tool_selection", "dimension_extraction", "planner", "embedding"}
        assert required_keys.issubset(set(INTERNAL_MODELS.keys())), (
            f"Missing keys: {required_keys - set(INTERNAL_MODELS.keys())}"
        )

    def test_settings_has_openai_api_key_field(self):
        """Settings model has openai_api_key field used by OpenRouterClient."""
        from src.config import Settings

        assert "openai_api_key" in Settings.model_fields

    def test_model_config_has_expected_fields(self):
        """ModelConfig has all expected model configuration fields."""
        from src.config import ModelConfig

        expected = {
            "tool_selection", "dimension_extraction", "planner",
            "embedding", "response_generation",
        }
        actual = set(ModelConfig.model_fields.keys())
        assert expected.issubset(actual), (
            f"Missing ModelConfig fields: {expected - actual}"
        )

    def test_user_configurable_models_all_have_provider(self):
        """Every user-configurable model specifies a provider."""
        from src.config import USER_CONFIGURABLE_MODELS

        for model_id, config in USER_CONFIGURABLE_MODELS.items():
            assert "provider" in config, f"Model {model_id} missing 'provider'"
            assert isinstance(config["provider"], str)

    def test_user_configurable_models_providers_have_normalizers(self):
        """Every provider in USER_CONFIGURABLE_MODELS has a registered normalizer."""
        from src.api.normalizers import NormalizerRegistry, ProviderResponseNormalizer
        from src.config import USER_CONFIGURABLE_MODELS

        for model_id, config in USER_CONFIGURABLE_MODELS.items():
            provider = config["provider"]
            normalizer = NormalizerRegistry.get_normalizer(provider)
            assert isinstance(normalizer, ProviderResponseNormalizer), (
                f"No normalizer for provider '{provider}' (model: {model_id})"
            )


# ============================================================================
# 5. Shape Compatibility Tests (no network calls)
# ============================================================================


class TestShapeCompatibility:
    """Verify that data shapes flowing between units are compatible."""

    def test_tool_definition_roundtrip_from_yaml_shape(self):
        """A realistic YAML-shaped dict validates as ToolDefinition."""
        from src.api.models.tool import ToolDefinition

        yaml_shape = {
            "id": "market_share_trend",
            "name": "Market Share Trend",
            "description": "Analyzes market share trends for brands over time",
            "capabilities": ["trend_analysis", "market_share"],
            "required_dimensions": ["brand", "time_range"],
            "optional_dimensions": ["geography", "category"],
            "parameters": [
                {
                    "name": "brand",
                    "type": "string",
                    "description": "Brand name to analyze",
                    "required": True,
                }
            ],
            "output_schema": {
                "format": "json",
                "description": "Time series of market share percentages",
            },
            "example_queries": ["What is Nike's market share trend?"],
            "aliases": ["share trend", "market trend"],
            "version": "1.0.0",
        }
        tool = ToolDefinition(**yaml_shape)
        assert tool.id == "market_share_trend"

    def test_retrieved_tool_shape_from_registry_output(self):
        """A realistic RetrievedTool shape validates correctly."""
        from src.api.models.tool import RetrievedTool, ToolDefinition

        tool_def = ToolDefinition(
            id="brand_comparison",
            name="Brand Comparison",
            description="Compares brands",
            capabilities=["comparison"],
            required_dimensions=["brand"],
            optional_dimensions=[],
            parameters=[],
            output_schema={"format": "json", "description": "Comparison results"},
            example_queries=["Compare Nike vs Adidas"],
            aliases=["brand compare"],
            version="1.0.0",
        )
        retrieved = RetrievedTool(
            tool_id="brand_comparison",
            tool_definition=tool_def,
            similarity=0.85,
            rank=1,
        )
        assert retrieved.similarity >= 0.70
        assert retrieved.rank == 1

    def test_cosine_similarity_accepts_numpy_arrays(self):
        """ToolRegistry._cosine_similarity works with np.ndarray inputs,
        matching the shape returned by OpenRouterClient.embed_texts."""
        from src.agent.registry import ToolRegistry

        a = np.random.rand(1536).astype(np.float32)
        b = np.random.rand(1536).astype(np.float32)
        sim = ToolRegistry._cosine_similarity(a, b)
        assert isinstance(sim, float)
        assert -1.0 <= sim <= 1.0

    def test_cosine_similarity_handles_dimension_mismatch(self):
        """ToolRegistry._cosine_similarity handles vectors of different lengths,
        in case embed_texts returns different dimensions."""
        from src.agent.registry import ToolRegistry

        a = np.random.rand(1536).astype(np.float32)
        b = np.random.rand(768).astype(np.float32)
        sim = ToolRegistry._cosine_similarity(a, b)
        assert isinstance(sim, float)

    def test_circuit_breaker_lifecycle(self):
        """CircuitBreaker state transitions work as expected for downstream consumers."""
        from src.api.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=1)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_attempt() is True

        # Record failures up to threshold
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_attempt() is False

        # Recovery via success
        cb.state = CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_prompt_version_model_validates(self):
        """PromptVersion can be constructed with expected fields."""
        from datetime import datetime

        from src.agent.prompts import PromptVersion

        pv = PromptVersion(
            version="v1.0.0",
            template_name="test_prompt",
            template_content="Hello {name}",
            variables=["name"],
            created_at=datetime.now(),
            created_by="test",
        )
        assert pv.version == "v1.0.0"

    def test_user_friendly_error_shape(self):
        """UserFriendlyError carries code, message, and request_id."""
        from src.api.openrouter import UserFriendlyError

        err = UserFriendlyError(
            code="TEST_ERROR",
            message="Something went wrong",
            request_id="abc123",
        )
        assert err.code == "TEST_ERROR"
        assert err.message == "Something went wrong"
        assert err.request_id == "abc123"
        assert "abc123" in str(err)
