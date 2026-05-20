"""Vector indexing to pgvector (local) and Azure AI Search (cloud)."""

from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.rag.chunker import TextChunk


class LocalVectorIndexer:
    """Indexes chunks into pgvector."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def index_chunks(
        self,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
        document_id: str,
    ) -> None:
        from app.models.document import DocumentChunk
        from sqlalchemy import delete

        # Remove existing chunks for this document
        await self._db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk.index,
                content=chunk.content,
                chunk_metadata=chunk.metadata,
                embedding=embedding,
                token_count=chunk.token_count,
            )
            self._db.add(db_chunk)

        await self._db.flush()


class AzureSearchIndexer:
    """Indexes chunks into Azure AI Search."""

    INDEX_NAME = settings.azure_search_index

    def __init__(self) -> None:
        self._credential = AzureKeyCredential(settings.azure_search_api_key)
        self._endpoint = settings.azure_search_endpoint

    async def ensure_index(self) -> None:
        """Create the index if it doesn't exist."""
        async with SearchIndexClient(
            endpoint=self._endpoint, credential=self._credential
        ) as client:
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
                SearchField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    analyzer_name="en.microsoft",
                ),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=3072,
                    vector_search_profile_name="hnsw-profile",
                ),
                SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
            ]
            vector_search = VectorSearch(
                algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
                profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw")],
            )
            semantic_search = SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="default",
                        prioritized_fields=SemanticPrioritizedFields(
                            content_fields=[SemanticField(field_name="content")]
                        ),
                    )
                ]
            )
            index = SearchIndex(
                name=self.INDEX_NAME,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search,
            )
            await client.create_or_update_index(index)

    async def index_chunks(
        self,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
        document_id: str,
        source: str = "",
    ) -> None:
        async with SearchClient(
            endpoint=self._endpoint,
            index_name=self.INDEX_NAME,
            credential=self._credential,
        ) as client:
            documents = [
                {
                    "id": f"{document_id}-{chunk.index}",
                    "document_id": document_id,
                    "chunk_index": chunk.index,
                    "content": chunk.content,
                    "embedding": embedding,
                    "source": source,
                }
                for chunk, embedding in zip(chunks, embeddings, strict=True)
            ]
            await client.upload_documents(documents)
