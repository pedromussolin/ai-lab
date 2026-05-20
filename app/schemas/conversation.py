"""Conversation schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampedSchema


class ConversationCreate(BaseModel):
    title: str = Field(default="New Conversation", max_length=512)
    persona_id: str | None = None
    provider: str = "openai"
    model: str = "gpt-4o"
    metadata: dict[str, Any] = {}


class ConversationUpdate(BaseModel):
    title: str | None = Field(None, max_length=512)
    is_active: bool | None = None


class MessageSchema(BaseSchema, TimestampedSchema):
    id: uuid.UUID
    role: str
    content: str
    tool_calls: list | None = None
    citations: list | None = None
    token_count: int


class ConversationSchema(BaseSchema, TimestampedSchema):
    id: uuid.UUID
    title: str
    persona_id: str | None
    provider: str
    model: str
    is_active: bool
    message_count: int = 0


class ConversationDetailSchema(ConversationSchema):
    messages: list[MessageSchema] = []
