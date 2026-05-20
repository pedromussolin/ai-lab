"""Conversation repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    model = Conversation

    async def get_with_messages(self, id: uuid.UUID) -> Conversation | None:
        result = await self._db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == id)
        )
        return result.scalar_one_or_none()

    async def get_active(self, limit: int = 20, offset: int = 0) -> list[Conversation]:
        result = await self._db.execute(
            select(Conversation)
            .where(Conversation.is_active == True)  # noqa: E712
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
