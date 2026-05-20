"""Common Pydantic v2 schemas."""

import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    data: T
    message: str = "success"


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] = {}


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime
