"""Document repository."""

import uuid

from sqlalchemy import select

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    async def get_by_status(self, status: str) -> list[Document]:
        result = await self._db.execute(
            select(Document).where(Document.status == status)
        )
        return list(result.scalars().all())
