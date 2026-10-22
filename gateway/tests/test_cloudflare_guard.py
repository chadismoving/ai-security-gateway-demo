from __future__ import annotations

import json

import httpx
import pytest

from app.config import Settings
from app.scanners.llama_guard import LlamaGuardClient


def test_cloudflare_output_parser_handles_safe_and_categories() -> None:
    safe = LlamaGuardClient._parse_guard_output("safe")
    unsafe = LlamaGuardClient._parse_guard_output("unsafe\nS2, S7")
    assert safe.classification == "safe"
    assert safe.confidence is None
    assert unsafe.classification == "unsafe"
    assert unsafe.category == "S2"
    assert unsafe.detector == "llama_guard_online"


@pytest.mark.asyncio
async def test_cloudflare_client_uses_gateway_auth_header(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("cf-aig-authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "unsafe\nS7"}}]},
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mock_client)
    settings = Settings(
        llama_guard_mode="cloudflare",
        llama_guard_url="https://gateway.example/compat/chat/completions",
        llama_guard_api_key="test-token-not-a-secret",
        llama_guard_model="workers-ai/@cf/meta/llama-guard-3-8b",
    )
    result = await LlamaGuardClient(settings).classify(
        "request", "synthetic test", mode="online"
    )

    assert result.classification == "unsafe"
    assert result.category == "S7"
    assert captured["auth"] == "Bearer test-token-not-a-secret"
    assert captured["url"] == settings.llama_guard_url
    assert captured["body"]["model"] == settings.llama_guard_model
    assert "Authorization" not in captured
