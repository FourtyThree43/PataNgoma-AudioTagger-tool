"""Unit tests for AuditJournal HTML and CSV exporters."""

from __future__ import annotations

from pathlib import Path

from patangoma.domain.models import (
    ConfidenceLevel,
    FieldDiffStatus,
    TagFieldDiff,
    TagPlan,
)
from patangoma.services.audio_backend import AudioBackend, compute_file_checksum
from patangoma.services.audit import AuditJournal


def test_audit_export_csv_and_html(mp3_complete: Path, tmp_path: Path):
    db_file = tmp_path / "export_test.db"
    journal = AuditJournal(db_path=db_file)
    backend = AudioBackend()

    before = backend.read_metadata(mp3_complete)
    plan = TagPlan(
        file_path=str(mp3_complete),
        provider_name="itunes",
        provider_id="itunes-exp",
        confidence=ConfidenceLevel.EXACT,
        total_score=1.0,
        checksum_pre=compute_file_checksum(mp3_complete),
        diffs=[
            TagFieldDiff(
                field_name="title",
                old_value=before.title,
                new_value="Export Title",
                status=FieldDiffStatus.MODIFIED,
            )
        ],
    )
    after = backend.write_tags(mp3_complete, {"title": "Export Title"})
    journal.record_apply(plan, before, after)

    # Export CSV
    csv_out = tmp_path / "report.csv"
    res_csv = journal.export_history_csv(csv_out)
    assert res_csv.exists()
    content_csv = res_csv.read_text(encoding="utf-8")
    assert "Export Title" in content_csv or "title" in content_csv

    # Export HTML
    html_out = tmp_path / "report.html"
    res_html = journal.export_history_html(html_out)
    assert res_html.exists()
    content_html = res_html.read_text(encoding="utf-8")
    assert "PataNgoma Audit Trail Report" in content_html
