"""API tests for chat endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_ok(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_chat_requires_api_key(self, client):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauth_client:
            response = await unauth_client.post(
                "/api/v1/chat",
                json={"message": "Hello"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_validates_empty_message(self, client):
        response = await client.post(
            "/api/v1/chat",
            json={"message": ""},
        )
        assert response.status_code == 422


class TestConversationEndpoint:
    @pytest.mark.asyncio
    async def test_list_conversations_requires_auth(self):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as unauth_client:
            response = await unauth_client.get("/api/v1/conversations")
            assert response.status_code == 401
