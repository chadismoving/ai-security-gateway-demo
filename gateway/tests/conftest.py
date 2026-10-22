from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.llm.openai_provider import OfflineLLMProvider
from app.logging.audit import AuditLogger
from app.logging.database import AuditDatabase
from app.pipeline import SecurityPipeline
from app.policy.engine import PolicyEngine
from app.scanners.llama_guard import LlamaGuardClient


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        llama_guard_mode="mock",
        llm_mode="offline",
        demo_offline_mode=True,
        database_path=str(tmp_path / "security.db"),
    )


@pytest.fixture
def pipeline(settings: Settings) -> SecurityPipeline:
    database = AuditDatabase(settings.database_path)
    database.initialize()
    return SecurityPipeline(
        guard=LlamaGuardClient(settings),
        policy=PolicyEngine(settings.policy_path),
        llm=OfflineLLMProvider(),
        audit=AuditLogger(database),
    )
