"""Document schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampedSchema


class DocumentSchema(BaseSchema, TimestampedSchema):
    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    status: str
    chunk_count: int
    error_message: str | None = None


class DocumentProcessRequest(BaseModel):
    document_id: uuid.UUID
    chunk_size: int = Field(default=1000, ge=100, le=8000)
    chunk_overlap: int = Field(default=200, ge=0)
    indexing_strategy: str = Field(default="hybrid")  # local|azure|hybrid


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    provider: str | None = None
    index_name: str | None = None
    filters: dict[str, Any] = {}


class RAGResult(BaseModel):
    content: str
    source: str
    score: float
    metadata: dict[str, Any] = {}
