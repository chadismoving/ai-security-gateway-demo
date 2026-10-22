from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class AuditDatabase:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self.available = False

    def initialize(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS security_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        user TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        classification TEXT NOT NULL,
                        category TEXT,
                        risk TEXT NOT NULL,
                        action TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        detector TEXT NOT NULL,
                        latency_ms INTEGER NOT NULL,
                        request_preview TEXT,
                        response_preview TEXT
                    )
                    """
                )
            self.available = True
        except sqlite3.Error as exc:
            self.available = False
            logger.error("Audit database unavailable; requests will continue without persistence: %s", exc)

    def insert(self, values: dict[str, Any]) -> int | None:
        if not self.available:
            return None
        try:
            with self._lock, self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO security_events (
                        timestamp, user, direction, classification, category,
                        risk, action, reason, detector, latency_ms,
                        request_preview, response_preview
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        values["timestamp"],
                        values["user"],
                        values["direction"],
                        values["classification"],
                        values.get("category"),
                        values["risk"],
                        values["action"],
                        values["reason"],
                        values["detector"],
                        values["latency_ms"],
                        values.get("request_preview"),
                        values.get("response_preview"),
                    ),
                )
                return int(cursor.lastrowid)
        except sqlite3.Error as exc:
            logger.error("Could not write security event: %s", exc)
            return None

    def recent(self, limit: int) -> list[dict[str, Any]]:
        if not self.available:
            return []
        try:
            with self._connect() as connection:
                connection.row_factory = sqlite3.Row
                rows = connection.execute(
                    "SELECT * FROM security_events ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as exc:
            logger.error("Could not read security events: %s", exc)
            return []

    def clear(self) -> None:
        if not self.available:
            return
        try:
            with self._lock, self._connect() as connection:
                connection.execute("DELETE FROM security_events")
        except sqlite3.Error as exc:
            logger.error("Could not clear security events: %s", exc)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)
