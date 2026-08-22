"""Unit tests for pure domain models and exceptions."""

from __future__ import annotations

import datetime

from patangoma.domain.exceptions import (
    AudioFileNotFoundError,
)
from patangoma.domain.models import (
    ConfidenceLevel,
    FieldDiffStatus,
    MetadataCandidate,
    TagFieldDiff,
    TagPlan,
    TrackMetadata,
)


def test_track_metadata_to_tag_dict():
    meta = TrackMetadata(
        file_path="/path/to/song.mp3",
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        year=2023,
        track_number=5,
        track_total=12,
        disc_number=1,
    )
    tag_dict = meta.to_tag_dict()
    assert tag_dict["title"] == "Test Song"
    assert tag_dict["artist"] == "Test Artist"
    assert tag_dict["album"] == "Test Album"
    assert tag_dict["year"] == 2023
    assert tag_dict["track"] == 5
    assert tag_dict["tracktotal"] == 12
    assert tag_dict["disc"] == 1


def test_metadata_candidate_to_tag_dict():
    candidate = MetadataCandidate(
        provider_name="spotify",
        provider_id="spot-123",
        title="Candidate Title",
        artists=["Primary Artist", "Featured Artist"],
        album="Candidate Album",
        year=2024,
        release_date=datetime.date(2024, 5, 20),
        track_number=2,
    )
    assert candidate.primary_artist == "Primary Artist"
    tags = candidate.to_tag_dict()
    assert tags["title"] == "Candidate Title"
    assert tags["artist"] == "Primary Artist"
    assert tags["album"] == "Candidate Album"
    assert tags["year"] == 2024
    assert tags["track"] == 2


def test_tag_plan_has_changes():
    plan_with_diffs = TagPlan(
        file_path="/path/to/song.mp3",
        provider_name="musicbrainz",
        provider_id="mb-1",
        confidence=ConfidenceLevel.HIGH,
        total_score=0.88,
        checksum_pre="abc123hash",
        diffs=[
            TagFieldDiff(
                field_name="title",
                old_value="Song Old",
                new_value="Song New",
                status=FieldDiffStatus.MODIFIED,
            )
        ],
    )
    assert plan_with_diffs.has_changes is True

    plan_no_diffs = TagPlan(
        file_path="/path/to/song.mp3",
        provider_name="musicbrainz",
        provider_id="mb-1",
        confidence=ConfidenceLevel.EXACT,
        total_score=1.0,
        checksum_pre="abc123hash",
        diffs=[
            TagFieldDiff(
                field_name="title",
                old_value="Same Title",
                new_value="Same Title",
                status=FieldDiffStatus.UNCHANGED,
            )
        ],
    )
    assert plan_no_diffs.has_changes is False


def test_domain_exceptions_formatting():
    err = AudioFileNotFoundError("File not found", "/tmp/nonexistent.mp3")
    assert str(err) == "File not found (/tmp/nonexistent.mp3)"
