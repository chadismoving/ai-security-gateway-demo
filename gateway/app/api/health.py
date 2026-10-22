from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import get_database, get_guard, get_pipeline
from app.logging.database import AuditDatabase
from app.scanners.llama_guard import LlamaGuardClient
from app.pipeline import SecurityPipeline


router = APIRouter(tags=["operations"])


@router.get("/health")
async def health(
    settings: Settings = Depends(get_settings),
    guard: LlamaGuardClient = Depends(get_guard),
    database: AuditDatabase = Depends(get_database),
    pipeline: SecurityPipeline = Depends(get_pipeline),
) -> dict[str, str]:
    llm = pipeline.llm
    return {
        "status": "ok",
        "gateway": "healthy",
        "guardrail_online": await guard.health(),
        "guardrail_local": await guard.local_health(),
        "llm_online": llm.online_status(),
        "llm_local": llm.local_status(),
        "audit": "healthy" if database.available else "unavailable (non-fatal)",
    }
