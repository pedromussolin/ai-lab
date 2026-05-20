"""RAG query endpoint."""

from fastapi import APIRouter, Depends

from app.core.dependencies import DBSession
from app.core.security import verify_api_key
from app.providers.factory import LLMProviderFactory
from app.schemas.document import RAGQueryRequest, RAGResult
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/rag/query", response_model=list[RAGResult])
async def rag_query(
    request: RAGQueryRequest,
    db=DBSession,
    _: str = Depends(verify_api_key),
) -> list[RAGResult]:
    factory = LLMProviderFactory()
    embedding_svc = EmbeddingService(factory)
    rag_svc = RAGService(db, embedding_svc)
    results = await rag_svc.retrieve(query=request.query, top_k=request.top_k)
    return [
        RAGResult(content=r.content, source=r.source, score=r.score, metadata=r.metadata)
        for r in results
    ]
