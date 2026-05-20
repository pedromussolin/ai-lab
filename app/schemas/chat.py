"""Chat request/response schemas."""

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class MessageInput(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str = Field(..., min_length=1, max_length=32000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000, description="User message")
    conversation_id: uuid.UUID | None = Field(None, description="Continue existing conversation")
    persona_id: str | None = Field(None, description="Persona slug to use")
    provider: str | None = Field(None, description="LLM provider override")
    model: str | None = Field(None, description="Model override")
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(4096, ge=1, le=32000)
    use_rag: bool = Field(True, description="Enable RAG retrieval")
    tools_enabled: bool = Field(True, description="Enable tool calling")
    stream: bool = False
    metadata: dict[str, Any] = {}


class Citation(BaseModel):
    source: str
    title: str | None = None
    url: str | None = None
    content_snippet: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ToolCallResult(BaseModel):
    tool_name: str
    tool_input: dict[str, Any]
    tool_output: Any
    duration_ms: float


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    content: str
    citations: list[Citation] = []
    tool_calls: list[ToolCallResult] = []
    provider: str
    model: str
    usage: dict[str, int] = {}
    metadata: dict[str, Any] = {}


class StreamChunk(BaseModel):
    type: Literal["chunk", "tool_call", "citation", "done", "error"]
    content: str | None = None
    tool_call: ToolCallResult | None = None
    citation: Citation | None = None
    error: str | None = None
    conversation_id: uuid.UUID | None = None
    message_id: uuid.UUID | None = None
