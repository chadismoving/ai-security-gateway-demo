from __future__ import annotations

import os
import re
from typing import Literal, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title="Local Llama Guard Adapter", version="2.0.0")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/")
OLLAMA_GUARD_MODEL = os.getenv("OLLAMA_GUARD_MODEL", "llama-guard3:1b")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))


class ClassifyRequest(BaseModel):
    direction: Literal["request", "response"]
    content: str = Field(min_length=1, max_length=20_000)


class ClassifyResponse(BaseModel):
    classification: Literal["safe", "unsafe"]
    category: Optional[str] = None
    confidence: Optional[float] = None


def guard_messages(direction: str, content: str) -> list[dict[str, str]]:
    if direction == "request":
        return [{"role": "user", "content": content}]
    return [
        {"role": "user", "content": "Provide a response to the user's enterprise AI request."},
        {"role": "assistant", "content": content},
    ]


@app.post("/classify", response_model=ClassifyResponse)
async def classify(payload: ClassifyRequest) -> ClassifyResponse:
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_GUARD_MODEL,
                    "messages": guard_messages(payload.direction, payload.content),
                    "stream": False,
                    "options": {"temperature": 0, "num_ctx": 2048},
                    "keep_alive": "10m",
                },
            )
            response.raise_for_status()
            output = response.json()["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local Llama Guard is unavailable") from exc

    first_line = output.lower().splitlines()[0] if output else ""
    if first_line == "safe":
        return ClassifyResponse(classification="safe")
    if first_line == "unsafe":
        category_match = re.search(r"\bS\d+\b", output, flags=re.IGNORECASE)
        category = category_match.group(0).upper() if category_match else "policy_violation"
        return ClassifyResponse(classification="unsafe", category=category)
    raise HTTPException(status_code=502, detail="Unexpected local Llama Guard output")


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            names = {model["name"] for model in response.json().get("models", [])}
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=503, detail="Local model runtime is unavailable")
    if OLLAMA_GUARD_MODEL not in names:
        raise HTTPException(status_code=503, detail="Local Llama Guard model is not installed")
    return {"status": "ok", "engine": "llama-guard", "model": OLLAMA_GUARD_MODEL}
