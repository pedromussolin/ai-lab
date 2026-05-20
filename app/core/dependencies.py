"""FastAPI dependency injection."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.providers.factory import LLMProviderFactory
from app.repositories.conversation import ConversationRepository
from app.repositories.document import DocumentRepository
from app.repositories.message import MessageRepository
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.guardrail_service import GuardrailService
from app.services.persona_service import PersonaService
from app.services.prompt_service import PromptService
from app.services.rag_service import RAGService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DBSession = Depends(get_db)


async def get_llm_factory() -> LLMProviderFactory:
    return LLMProviderFactory()


LLMFactory = Depends(get_llm_factory)


async def get_chat_service(
    db: AsyncSession = DBSession,
    llm_factory: LLMProviderFactory = LLMFactory,
) -> ChatService:
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    persona_svc = PersonaService()
    prompt_svc = PromptService()
    guardrail_svc = GuardrailService()
    embedding_svc = EmbeddingService(llm_factory)
    rag_svc = RAGService(db, embedding_svc)
    return ChatService(
        llm_factory=llm_factory,
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        persona_svc=persona_svc,
        prompt_svc=prompt_svc,
        guardrail_svc=guardrail_svc,
        rag_svc=rag_svc,
    )


async def get_document_service(
    db: AsyncSession = DBSession,
    llm_factory: LLMProviderFactory = LLMFactory,
) -> DocumentService:
    doc_repo = DocumentRepository(db)
    embedding_svc = EmbeddingService(llm_factory)
    rag_svc = RAGService(db, embedding_svc)
    return DocumentService(doc_repo=doc_repo, embedding_svc=embedding_svc, rag_svc=rag_svc)
