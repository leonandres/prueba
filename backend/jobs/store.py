from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class JobRecord:
    id: str
    input_path: str
    description: Optional[str]
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    output_pdf: Optional[str] = None
    preview_html: Optional[str] = None
    metrics: Optional[dict] = None
    error: Optional[str] = None
    attempts: int = 0


class JobStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def initialize(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    input_path TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    output_pdf TEXT,
                    preview_html TEXT,
                    metrics TEXT,
                    error TEXT,
                    attempts INTEGER DEFAULT 0
                )
                """
            )
            conn.commit()

    def create(self, record: JobRecord):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO jobs (id, input_path, description, status, created_at, updated_at, output_pdf, preview_html, metrics, error, attempts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.input_path,
                    record.description,
                    record.status.value,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                    record.output_pdf,
                    record.preview_html,
                    json.dumps(record.metrics) if record.metrics else None,
                    record.error,
                    record.attempts,
                ),
            )
            conn.commit()

    def update(self, record: JobRecord):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE jobs SET status=?, updated_at=?, output_pdf=?, preview_html=?, metrics=?, error=?, attempts=?
                WHERE id=?
                """,
                (
                    record.status.value,
                    record.updated_at.isoformat(),
                    record.output_pdf,
                    record.preview_html,
                    json.dumps(record.metrics) if record.metrics else None,
                    record.error,
                    record.attempts,
                    record.id,
                ),
            )
            conn.commit()

    def get(self, job_id: str) -> Optional[JobRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def list_recent(self, limit: int = 100) -> List[JobRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            id=row["id"],
            input_path=row["input_path"],
            description=row["description"],
            status=JobStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            output_pdf=row["output_pdf"],
            preview_html=row["preview_html"],
            metrics=json.loads(row["metrics"]) if row["metrics"] else None,
            error=row["error"],
            attempts=row["attempts"],
        )

