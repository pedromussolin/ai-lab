"""RAG service - facade over the RAG pipeline."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.pipeline import RAGPipeline
from app.rag.retriever import RetrievalResult
from app.services.embedding_service import EmbeddingService


class RAGService:
    def __init__(self, db: AsyncSession, embedding_svc: EmbeddingService) -> None:
        self._pipeline = RAGPipeline(db=db, embedding_svc=embedding_svc)

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        return await self._pipeline.retrieve(query=query, top_k=top_k, filters=filters)

    async def get_pipeline(self) -> RAGPipeline:
        return self._pipeline
