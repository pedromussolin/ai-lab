"""Unit tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.providers.base import LLMMessage, LLMResponse, ToolDefinition
from app.providers.factory import LLMProviderFactory


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_complete_success(self):
        with patch("app.providers.openai_provider.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.model = "gpt-4o"
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello!"
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            from app.providers.openai_provider import OpenAIProvider
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.openai_api_key = "sk-test"
                provider = OpenAIProvider()
                response = await provider.complete(
                    messages=[LLMMessage(role="user", content="Hello")],
                    model="gpt-4o",
                )

            assert response.content == "Hello!"
            assert response.provider == "openai"

    def test_is_not_available_without_key(self):
        with patch("app.providers.openai_provider.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            from app.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            assert not provider.is_available()


class TestProviderFactory:
    def test_raises_for_unknown_provider(self):
        from app.core.exceptions import ProviderError
        factory = LLMProviderFactory()
        with pytest.raises(ProviderError):
            factory.get_llm_provider("unknown_provider")

    def test_get_available_providers_returns_list(self):
        factory = LLMProviderFactory()
        available = factory.get_available_llm_providers()
        assert isinstance(available, list)
