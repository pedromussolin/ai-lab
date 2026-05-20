"""LLM provider factory."""

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.azure_provider import AzureEmbeddingProvider, AzureOpenAIProvider
from app.providers.base import BaseEmbeddingProvider, BaseLLMProvider
from app.providers.openai_provider import OpenAIEmbeddingProvider, OpenAIProvider

_LLM_REGISTRY: dict[str, type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "azure": AzureOpenAIProvider,
}

_EMBEDDING_REGISTRY: dict[str, type[BaseEmbeddingProvider]] = {
    "openai": OpenAIEmbeddingProvider,
    "azure": AzureEmbeddingProvider,
}


class LLMProviderFactory:
    """Factory for creating LLM and embedding providers."""

    def get_llm_provider(self, provider_name: str | None = None) -> BaseLLMProvider:
        name = provider_name or settings.default_llm_provider
        cls = _LLM_REGISTRY.get(name)
        if not cls:
            raise ProviderError(name, f"Unknown provider '{name}'. Available: {list(_LLM_REGISTRY)}")
        provider = cls()
        if not provider.is_available():
            raise ProviderError(name, f"Provider '{name}' is not configured (missing API key)")
        return provider

    def get_embedding_provider(self, provider_name: str | None = None) -> BaseEmbeddingProvider:
        name = provider_name or settings.default_embedding_provider
        cls = _EMBEDDING_REGISTRY.get(name)
        if not cls:
            raise ProviderError(
                name,
                f"Unknown embedding provider '{name}'. Available: {list(_EMBEDDING_REGISTRY)}",
            )
        provider = cls()
        if not provider.is_available():
            raise ProviderError(name, f"Embedding provider '{name}' is not configured")
        return provider

    def get_available_llm_providers(self) -> list[str]:
        return [name for name, cls in _LLM_REGISTRY.items() if cls().is_available()]

    def get_available_embedding_providers(self) -> list[str]:
        return [name for name, cls in _EMBEDDING_REGISTRY.items() if cls().is_available()]
