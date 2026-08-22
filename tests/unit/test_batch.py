"""Unit tests for BatchService."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from patangoma.domain.models import ConfidenceLevel, MetadataCandidate
from patangoma.services.batch import BatchService
from tests.helpers.audio_factory import create_minimal_mp3


def test_batch_service_generate_and_apply(tmp_path: Path):
    music_dir = tmp_path / "music"
    music_dir.mkdir()

    # Track 1
    create_minimal_mp3(
        music_dir / "track1.mp3",
        {"title": "Calm Down", "artist": "Rema", "album": "Raves & Roses"},
    )
    # Track 2
    create_minimal_mp3(
        music_dir / "track2.mp3",
        {"title": "Ku Lo Sa", "artist": "Oxlade"},
    )

    batch_service = BatchService()

    cand1 = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="rec-1",
        title="Calm Down",
        artists=["Rema"],
        album="Raves & Roses",
        year=2022,
    )
    cand2 = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="rec-2",
        title="Ku Lo Sa",
        artists=["Oxlade"],
        album="Ku Lo Sa - Single",
        year=2022,
    )

    def mock_search(query):
        if "Calm Down" in (query.title or ""):
            return [cand1]
        elif "Ku Lo Sa" in (query.title or ""):
            return [cand2]
        return []

    with patch(
        "patangoma.providers.musicbrainz.MusicBrainzProvider.search_tracks",
        side_effect=mock_search,
    ):
        batch_plan = batch_service.generate_batch_plan(
            music_dir,
            provider_name="musicbrainz",
            min_confidence=ConfidenceLevel.MEDIUM,
        )

        assert batch_plan.total_files == 2
        assert len(batch_plan.matched_plans) == 2

        # Export & Load Batch Plan
        plan_file = tmp_path / "batch.json"
        batch_service.export_batch_plan(batch_plan, plan_file)
        loaded = batch_service.load_batch_plan(plan_file)
        assert len(loaded.matched_plans) == 2

        # Dry run apply
        dry_records = batch_service.apply_batch_plan(batch_plan, dry_run=True)
        assert len(dry_records) == 0

        # Real apply
        real_records = batch_service.apply_batch_plan(batch_plan, dry_run=False)
        assert len(real_records) == 2
