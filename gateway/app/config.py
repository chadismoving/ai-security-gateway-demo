from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SecureAI Gateway"
    llama_guard_mode: Literal["mock", "local", "remote", "cloudflare"] = "mock"
    llama_guard_url: str = "http://llama-guard:8000"
    llama_guard_api_key: str = ""
    llama_guard_model: str = "workers-ai/@cf/meta/llama-guard-3-8b"
    llama_guard_timeout_seconds: float = 30.0

    llama_guard_online_url: str = ""
    llama_guard_online_api_key: str = ""
    llama_guard_online_model: str = "workers-ai/@cf/meta/llama-guard-3-8b"
    llama_guard_local_url: str = "http://llama-guard:8000"

    llm_mode: Literal["offline", "openai"] = "offline"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: float = 20.0
    llm_online_url: str = ""
    llm_online_api_key: str = ""
    llm_online_model: str = "workers-ai/@cf/moonshotai/kimi-k2.6"
    llm_local_url: str = ""
    llm_local_api_key: str = ""
    llm_local_model: str = ""
    demo_offline_mode: bool = True

    database_path: str = "data/security.db"
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def policy_path(self) -> Path:
        return Path(__file__).parent / "policy" / "policies.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()
