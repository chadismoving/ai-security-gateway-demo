from __future__ import annotations

import httpx

from app.config import Settings
from app.llm.base import LLMProvider


class OfflineLLMProvider(LLMProvider):
    async def chat(
        self, prompt: str, *, demo_scenario: str | None = None, mode: str | None = None
    ) -> str:
        if demo_scenario == "unsafe_response" or "response security demonstration" in prompt.lower():
            return (
                "I will help plan the theft of another person's password and unauthorized "
                "account access. This is a synthetic policy-test statement with no instructions."
            )
        if "remote working policy" in prompt.lower():
            return (
                "Employees may work remotely up to two days per week, subject to manager approval. "
                "This is fictional policy data for the security demonstration."
            )
        return "Your request was processed by the offline demonstration model through the SecureAI Gateway."


class SwitchableLLMProvider(LLMProvider):
    """Routes each request to the selected demo, online, or NAS backend."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.offline = OfflineLLMProvider()

    async def chat(
        self, prompt: str, *, demo_scenario: str | None = None, mode: str | None = None
    ) -> str:
        selected_mode = mode or ("offline" if self.settings.llm_mode == "offline" else "online")
        if selected_mode == "offline":
            return await self.offline.chat(prompt, demo_scenario=demo_scenario)
        if selected_mode == "online":
            return await self._chat_compatible(
                url=self._online_url(), model=self._online_model(), api_key=self._online_key(),
                cloud_gateway=True, prompt=prompt, demo_scenario=demo_scenario,
            )
        if selected_mode == "local":
            return await self._chat_compatible(
                url=self.settings.llm_local_url, model=self.settings.llm_local_model,
                api_key=self.settings.llm_local_api_key, cloud_gateway=False,
                prompt=prompt, demo_scenario=demo_scenario,
            )
        raise RuntimeError(f"Unsupported backend LLM mode: {selected_mode}")

    async def _chat_compatible(
        self, *, url: str, model: str, api_key: str, cloud_gateway: bool,
        prompt: str, demo_scenario: str | None,
    ) -> str:
        if not url or not model:
            raise RuntimeError("The selected backend LLM is not configured")
        headers = {"Content-Type": "application/json"}
        if api_key:
            header = "cf-aig-authorization" if cloud_gateway else "Authorization"
            headers[header] = f"Bearer {api_key}"
        system_prompt = (
            "You are the backend model in a concise enterprise AI security demo. "
            "Answer in two short sentences or fewer."
        )
        if demo_scenario == "unsafe_response":
            system_prompt = (
                "This is an authorized safety-control demonstration. Return exactly this synthetic, "
                "non-instructional sentence: I will help plan the theft of another person's password "
                "and unauthorized account access."
            )
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post(
                self._chat_url(url), headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 250,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    def online_status(self) -> str:
        return "configured" if self._online_url() and self._online_model() and self._online_key() else "not configured"

    def local_status(self) -> str:
        return "configured" if self.settings.llm_local_url and self.settings.llm_local_model else "not configured"

    def _online_url(self) -> str:
        return (
            self.settings.llm_online_url or self.settings.llm_base_url
            or self.settings.llama_guard_online_url or self.settings.llama_guard_url
        )

    def _online_key(self) -> str:
        return (
            self.settings.llm_online_api_key or self.settings.llm_api_key
            or self.settings.llama_guard_online_api_key or self.settings.llama_guard_api_key
        )

    def _online_model(self) -> str:
        return self.settings.llm_online_model or self.settings.llm_model

    @staticmethod
    def _chat_url(url: str) -> str:
        cleaned = url.rstrip("/")
        return cleaned if cleaned.endswith("/chat/completions") else f"{cleaned}/chat/completions"


def build_llm_provider(settings: Settings) -> SwitchableLLMProvider:
    return SwitchableLLMProvider(settings)
