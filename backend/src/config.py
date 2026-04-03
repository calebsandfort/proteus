from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/proteus"
    openai_api_key: str = ""
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:5000"  # ASP.NET Core Data API (IU-3)

    model_config = {"env_file": ".env", "extra": "ignore"}


# FR-8.2: Internal Pipeline Models
# These models are used for specific pipeline stages and are not user-configurable
INTERNAL_MODELS = {
    "tool_selection": "minimax/text-01",  # MiniMax-Text-01 for tool selection
    "dimension_extraction": "moonshot/kimi-k2",  # Kimi-K2 for dimension extraction
    "planner": "google/gemini-2.0-flash",  # GLM-4-Air (via Gemini Flash) for planning
    "embedding": "openai/text-embedding-3-small",  # OpenAI embedding for vector operations
}


# FR-8.1 & FR-8.3: User-configurable models with provider info and capabilities
# All LLM calls route through OpenRouter - no direct provider API integrations
USER_CONFIGURABLE_MODELS = {
    "openai/gpt-4o": {"provider": "openai", "supports_function_calling": True},
    "google/gemini-2.0-flash": {"provider": "google", "supports_function_calling": True},
    "anthropic/claude-3.5-sonnet": {"provider": "anthropic", "supports_function_calling": True},
    "moonshot/kimi-k2": {"provider": "kimi", "supports_function_calling": True},
    "minimax/text-01": {"provider": "minimax", "supports_function_calling": True},
    "google/gemini-2.5-pro": {"provider": "glm", "supports_function_calling": True},
}


class ModelConfig(BaseSettings):
    """
    Model configuration for pipeline execution.

    FR-8.4: Pipeline SHALL be model-agnostic. Swapping models requires only configuration.
    These settings can be overridden via environment variables with MODEL_ prefix.

    Defaults match INTERNAL_MODELS but can be changed for testing or experimentation.
    """

    # Internal model overrides (defaults from INTERNAL_MODELS)
    tool_selection: str = INTERNAL_MODELS["tool_selection"]
    dimension_extraction: str = INTERNAL_MODELS["dimension_extraction"]
    planner: str = INTERNAL_MODELS["planner"]
    embedding: str = INTERNAL_MODELS["embedding"]

    # User-configurable response generation model (FR-8.3)
    # This is the default model for response generation - users can override
    response_generation: str = "openai/gpt-4o"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
        # Environment variable prefix for model settings
        "env_prefix": "MODEL_",
    }


settings = Settings()
model_config = ModelConfig()
