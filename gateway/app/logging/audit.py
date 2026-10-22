from __future__ import annotations

from datetime import datetime, timezone

from app.logging.database import AuditDatabase
from app.models.schemas import Classification, PolicyDecision


class AuditLogger:
    def __init__(
        self,
        database: AuditDatabase,
    ) -> None:
        self.database = database

    def log(
        self,
        *,
        user: str,
        direction: str,
        classification: Classification,
        decision: PolicyDecision,
        latency_ms: int,
        request_content: str | None,
        response_content: str | None,
    ) -> int | None:
        return self.database.insert(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user": user,
                "direction": direction.upper(),
                "classification": classification.classification.upper(),
                "category": (classification.category or "safe").upper(),
                "risk": decision.risk,
                "action": decision.action,
                "reason": decision.reason,
                "detector": decision.detector,
                "latency_ms": latency_ms,
                "request_preview": self.safe_preview(request_content),
                "response_preview": self.safe_preview(response_content),
            }
        )

    def safe_preview(self, content: str | None) -> str | None:
        if content is None:
            return None
        # Classifier-only mode intentionally omits raw content because no DLP scanner is present.
        return "[CONTENT OMITTED — LLAMA GUARD CLASSIFIER DEMO]"
