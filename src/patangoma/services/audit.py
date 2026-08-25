"""Audit journal and rollback service for safe reversible metadata operations."""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import platformdirs

from patangoma.domain.exceptions import AudioFileNotFoundError, RollbackError
from patangoma.domain.models import AuditRecord, FieldDiffStatus, TagPlan, TrackMetadata
from patangoma.services.audio_backend import AudioBackend, compute_file_checksum


def default_audit_db_path() -> Path:
    """Return default path to user audit database conforming to OS standards via platformdirs."""
    if env_home := os.getenv("PATANGOMA_HOME"):
        return Path(env_home) / "audit.db"
    try:
        data_dir = Path(platformdirs.user_data_dir("patangoma", appauthor=False))
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "audit.db"
    except OSError:
        import tempfile

        tmp = Path(tempfile.gettempdir()) / ".patangoma"
        tmp.mkdir(parents=True, exist_ok=True)
        return tmp / "audit.db"


class AuditJournal:
    """Persistent SQLite-backed audit log for recording changes and executing rollbacks."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else default_audit_db_path()
        self._initialized = False

    def _get_connection(self) -> sqlite3.Connection:
        if not self._initialized:
            with contextlib.suppress(OSError):
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
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
                self._initialized = True
            except sqlite3.OperationalError:
                # In read-only or restricted environments
                pass
            return conn
        return sqlite3.connect(str(self.db_path))

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

    def list_history(
        self,
        file_path: str | Path | None = None,
        limit: int = 50,
    ) -> list[AuditRecord]:
        """List past audit records in reverse chronological order with optional path filtering."""
        records: list[AuditRecord] = []
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if file_path:
                norm_prefix = str(file_path)
                cursor.execute(
                    """
                    SELECT operation_id, timestamp, file_path, checksum_before,
                           checksum_after, backup_tags, applied_tags
                    FROM audit_log
                    WHERE file_path = ? OR file_path LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (norm_prefix, f"{norm_prefix}%", limit),
                )
            else:
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

    def rollback_latest(self, backend: AudioBackend) -> TrackMetadata:
        """Rollback the single most recent operation in the audit log."""
        records = self.list_history(limit=1)
        if not records:
            raise RollbackError("No operations found in audit log to rollback.")
        return self.rollback_operation(records[0].operation_id, backend)

    def rollback_path(
        self,
        file_path: str | Path,
        backend: AudioBackend,
    ) -> list[TrackMetadata]:
        """Rollback all recorded operations targeting the given file or directory."""
        records = self.list_history(file_path=file_path, limit=100)
        if not records:
            raise RollbackError(f"No audit records found for path '{file_path}'.")

        restored_tracks: list[TrackMetadata] = []
        # Roll back in reverse chronological order
        for rec in records:
            target = Path(rec.file_path)
            if target.exists():
                restored = backend.write_tags(target, rec.backup_tags, dry_run=False)
                restored_tracks.append(restored)

        return restored_tracks

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

    def export_history_csv(
        self,
        output_path: str | Path,
        limit: int = 500,
    ) -> Path:
        """Export audit history records to a CSV file."""
        import csv

        records = self.list_history(limit=limit)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Operation ID",
                    "Timestamp",
                    "File Path",
                    "Checksum Before",
                    "Checksum After",
                    "Modified Tags",
                ]
            )
            for rec in records:
                mod_keys = (
                    ", ".join(rec.applied_tags.keys()) if rec.applied_tags else ""
                )
                writer.writerow(
                    [
                        rec.operation_id,
                        rec.timestamp.isoformat(),
                        rec.file_path,
                        rec.checksum_before,
                        rec.checksum_after,
                        mod_keys,
                    ]
                )
        return out

    def export_history_html(
        self,
        output_path: str | Path,
        limit: int = 500,
    ) -> Path:
        """Export audit history records to a formatted HTML report."""
        records = self.list_history(limit=limit)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        for rec in records:
            mod_keys = (
                ", ".join(rec.applied_tags.keys()) if rec.applied_tags else "None"
            )
            rows.append(
                f"<tr>"
                f"<td><code>{rec.operation_id[:8]}...</code></td>"
                f"<td>{rec.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>"
                f"<td>{Path(rec.file_path).name}</td>"
                f"<td>{mod_keys}</td>"
                f"<td><code>{rec.checksum_after[:12]}...</code></td>"
                f"</tr>"
            )

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PataNgoma Audit Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #0f172a; color: #e2e8f0; }}
        h1 {{ color: #38bdf8; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #0284c7; color: white; }}
        tr:hover {{ background: #334155; }}
        code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #a5f3fc; }}
    </style>
</head>
<body>
    <h1>PataNgoma Audit Trail Report</h1>
    <p>Total Records: {len(records)}</p>
    <table>
        <thead>
            <tr>
                <th>Operation ID</th>
                <th>Timestamp</th>
                <th>File Name</th>
                <th>Modified Fields</th>
                <th>Checksum Post-Mutation</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows) if rows else "<tr><td colspan='5'>No records found</td></tr>"}
        </tbody>
    </table>
</body>
</html>"""
        out.write_text(html, encoding="utf-8")
        return out
