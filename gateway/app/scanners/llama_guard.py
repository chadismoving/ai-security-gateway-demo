from __future__ import annotations

import logging
import re

import httpx

from app.config import Settings
from app.models.schemas import Classification, Direction


logger = logging.getLogger(__name__)


class LlamaGuardClient:
    """HTTP boundary around Llama Guard with a deterministic interview mode."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def classify(
        self, direction: Direction, content: str, *, mode: str | None = None
    ) -> Classification:
        selected_mode = mode or self._configured_mode()
        if selected_mode == "offline":
            return self._mock_classify(direction, content)
        if selected_mode == "online":
            return await self._classify_online(direction, content)
        if selected_mode != "local":
            return self._unavailable("unsupported_guardrail_mode")

        url = self.settings.llama_guard_local_url or self.settings.llama_guard_url
        try:
            async with httpx.AsyncClient(timeout=self.settings.llama_guard_timeout_seconds) as client:
                response = await client.post(
                    f"{url.rstrip('/')}/classify",
                    json={"direction": direction, "content": content},
                )
                response.raise_for_status()
                payload = response.json()
                return Classification(**payload, detector="llama_guard_local")
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("Security classifier unavailable; fallback policy activated: %s", exc)
            return Classification(
                classification="unavailable",
                category="classifier_unavailable",
                confidence=None,
                detector="llama_guard_local_fallback",
                fallback=True,
            )

    async def health(self) -> str:
        if self._online_url().startswith("https://") and self._online_key() and self._online_model():
            return "online configured"
        return "online not configured"

    async def local_health(self) -> str:
        url = self.settings.llama_guard_local_url or self.settings.llama_guard_url
        try:
            async with httpx.AsyncClient(timeout=self.settings.llama_guard_timeout_seconds) as client:
                response = await client.get(f"{url.rstrip('/')}/health")
                response.raise_for_status()
            return "local available"
        except httpx.HTTPError:
            return "local unavailable"

    async def _classify_online(
        self, direction: Direction, content: str
    ) -> Classification:
        api_key = self._online_key()
        if not api_key:
            logger.warning("Online Llama Guard API key is not configured")
            return self._unavailable("online_auth_missing")

        messages = self._guard_messages(direction, content)
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.llama_guard_timeout_seconds
            ) as client:
                response = await client.post(
                    self._online_url(),
                    headers={
                        "Content-Type": "application/json",
                        "cf-aig-authorization": (
                            f"Bearer {api_key}"
                        ),
                    },
                    json={
                        "model": self._online_model(),
                        "messages": messages,
                        "temperature": 0,
                        "max_tokens": 32,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                output = payload["choices"][0]["message"]["content"]
                return self._parse_guard_output(output)
        except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as exc:
            logger.warning(
                "Online Llama Guard unavailable; fallback policy activated: %s",
                exc,
            )
            return self._unavailable("online_classifier_unavailable")

    @staticmethod
    def _guard_messages(direction: Direction, content: str) -> list[dict[str, str]]:
        if direction == "request":
            return [{"role": "user", "content": content}]
        return [
            {
                "role": "user",
                "content": "Provide a response to the user's enterprise AI request.",
            },
            {"role": "assistant", "content": content},
        ]

    @staticmethod
    def _parse_guard_output(output: str) -> Classification:
        normalized = output.strip().lower()
        first_line = normalized.splitlines()[0] if normalized else ""
        if first_line == "safe":
            return Classification(
                classification="safe",
                category=None,
                confidence=None,
                detector="llama_guard_online",
            )
        if first_line == "unsafe":
            category_match = re.search(r"\bS\d+\b", output, flags=re.IGNORECASE)
            category = category_match.group(0).upper() if category_match else "policy_violation"
            return Classification(
                classification="unsafe",
                category=category,
                confidence=None,
                detector="llama_guard_online",
            )
        raise ValueError("Unexpected Llama Guard output format")

    @staticmethod
    def _unavailable(category: str) -> Classification:
        return Classification(
            classification="unavailable",
            category=category,
            confidence=None,
            detector="llama_guard_online_fallback",
            fallback=True,
        )

    @staticmethod
    def _mock_classify(direction: Direction, content: str) -> Classification:
        normalized = " ".join(content.lower().split())
        if direction == "response" and any(
            marker in normalized
            for marker in (
                "test_policy_violation",
                "instructions for stealing another person's password",
                "plan the theft of another person's password",
            )
        ):
            return Classification(
                classification="unsafe",
                category="unsafe_model_response",
                confidence=0.99,
                detector="llama_guard_offline_demo",
            )

        prompt_attack_markers = (
            "ignore the application's previous instructions",
            "ignore previous instructions",
            "reveal information that should remain private",
            "system prompt",
            "bypass policy",
            "steal another person's password",
            "access their account without permission",
        )
        if direction == "request" and any(marker in normalized for marker in prompt_attack_markers):
            return Classification(
                classification="unsafe",
                category="prompt_policy_violation",
                confidence=0.98,
                detector="llama_guard_offline_demo",
            )

        return Classification(
            classification="safe",
            category=None,
            confidence=0.99,
            detector="llama_guard_offline_demo",
        )

    def _configured_mode(self) -> str:
        return {
            "mock": "offline",
            "cloudflare": "online",
            "remote": "local",
        }.get(self.settings.llama_guard_mode, self.settings.llama_guard_mode)

    def _online_url(self) -> str:
        return self.settings.llama_guard_online_url or self.settings.llama_guard_url

    def _online_key(self) -> str:
        return self.settings.llama_guard_online_api_key or self.settings.llama_guard_api_key

    def _online_model(self) -> str:
        return self.settings.llama_guard_online_model or self.settings.llama_guard_model
