"""Embedding service with batching, caching, and normalization."""

import hashlib
import json
from typing import Any

from app.providers.factory import LLMProviderFactory


class EmbeddingService:
    def __init__(self, llm_factory: LLMProviderFactory) -> None:
        self._factory = llm_factory
        self._cache: dict[str, list[float]] = {}  # simple in-memory cache

    async def embed_text(self, text: str, provider: str | None = None) -> list[float]:
        """Embed a single text string."""
        results = await self.embed_batch([text], provider=provider)
        return results[0]

    async def embed_batch(
        self,
        texts: list[str],
        provider: str | None = None,
        batch_size: int = 16,
    ) -> list[list[float]]:
        """Embed a batch of texts with caching."""
        provider_obj = self._factory.get_embedding_provider(provider)

        # Check cache
        uncached_indices = []
        cached_results: dict[int, list[float]] = {}
        for i, text in enumerate(texts):
            key = self._cache_key(text, provider_obj.provider_name)
            if key in self._cache:
                cached_results[i] = self._cache[key]
            else:
                uncached_indices.append(i)

        # Embed uncached texts in batches
        new_embeddings: list[list[float]] = []
        uncached_texts = [texts[i] for i in uncached_indices]
        for batch_start in range(0, len(uncached_texts), batch_size):
            batch = uncached_texts[batch_start:batch_start + batch_size]
            response = await provider_obj.embed(batch)
            new_embeddings.extend(response.embeddings)

        # Store in cache
        for i, idx in enumerate(uncached_indices):
            key = self._cache_key(texts[idx], provider_obj.provider_name)
            self._cache[key] = new_embeddings[i]
            cached_results[idx] = new_embeddings[i]

        return [cached_results[i] for i in range(len(texts))]

    @staticmethod
    def _cache_key(text: str, provider: str) -> str:
        content = f"{provider}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
