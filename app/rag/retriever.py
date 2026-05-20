"""RAG retrieval from pgvector (local) and Azure AI Search (cloud)."""

from dataclasses import dataclass
from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


@dataclass
class RetrievalResult:
    content: str
    source: str
    score: float
    metadata: dict[str, Any]


class LocalVectorRetriever:
    """Retrieves similar chunks from pgvector."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def retrieve(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        sql = text("""
            SELECT
                dc.content,
                d.filename AS source,
                1 - (dc.embedding <=> CAST(:embedding AS vector)) AS score,
                dc.chunk_metadata
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.status = 'ready'
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        result = await self._db.execute(
            sql,
            {"embedding": str(query_embedding), "top_k": top_k},
        )
        rows = result.fetchall()
        return [
            RetrievalResult(
                content=row.content,
                source=row.source,
                score=float(row.score),
                metadata=row.chunk_metadata or {},
            )
            for row in rows
        ]


class AzureSearchRetriever:
    """Retrieves from Azure AI Search using hybrid (vector + keyword) search."""

    def __init__(self) -> None:
        self._credential = AzureKeyCredential(settings.azure_search_api_key)
        self._endpoint = settings.azure_search_endpoint
        self._index = settings.azure_search_index

    async def retrieve(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 5,
        filters: str | None = None,
    ) -> list[RetrievalResult]:
        async with SearchClient(
            endpoint=self._endpoint,
            index_name=self._index,
            credential=self._credential,
        ) as client:
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top_k,
                fields="embedding",
            )
            results = await client.search(
                search_text=query,
                vector_queries=[vector_query],
                top=top_k,
                filter=filters,
                query_type="semantic",
                semantic_configuration_name=settings.azure_search_semantic_config,
                query_caption="extractive",
            )
            output = []
            async for result in results:
                output.append(
                    RetrievalResult(
                        content=result["content"],
                        source=result.get("source", ""),
                        score=result["@search.score"],
                        metadata={"document_id": result.get("document_id")},
                    )
                )
            return output
