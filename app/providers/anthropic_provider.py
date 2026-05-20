"""Anthropic LLM provider adapter."""

from collections.abc import AsyncGenerator
from typing import Any

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    ToolDefinition,
)


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    def is_available(self) -> bool:
        return bool(settings.anthropic_api_key)

    def get_default_model(self) -> str:
        return settings.anthropic_default_model

    def _build_messages_and_system(
        self, messages: list[LLMMessage]
    ) -> tuple[str | None, list[dict]]:
        """Separate system message from conversation messages."""
        system = None
        conversation = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                conversation.append({"role": m.role, "content": m.content})
        return system, conversation

    def _build_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
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
            system, conversation = self._build_messages_and_system(messages)
            params: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": conversation,
            }
            if system:
                params["system"] = system
            if tools:
                params["tools"] = self._build_tools(tools)

            response = await self._client.messages.create(**params)

            content = ""
            tool_calls = None
            for block in response.content:
                if block.type == "text":
                    content = block.text
                elif block.type == "tool_use":
                    if tool_calls is None:
                        tool_calls = []
                    tool_calls.append(
                        {
                            "id": block.id,
                            "type": "function",
                            "function": {"name": block.name, "arguments": str(block.input)},
                        }
                    )

            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                tool_calls=tool_calls,
                finish_reason=response.stop_reason or "stop",
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
            system, conversation = self._build_messages_and_system(messages)
            params: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": conversation,
            }
            if system:
                params["system"] = system

            async with self._client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise ProviderError(self.provider_name, str(e)) from e
