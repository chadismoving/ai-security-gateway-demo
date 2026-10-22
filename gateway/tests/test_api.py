from __future__ import annotations

from fastapi.testclient import TestClient

from app.dependencies import get_database
from app.main import app


def test_events_can_be_cleared_for_demo_rehearsal(pipeline) -> None:
    app.dependency_overrides[get_database] = lambda: pipeline.audit.database
    try:
        client = TestClient(app)
        pipeline.audit.database.insert(
            {
                "timestamp": "2026-08-12T00:00:00+00:00",
                "user": "demo-user",
                "direction": "REQUEST",
                "classification": "SAFE",
                "category": "SAFE",
                "risk": "LOW",
                "action": "ALLOW",
                "reason": "Demo event",
                "detector": "llama_guard_mock",
                "latency_ms": 1,
                "request_preview": "[CONTENT OMITTED — LLAMA GUARD CLASSIFIER DEMO]",
                "response_preview": None,
            }
        )
        assert client.get("/events").json()
        response = client.delete("/events")
        assert response.status_code == 204
        assert client.get("/events").json() == []
    finally:
        app.dependency_overrides.clear()
