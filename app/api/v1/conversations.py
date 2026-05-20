"""Conversation CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import DBSession
from app.core.exceptions import NotFoundError
from app.core.security import verify_api_key
from app.models.conversation import Conversation
from app.repositories.conversation import ConversationRepository
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailSchema,
    ConversationSchema,
    ConversationUpdate,
)

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationSchema])
async def list_conversations(
    db=DBSession,
    limit: int = 20,
    offset: int = 0,
    _: str = Depends(verify_api_key),
):
    repo = ConversationRepository(db)
    return await repo.get_active(limit=limit, offset=offset)


@router.post("/conversations", response_model=ConversationSchema, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    db=DBSession,
    _: str = Depends(verify_api_key),
):
    repo = ConversationRepository(db)
    conv = Conversation(
        title=data.title,
        persona_id=data.persona_id,
        provider=data.provider,
        model=data.model,
        metadata_=data.metadata,
    )
    return await repo.create(conv)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailSchema)
async def get_conversation(
    conversation_id: uuid.UUID,
    db=DBSession,
    _: str = Depends(verify_api_key),
):
    repo = ConversationRepository(db)
    conv = await repo.get_with_messages(conversation_id)
    if not conv:
        raise NotFoundError("Conversation", conversation_id)
    return conv


@router.patch("/conversations/{conversation_id}", response_model=ConversationSchema)
async def update_conversation(
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    db=DBSession,
    _: str = Depends(verify_api_key),
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conversation_id)
    if not conv:
        raise NotFoundError("Conversation", conversation_id)
    if data.title is not None:
        conv.title = data.title
    if data.is_active is not None:
        conv.is_active = data.is_active
    await db.flush()
    return conv


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db=DBSession,
    _: str = Depends(verify_api_key),
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conversation_id)
    if not conv:
        raise NotFoundError("Conversation", conversation_id)
    await repo.delete(conv)
