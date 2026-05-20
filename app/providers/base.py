"""Abstract base classes for LLM providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str  # system | user | assistant | tool
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    usage: dict[str, int] = {}
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str = "stop"


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    provider: str
    usage: dict[str, int] = {}


class BaseLLMProvider(ABC):
    """Abstract LLM provider — chat completion."""

    provider_name: str = ""

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        ...

    @abstractmethod
    def get_default_model(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...


class BaseEmbeddingProvider(ABC):
    """Abstract embedding provider."""

    provider_name: str = ""

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> EmbeddingResponse:
        ...

    @abstractmethod
    def get_default_model(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...
