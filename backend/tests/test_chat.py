import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/chat", json={"message": "test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_returns_stream():
    async def mock_stream(*args, **kwargs):
        for chunk in ["Hello", " world"]:
            yield chunk

    with patch("app.routers.chat.llm.stream_chat", side_effect=lambda *a, **k: mock_stream()):
        with patch("app.routers.chat.rag.retrieve_similar", return_value=[]):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/chat",
                    json={"message": "Why is payment API slow?"},
                    headers={"X-API-Key": "dev-secret"},
                )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
