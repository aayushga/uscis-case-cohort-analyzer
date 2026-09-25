"""Local SQLite storage. The database path is gitignored by default."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    receipt_number TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    form_type TEXT,
    status_text TEXT,
    submitted_date TEXT,
    modified_date TEXT,
    raw_json TEXT NOT NULL,
    PRIMARY KEY (receipt_number, observed_at)
);
CREATE INDEX IF NOT EXISTS observations_form_status
ON observations(form_type, status_text);
"""


class CaseStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.executescript(SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def save(self, payload: dict[str, Any]) -> None:
        case = payload["case_status"]
        observed = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """INSERT INTO observations
               (receipt_number, observed_at, form_type, status_text,
                submitted_date, modified_date, raw_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                case.get("receiptNumber"),
                observed,
                case.get("formType"),
                case.get("current_case_status_text_en"),
                case.get("submittedDate"),
                case.get("modifiedDate"),
                json.dumps(payload, separators=(",", ":")),
            ),
        )
        self.connection.commit()

    def summary(self, form_type: str | None = None) -> Iterable[tuple[str, int]]:
        query = """
            WITH latest AS (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY receipt_number ORDER BY observed_at DESC
                ) AS row_num
                FROM observations
            )
            SELECT COALESCE(status_text, 'Unknown'), COUNT(*)
            FROM latest WHERE row_num = 1
        """
        parameters: tuple[str, ...] = ()
        if form_type:
            query += " AND form_type = ?"
            parameters = (form_type,)
        query += " GROUP BY status_text ORDER BY COUNT(*) DESC, status_text"
        return self.connection.execute(query, parameters).fetchall()

