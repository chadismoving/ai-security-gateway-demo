from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        prompt: str,
        *,
        demo_scenario: str | None = None,
        mode: str | None = None,
    ) -> str:
        """Return text from the configured inference provider."""
