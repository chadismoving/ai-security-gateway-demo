from fastapi import APIRouter, Depends, Query

from app.dependencies import get_database
from app.logging.database import AuditDatabase
from app.models.schemas import SecurityEvent


router = APIRouter(tags=["audit"])


@router.get("/events", response_model=list[SecurityEvent])
def recent_events(
    limit: int = Query(default=50, ge=1, le=500),
    database: AuditDatabase = Depends(get_database),
) -> list[dict[str, object]]:
    return database.recent(limit)


@router.delete("/events", status_code=204)
def clear_events(database: AuditDatabase = Depends(get_database)) -> None:
    database.clear()
