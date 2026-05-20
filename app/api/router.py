"""Main API router."""

from fastapi import APIRouter

from app.api.v1 import chat, conversations, documents, guardrails, personas, prompts, rag

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/api/v1", tags=["chat"])
api_router.include_router(
    conversations.router, prefix="/api/v1", tags=["conversations"]
)
api_router.include_router(documents.router, prefix="/api/v1", tags=["documents"])
api_router.include_router(rag.router, prefix="/api/v1", tags=["rag"])
api_router.include_router(personas.router, prefix="/api/v1", tags=["personas"])
api_router.include_router(prompts.router, prefix="/api/v1", tags=["prompts"])
api_router.include_router(guardrails.router, prefix="/api/v1", tags=["guardrails"])
