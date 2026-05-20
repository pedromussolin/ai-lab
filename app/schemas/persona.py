"""Persona, Prompt, Guardrail schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampedSchema


class PersonaCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128, pattern=r'^[a-z0-9_-]+$')
    name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    system_prompt: str = Field(..., min_length=1)
    tone: str = "professional"
    allowed_tools: list[str] = []
    config: dict[str, Any] = {}


class PersonaSchema(BaseSchema, TimestampedSchema):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    system_prompt: str
    tone: str
    allowed_tools: list[str]
    is_active: bool
    is_builtin: bool


class PromptCreate(BaseModel):
    slug: str = Field(..., max_length=128)
    category: str = Field(..., description="system|chat|rag|tool")
    content: str = Field(..., min_length=1)
    variables: list[str] = []
    provider: str | None = None
    model: str | None = None


class PromptSchema(BaseSchema, TimestampedSchema):
    id: uuid.UUID
    slug: str
    version: int
    category: str
    content: str
    variables: list[str]
    provider: str | None
    model: str | None
    is_active: bool


class GuardrailCreate(BaseModel):
    slug: str = Field(..., max_length=128, pattern=r'^[a-z0-9_-]+$')
    name: str = Field(..., max_length=256)
    description: str | None = None
    rules: dict[str, Any] = Field(..., description="Guardrail rules configuration")


class GuardrailSchema(BaseSchema, TimestampedSchema):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    rules: dict[str, Any]
    is_active: bool
