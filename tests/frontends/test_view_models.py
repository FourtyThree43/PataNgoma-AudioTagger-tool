"""Unit tests for presentation layer ViewModels and frontends."""

from __future__ import annotations

from pathlib import Path

from patangoma.bootstrap.application import create_application
from patangoma.domain.models import MetadataCandidate
from patangoma.frontends.gui.view_models import (
    DiagnosticsViewModel,
    JobMonitorViewModel,
    LibraryViewModel,
    TagEditorViewModel,
)
from tests.helpers.audio_factory import create_minimal_mp3


def test_library_view_model(tmp_path: Path):
    """Test LibraryViewModel browsing, filtering, and selection."""
    create_minimal_mp3(
        tmp_path / "song1.mp3",
        {"title": "Track One", "artist": "Artist Alpha", "album": "Album A"},
    )
    create_minimal_mp3(
        tmp_path / "song2.mp3",
        {"title": "Track Two", "artist": "Artist Beta", "album": "Album B"},
    )

    app = create_application(audit_db_path=tmp_path / "audit.db")
    vm = LibraryViewModel(app=app)

    loaded_count = vm.load_directory(tmp_path)
    assert loaded_count == 2
    assert vm.selected_track is not None
    assert vm.selected_track.title == "Track One"

    # Filter
    vm.filter_query = "Beta"
    assert len(vm.filtered_tracks) == 1
    assert vm.filtered_tracks[0].artist == "Artist Beta"


def test_tag_editor_view_model(tmp_path: Path):
    """Test TagEditorViewModel candidate matching and plan generation."""
    f = tmp_path / "edit.mp3"
    create_minimal_mp3(
        f,
        {"title": "Old Name", "artist": "Old Artist", "album": "Old Album"},
    )

    app = create_application(audit_db_path=tmp_path / "audit.db")
    meta = app.read_metadata(f)

    vm = TagEditorViewModel(app=app, track=meta)
    vm.selected_candidate = MetadataCandidate(
        provider_name="spotify",
        provider_id="spot-1",
        title="New Name",
        artists=["New Artist"],
        album="New Album",
    )

    plan = vm.generate_plan()
    assert plan is not None
    assert plan.has_changes is True

    updated = vm.apply_plan(dry_run=False)
    assert updated is not None
    assert updated.title == "New Name"


def test_job_and_diagnostics_view_models(tmp_path: Path):
    """Test JobMonitorViewModel and DiagnosticsViewModel."""
    app = create_application(audit_db_path=tmp_path / "audit.db")

    jobs_vm = JobMonitorViewModel(app=app)
    app.jobs.create_job("Test Scan", "SCAN")
    jobs = jobs_vm.refresh()
    assert len(jobs) >= 1
    assert jobs[0].name == "Test Scan"

    diag_vm = DiagnosticsViewModel(app=app)
    diag_vm.refresh()
    assert hasattr(diag_vm.diagnostics, "checks")
    assert len(diag_vm.diagnostics.checks) > 0
    assert "musicbrainz" in diag_vm.plugin_health


def test_tui_screen_model(tmp_path: Path):
    """Test TUIScreenModel headless execution and controller lifecycle."""
    from patangoma.frontends.tui.screens import TUIScreenModel

    song_path = tmp_path / "tui_song.mp3"
    create_minimal_mp3(
        song_path,
        {"title": "TUI Title", "artist": "TUI Artist", "album": "TUI Album"},
    )

    app = create_application(audit_db_path=tmp_path / "audit.db")
    tui_model = TUIScreenModel(app)

    count = tui_model.scan_directory(tmp_path)
    assert count == 1
    assert tui_model.selected_track is not None
    assert tui_model.selected_track.title == "TUI Title"

    cand = MetadataCandidate(
        provider_name="deezer",
        provider_id="dz-101",
        title="Enhanced TUI Title",
        artists=["Enhanced Artist"],
        album="Enhanced Album",
    )
    plan = tui_model.plan_candidate(cand)
    assert plan is not None
    assert plan.provider_name == "deezer"

    updated = tui_model.apply_plan(dry_run=False)
    assert updated is not None
    assert updated.title == "Enhanced TUI Title"

    diag = tui_model.get_diagnostics()
    assert "doctor" in diag
    assert "plugins" in diag


def test_batch_and_rollback_view_models(tmp_path: Path):
    """Test BatchViewModel and RollbackViewModel execution headlessly."""
    from patangoma.frontends.gui.view_models import BatchViewModel, RollbackViewModel

    audio_file = tmp_path / "batch_song.mp3"
    create_minimal_mp3(
        audio_file,
        {"title": "Before Batch", "artist": "Batch Artist", "album": "Batch Album"},
    )

    app = create_application(audit_db_path=tmp_path / "audit.db")

    # Batch VM
    batch_vm = BatchViewModel(app=app)
    # Manually create a plan to test apply_selected
    cand = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="mb-batch-1",
        title="After Batch",
        artists=["Batch Artist"],
        album="New Album",
    )
    plan = app.create_tag_plan(audio_file, cand)
    batch_vm.plans = [plan]
    batch_vm.selected_plan_indices = {0}

    results = batch_vm.apply_selected(dry_run=False)
    assert len(results) == 1
    assert results[0].title == "After Batch"

    # Rollback VM
    rollback_vm = RollbackViewModel(app=app)
    records = rollback_vm.load_history(file_path=str(audio_file.resolve()))
    assert len(records) >= 1

    rolled_back = rollback_vm.rollback(file_path=str(audio_file.resolve()))
    assert rolled_back.title == "Before Batch"


def test_plugins_view_model(tmp_path: Path):
    """Test PluginsViewModel enable, disable, and refresh operations."""
    from patangoma.frontends.gui.view_models import PluginsViewModel

    app = create_application(audit_db_path=tmp_path / "audit.db")
    pvm = PluginsViewModel(app=app)
    pvm.refresh()

    assert len(pvm.plugins) >= 7
    assert "musicbrainz" in pvm.health_status

    pvm.disable_plugin("musicbrainz")
    assert app.plugins.get("musicbrainz") is None

    pvm.enable_plugin("musicbrainz")
    assert app.plugins.get("musicbrainz") is not None
