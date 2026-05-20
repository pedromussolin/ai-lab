"""OpenAI LLM provider adapter."""

from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.base import (
    BaseEmbeddingProvider,
    BaseLLMProvider,
    EmbeddingResponse,
    LLMMessage,
    LLMResponse,
    ToolDefinition,
)


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    def is_available(self) -> bool:
        return bool(settings.openai_api_key)

    def get_default_model(self) -> str:
        return settings.openai_default_model

    def _build_messages(self, messages: list[LLMMessage]) -> list[dict]:
        result = []
        for m in messages:
            msg: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            result.append(msg)
        return result

    def _build_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        try:
            params: dict[str, Any] = {
                "model": model,
                "messages": self._build_messages(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                params["tools"] = self._build_tools(tools)
                params["tool_choice"] = "auto"

            response = await self._client.chat.completions.create(**params)
            choice = response.choices[0]

            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.message.tool_calls
                ]

            return LLMResponse(
                content=choice.message.content or "",
                model=response.model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
            )
        except Exception as e:
            raise ProviderError(self.provider_name, str(e)) from e

    async def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        try:
            params: dict[str, Any] = {
                "model": model,
                "messages": self._build_messages(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }
            if tools:
                params["tools"] = self._build_tools(tools)
                params["tool_choice"] = "auto"

            async with self._client.chat.completions.stream(**params) as stream:
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception as e:
            raise ProviderError(self.provider_name, str(e)) from e


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    def is_available(self) -> bool:
        return bool(settings.openai_api_key)

    def get_default_model(self) -> str:
        return settings.openai_embedding_model

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def embed(self, texts: list[str], model: str | None = None) -> EmbeddingResponse:
        try:
            model = model or self.get_default_model()
            response = await self._client.embeddings.create(model=model, input=texts)
            return EmbeddingResponse(
                embeddings=[item.embedding for item in response.data],
                model=response.model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            )
        except Exception as e:
            raise ProviderError(self.provider_name, str(e)) from e
