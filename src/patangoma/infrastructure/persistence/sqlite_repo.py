"""SQLite repository implementations for persistent library data, audit journals, and jobs."""

from __future__ import annotations

import contextlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from patangoma.domain.exceptions import RepositoryError
from patangoma.domain.models import (
    AuditRecord,
    JobDescriptor,
    JobProgress,
    JobStatus,
)


class SQLiteAuditRepository:
    """SQLite repository for transactional audit records."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with contextlib.suppress(OSError):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_log (
                        operation_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        checksum_before TEXT NOT NULL,
                        checksum_after TEXT NOT NULL,
                        backup_tags TEXT NOT NULL,
                        applied_tags TEXT NOT NULL
                    )
                    """
                )
        finally:
            conn.close()

    def record(self, entry: AuditRecord) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO audit_log (
                        operation_id, timestamp, file_path, checksum_before,
                        checksum_after, backup_tags, applied_tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.operation_id,
                        entry.timestamp.isoformat(),
                        entry.file_path,
                        entry.checksum_before,
                        entry.checksum_after,
                        json.dumps(entry.backup_tags, default=str),
                        json.dumps(entry.applied_tags, default=str),
                    ),
                )
        except sqlite3.Error as e:
            raise RepositoryError(
                "Failed to record audit entry in database", str(e)
            ) from e
        finally:
            conn.close()

    def get_history(
        self, file_path: str | None = None, limit: int = 100
    ) -> list[AuditRecord]:
        conn = self._get_connection()
        try:
            if file_path:
                cursor = conn.execute(
                    """
                    SELECT * FROM audit_log
                    WHERE file_path = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (file_path, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM audit_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            records: list[AuditRecord] = []
            for row in cursor.fetchall():
                records.append(
                    AuditRecord(
                        operation_id=row["operation_id"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        file_path=row["file_path"],
                        checksum_before=row["checksum_before"],
                        checksum_after=row["checksum_after"],
                        backup_tags=json.loads(row["backup_tags"]),
                        applied_tags=json.loads(row["applied_tags"]),
                    )
                )
            return records
        finally:
            conn.close()

    def get_by_operation_id(self, operation_id: str) -> AuditRecord | None:
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM audit_log WHERE operation_id = ?",
                (operation_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return AuditRecord(
                operation_id=row["operation_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                file_path=row["file_path"],
                checksum_before=row["checksum_before"],
                checksum_after=row["checksum_after"],
                backup_tags=json.loads(row["backup_tags"]),
                applied_tags=json.loads(row["applied_tags"]),
            )
        finally:
            conn.close()


class SQLiteJobRepository:
    """SQLite repository for persisting background job state."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with contextlib.suppress(OSError):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        status TEXT NOT NULL,
                        progress_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT,
                        error_message TEXT,
                        result_summary TEXT
                    )
                    """
                )
        finally:
            conn.close()

    def save(self, job: JobDescriptor) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO jobs (
                        job_id, name, operation, status, progress_json,
                        created_at, started_at, completed_at, error_message, result_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(job_id) DO UPDATE SET
                        status=excluded.status,
                        progress_json=excluded.progress_json,
                        started_at=excluded.started_at,
                        completed_at=excluded.completed_at,
                        error_message=excluded.error_message,
                        result_summary=excluded.result_summary
                    """,
                    (
                        job.job_id,
                        job.name,
                        job.operation,
                        job.status.value,
                        job.progress.model_dump_json(),
                        job.created_at.isoformat(),
                        job.started_at.isoformat() if job.started_at else None,
                        job.completed_at.isoformat() if job.completed_at else None,
                        job.error_message,
                        json.dumps(job.result_summary, default=str),
                    ),
                )
        except sqlite3.Error as e:
            raise RepositoryError("Failed to save job in database", str(e)) from e
        finally:
            conn.close()

    def get_by_id(self, job_id: str) -> JobDescriptor | None:
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_job(row)
        finally:
            conn.close()

    def list_all(self, limit: int = 100) -> list[JobDescriptor]:
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            return [self._row_to_job(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def _row_to_job(self, row: sqlite3.Row) -> JobDescriptor:
        prog_data = json.loads(row["progress_json"])
        return JobDescriptor(
            job_id=row["job_id"],
            name=row["name"],
            operation=row["operation"],
            status=JobStatus(row["status"]),
            progress=JobProgress(**prog_data),
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"])
            if row["started_at"]
            else None,
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
            error_message=row["error_message"],
            result_summary=json.loads(row["result_summary"] or "{}"),
        )
