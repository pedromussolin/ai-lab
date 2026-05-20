"""Central application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "AI Lab"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "change-me"
    api_key: str = "change-me"
    cors_origins: list[str] = ["*"]

    # Database
    database_url: str = "postgresql+asyncpg://ailab:ailab@localhost:5432/ailab"
    database_url_sync: str = "postgresql+psycopg2://ailab:ailab@localhost:5432/ailab"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-sonnet-4-5"
    anthropic_max_tokens: int = 4096
    anthropic_temperature: float = 0.7

    # Azure OpenAI / AI Foundry
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"

    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""
    azure_search_index: str = "ai-lab-docs"
    azure_search_semantic_config: str = "default"

    # LLM defaults
    default_llm_provider: str = "openai"
    default_embedding_provider: str = "openai"

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "ai-lab"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "ai-lab-api"
    otel_traces_exporter: str = "otlp"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Uploads
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # Logging
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
