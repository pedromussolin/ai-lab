"""Azure OpenAI / AI Foundry LLM provider adapter."""

from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncAzureOpenAI
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


class AzureOpenAIProvider(BaseLLMProvider):
    provider_name = "azure"

    def __init__(self) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )

    def is_available(self) -> bool:
        return bool(settings.azure_openai_api_key and settings.azure_openai_endpoint)

    def get_default_model(self) -> str:
        return settings.azure_openai_deployment

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
            deployment = model or self.get_default_model()
            params: dict[str, Any] = {
                "model": deployment,
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
            deployment = model or self.get_default_model()
            params: dict[str, Any] = {
                "model": deployment,
                "messages": self._build_messages(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }
            async with self._client.chat.completions.stream(**params) as stream:
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception as e:
            raise ProviderError(self.provider_name, str(e)) from e


class AzureEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "azure"

    def __init__(self) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )

    def is_available(self) -> bool:
        return bool(settings.azure_openai_api_key and settings.azure_openai_endpoint)

    def get_default_model(self) -> str:
        return settings.azure_openai_embedding_deployment

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def embed(self, texts: list[str], model: str | None = None) -> EmbeddingResponse:
        try:
            deployment = model or self.get_default_model()
            response = await self._client.embeddings.create(model=deployment, input=texts)
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
