"""Message repository."""

import uuid

from sqlalchemy import select

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def get_conversation_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int = 100,
    ) -> list[Message]:
        result = await self._db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
