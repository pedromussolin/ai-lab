"""Generic async SQLAlchemy repository base."""

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, id: uuid.UUID) -> ModelT | None:
        result = await self._db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
        **filters: Any,
    ) -> list[ModelT]:
        q = select(self.model)
        for attr, value in filters.items():
            q = q.where(getattr(self.model, attr) == value)
        q = q.offset(offset).limit(limit)
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def create(self, instance: ModelT) -> ModelT:
        self._db.add(instance)
        await self._db.flush()
        await self._db.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self._db.delete(instance)
        await self._db.flush()

    async def count(self, **filters: Any) -> int:
        from sqlalchemy import func
        q = select(func.count()).select_from(self.model)
        for attr, value in filters.items():
            q = q.where(getattr(self.model, attr) == value)
        result = await self._db.execute(q)
        return result.scalar_one()
