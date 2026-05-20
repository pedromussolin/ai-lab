"""Unified RAG pipeline orchestrating retrieval from all sources."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.rag.reranker import SimpleReranker
from app.rag.retriever import AzureSearchRetriever, LocalVectorRetriever, RetrievalResult
from app.services.embedding_service import EmbeddingService


class RAGPipeline:
    """
    Hybrid RAG pipeline: retrieves from pgvector (local) and/or
    Azure AI Search (cloud) then reranks combined results.
    """

    def __init__(self, db: AsyncSession, embedding_svc: EmbeddingService) -> None:
        self._db = db
        self._embedding_svc = embedding_svc
        self._local_retriever = LocalVectorRetriever(db)
        self._azure_retriever = AzureSearchRetriever() if settings.azure_search_endpoint else None
        self._reranker = SimpleReranker()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_local: bool = True,
        use_azure: bool = True,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        query_embedding = await self._embedding_svc.embed_text(query)
        all_results: list[RetrievalResult] = []

        if use_local:
            local_results = await self._local_retriever.retrieve(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters,
            )
            all_results.extend(local_results)

        if use_azure and self._azure_retriever:
            try:
                azure_results = await self._azure_retriever.retrieve(
                    query=query,
                    query_embedding=query_embedding,
                    top_k=top_k,
                )
                all_results.extend(azure_results)
            except Exception:
                pass  # Azure Search is optional; fail gracefully

        return self._reranker.rerank(all_results, top_k=top_k)
