"""Audit journal and rollback service for safe reversible metadata operations."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from patangoma.domain.exceptions import AudioFileNotFoundError, RollbackError
from patangoma.domain.models import AuditRecord, FieldDiffStatus, TagPlan, TrackMetadata
from patangoma.services.audio_backend import AudioBackend, compute_file_checksum


def default_audit_db_path() -> Path:
    """Return default path to user audit database."""
    base = Path(os.getenv("PATANGOMA_HOME", Path.home() / ".patangoma"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "audit.db"


class AuditJournal:
    """Persistent SQLite-backed audit log for recording changes and executing rollbacks."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else default_audit_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
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

    def record_apply(
        self,
        plan: TagPlan,
        track_before: TrackMetadata,
        track_after: TrackMetadata,
    ) -> AuditRecord:
        """Create and store an audit log record for an applied plan."""
        op_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc)
        checksum_after = compute_file_checksum(track_after.file_path)

        # Collect only the tags that changed
        applied: dict[str, Any] = {}
        for diff in plan.diffs:
            if diff.status != FieldDiffStatus.UNCHANGED:
                applied[diff.field_name] = diff.new_value

        record = AuditRecord(
            operation_id=op_id,
            timestamp=ts,
            file_path=plan.file_path,
            checksum_before=plan.checksum_pre,
            checksum_after=checksum_after,
            backup_tags=track_before.to_tag_dict(),
            applied_tags=applied,
        )

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
                        record.operation_id,
                        record.timestamp.isoformat(),
                        record.file_path,
                        record.checksum_before,
                        record.checksum_after,
                        json.dumps(record.backup_tags, default=str),
                        json.dumps(record.applied_tags, default=str),
                    ),
                )
        finally:
            conn.close()

        return record

    def list_history(self, limit: int = 50) -> list[AuditRecord]:
        """List past audit records in reverse chronological order."""
        records: list[AuditRecord] = []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT operation_id, timestamp, file_path, checksum_before,
                       checksum_after, backup_tags, applied_tags
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            for row in cursor.fetchall():
                records.append(
                    AuditRecord(
                        operation_id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        file_path=row[2],
                        checksum_before=row[3],
                        checksum_after=row[4],
                        backup_tags=json.loads(row[5]),
                        applied_tags=json.loads(row[6]),
                    )
                )
        finally:
            conn.close()
        return records

    def get_record(self, operation_id: str) -> AuditRecord | None:
        """Fetch audit record by operation ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT operation_id, timestamp, file_path, checksum_before,
                       checksum_after, backup_tags, applied_tags
                FROM audit_log
                WHERE operation_id = ?
                """,
                (operation_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return AuditRecord(
                operation_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                file_path=row[2],
                checksum_before=row[3],
                checksum_after=row[4],
                backup_tags=json.loads(row[5]),
                applied_tags=json.loads(row[6]),
            )
        finally:
            conn.close()

    def rollback_operation(
        self,
        operation_id: str,
        backend: AudioBackend,
    ) -> TrackMetadata:
        """Revert audio file metadata tags to their state prior to the operation."""
        record = self.get_record(operation_id)
        if not record:
            raise RollbackError(
                f"Operation ID '{operation_id}' not found in audit history."
            )

        target_path = Path(record.file_path)
        if not target_path.exists():
            raise AudioFileNotFoundError(
                "File to rollback does not exist on disk", str(target_path)
            )

        # Re-apply backup tags
        try:
            restored = backend.write_tags(
                target_path, record.backup_tags, dry_run=False
            )
            return restored
        except Exception as e:
            raise RollbackError(
                f"Failed to rollback operation {operation_id}", str(e)
            ) from e
