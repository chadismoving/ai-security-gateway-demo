from __future__ import annotations

import json

import httpx
import pytest

from app.config import Settings
from app.llm.openai_provider import SwitchableLLMProvider


@pytest.mark.asyncio
async def test_online_llm_uses_gateway_auth_and_kimi_model(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["gateway_auth"] = request.headers.get("cf-aig-authorization")
        captured["authorization"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "Online answer"}}]})

    transport = httpx.MockTransport(handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mock_client)
    settings = Settings(
        llm_online_url="https://gateway.example/compat/chat/completions",
        llm_online_api_key="test-token-not-a-secret",
    )
    answer = await SwitchableLLMProvider(settings).chat("Hello", mode="online")

    assert answer == "Online answer"
    assert captured["url"] == settings.llm_online_url
    assert captured["gateway_auth"] == "Bearer test-token-not-a-secret"
    assert captured["authorization"] is None
    assert captured["body"]["model"] == "workers-ai/@cf/moonshotai/kimi-k2.6"


@pytest.mark.asyncio
async def test_local_llm_uses_openai_compatible_url(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"choices": [{"message": {"content": "NAS answer"}}]})

    transport = httpx.MockTransport(handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mock_client)
    settings = Settings(
        llm_local_url="http://nas-model:11434/v1",
        llm_local_api_key="local-key",
        llm_local_model="local-model",
    )
    answer = await SwitchableLLMProvider(settings).chat("Hello", mode="local")

    assert answer == "NAS answer"
    assert captured["url"] == "http://nas-model:11434/v1/chat/completions"
    assert captured["auth"] == "Bearer local-key"
