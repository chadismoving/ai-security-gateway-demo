from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.llm.openai_provider import build_llm_provider
from app.logging.audit import AuditLogger
from app.logging.database import AuditDatabase
from app.pipeline import SecurityPipeline
from app.policy.engine import PolicyEngine
from app.scanners.llama_guard import LlamaGuardClient


@lru_cache
def get_database() -> AuditDatabase:
    database = AuditDatabase(get_settings().database_path)
    database.initialize()
    return database


@lru_cache
def get_guard() -> LlamaGuardClient:
    return LlamaGuardClient(get_settings())


@lru_cache
def get_pipeline() -> SecurityPipeline:
    settings = get_settings()
    database = get_database()
    return SecurityPipeline(
        guard=get_guard(),
        policy=PolicyEngine(settings.policy_path),
        llm=build_llm_provider(settings),
        audit=AuditLogger(database),
    )
