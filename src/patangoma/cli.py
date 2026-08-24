#!/usr/bin/env python3
"""Modern CLI interface for PataNgoma AudioTagger."""

from __future__ import annotations

import json
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator
from mediafile import MediaFile
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from patangoma.domain.exceptions import AudioFileError, PataNgomaError, ProviderError
from patangoma.domain.models import (
    ConfidenceLevel,
    FieldDiffStatus,
    MetadataCandidate,
    QueryParameters,
    TrackMetadata,
)
from patangoma.matching.matcher import MatchingEngine
from patangoma.providers.registry import get_provider
from patangoma.services.ai_reasoner import MetadataReasoner
from patangoma.services.audio_backend import AudioBackend
from patangoma.services.audit import AuditJournal
from patangoma.services.batch import BatchService
from patangoma.services.doctor import run_diagnostics
from patangoma.services.planner import PlanEngine
from patangoma.services.scanner import LibraryScanner

console = Console()
backend = AudioBackend()
planner = PlanEngine()
audit_journal = AuditJournal()
matching_engine = MatchingEngine()
batch_service = BatchService(backend, planner, matching_engine, audit_journal)
reasoner = MetadataReasoner()


def get_app_info() -> tuple[str, str]:
    """Get application name and version."""
    app_name = "PataNgoma"
    try:
        app_version = version("patangoma")
    except PackageNotFoundError:
        app_version = "1.0.0"
    return app_name, app_version


def app_info() -> None:
    """Print welcome header."""
    app_name, app_version = get_app_info()
    console.print(
        Panel.fit(
            f"[bold red]♥[/bold red] [bold yellow]{app_name}[/bold yellow] - [bold white]v{app_version}[/bold white] [bold red]♥[/bold red]\n"
            "[cyan]Deterministic Music Metadata Intelligence Platform[/cyan]",
            border_style="red",
        )
    )


# -------------------------------------------------------------------------
# Modern Commands: scan, inspect, match, plan, apply, rollback, history, doctor, verify
# -------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, dir_okay=True, resolve_path=True),
    help="Path to the audio file or its parent directory",
)
def cli(ctx: click.Context, path: str | None) -> None:
    """PataNgoma AudioTagger CLI."""
    if ctx.invoked_subcommand is None:
        app_info()
        target_path = path or _interactive_select_path()
        ctx.obj = target_path
        if _is_valid_audio(target_path):
            _main_menu(ctx)
        else:
            sys.exit(1)


@cli.command()
@click.argument(
    "path", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
@click.option(
    "--recursive/--no-recursive",
    "-r/-R",
    default=True,
    help="Scan subdirectories recursively",
)
@click.option(
    "--json-out", "--json", is_flag=True, help="Output results in JSON format"
)
def scan(path: str, recursive: bool, json_out: bool) -> None:
    """Scan directory and report library metadata health and duplicates."""
    scanner = LibraryScanner(backend)
    _tracks, summary = scanner.scan_directory(path, recursive=recursive)

    if json_out:
        click.echo(summary.model_dump_json(indent=2))
        return

    table = Table(title=f"Library Scan Summary: {path}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Files Scanned", str(summary.total_files_scanned))
    table.add_row("Valid Audio Files", str(summary.valid_audio_files))
    table.add_row("Corrupt / Unreadable", f"[red]{summary.corrupt_or_unreadable}[/red]")
    table.add_row("Missing Titles", str(summary.missing_title_count))
    table.add_row("Missing Artists", str(summary.missing_artist_count))
    table.add_row("Missing Albums", str(summary.missing_album_count))
    table.add_row("Missing Years", str(summary.missing_year_count))
    table.add_row("Missing Artwork", str(summary.missing_artwork_count))
    table.add_row("Duplicate Sets Found", str(len(summary.duplicate_groups)))

    console.print(table)

    if summary.duplicate_groups:
        dup_table = Table(title="Detected Duplicate Sets", border_style="yellow")
        dup_table.add_column("#", style="dim")
        dup_table.add_column("Duplicate File Paths")
        for i, group in enumerate(summary.duplicate_groups, start=1):
            dup_table.add_row(str(i), "\n".join(group))
        console.print(dup_table)


@cli.command()
@click.argument(
    "file_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    "--json-out", "--json", is_flag=True, help="Output metadata in JSON format"
)
def inspect(file_path: str, json_out: bool) -> None:
    """Inspect metadata and technical properties of an audio file."""
    try:
        meta = backend.read_metadata(file_path)
    except AudioFileError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)

    if json_out:
        click.echo(meta.model_dump_json(indent=2))
        return

    table = Table(title=f"Track Inspection: {Path(file_path).name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    for k, v in meta.model_dump().items():
        if k not in ("file_path", "artists", "genres") and v is not None:
            table.add_row(k, str(v))

    console.print(table)


def _query_candidates(
    track: TrackMetadata, file_path: str, provider_name: str
) -> tuple[list[MetadataCandidate], str]:
    """Query metadata candidates with automatic filename heuristic fallback and multi-provider support."""
    q_title = track.title
    q_artist = track.artist
    q_album = track.album
    display_title = track.title or Path(file_path).name

    # Automatic fallback if title is missing from tags
    if not q_title:
        inf = reasoner.parse_filename(file_path)
        if inf.suggested_title:
            q_title = inf.suggested_title
            display_title = inf.suggested_title
            if not q_artist:
                q_artist = inf.suggested_artist
            console.print(
                f"[cyan]* Inferred title '[bold]{q_title}[/bold]'"
                + (f" by '{q_artist}'" if q_artist else "")
                + " from filename for lookup.[/cyan]"
            )

    norm_prov = provider_name.lower().strip()

    if norm_prov in ("multi", "all"):
        from patangoma.services.aggregator import MetadataAggregator

        agg = MetadataAggregator()
        cands = agg.search_all_providers(
            QueryParameters(
                title=q_title,
                artist=q_artist,
                album=q_album,
                isrc=track.isrc,
            )
        )
        return cands, display_title

    if norm_prov == "acoustid":
        from patangoma.providers.acoustid import (
            find_fpcalc_binary,
            generate_chromaprint,
        )

        fpcalc_bin = find_fpcalc_binary()
        if fpcalc_bin:
            fp_info = generate_chromaprint(file_path)
            if fp_info:
                dur, fp = fp_info
                prov = get_provider("acoustid")
                return (
                    prov.lookup_fingerprint(dur, fp),
                    display_title,
                )

        console.print(
            "[yellow]⚠ fpcalc (Chromaprint) not found on system path. Using metadata text search...[/yellow]"
        )

    prov = get_provider(norm_prov)
    cands = prov.search_tracks(
        QueryParameters(
            title=q_title,
            artist=q_artist,
            album=q_album,
            isrc=track.isrc,
        )
    )
    return cands, display_title


@cli.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
@click.option(
    "--provider",
    "-p",
    default="musicbrainz",
    help="Provider (musicbrainz, itunes, deezer, spotify, discogs, acoustid, multi)",
)
@click.option(
    "--json-out",
    "--json",
    is_flag=True,
    help="Output match results in JSON format",
)
def match(file_path: str, provider: str, json_out: bool) -> None:
    """Search provider and compute explainable match confidence scores."""
    try:
        track = backend.read_metadata(file_path)
    except AudioFileError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)

    try:
        candidates, display_title = _query_candidates(track, file_path, provider)
    except ProviderError as e:
        console.print(f"[bold red]Provider Error:[/bold red] {e}")
        sys.exit(3)

    if not candidates:
        console.print(
            f"[yellow]No candidates found on {provider} for '{display_title}'.[/yellow]"
        )
        return

    results = matching_engine.rank_candidates(track, candidates)

    if json_out:
        click.echo(json.dumps([r.model_dump() for r in results], indent=2, default=str))
        return

    table = Table(title=f"Metadata Matches for '{display_title}' (via {provider})")
    table.add_column("Rank", style="dim")
    table.add_column("Candidate Title", style="cyan")
    table.add_column("Artist", style="green")
    table.add_column("Album", style="magenta")
    table.add_column("Score", style="bold yellow")
    table.add_column("Confidence", style="bold")

    for i, res in enumerate(results, start=1):
        color = (
            "green"
            if res.confidence in (ConfidenceLevel.EXACT, ConfidenceLevel.HIGH)
            else "yellow"
        )
        table.add_row(
            str(i),
            res.candidate.title,
            res.candidate.primary_artist,
            res.candidate.album or "—",
            f"{res.score.total_score * 100:.1f}%",
            f"[{color}]{res.confidence.value}[/{color}]",
        )

    console.print(table)


@cli.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
@click.option(
    "--provider",
    "-p",
    default="musicbrainz",
    help="Provider (musicbrainz, itunes, deezer, spotify, discogs, acoustid, multi)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    help="Path to write the plan JSON file",
)
@click.option("--json-out", "--json", is_flag=True, help="Print plan JSON to stdout")
def plan(file_path: str, provider: str, output: str | None, json_out: bool) -> None:
    """Generate a deterministic mutation plan for an audio file."""
    try:
        track = backend.read_metadata(file_path)
    except AudioFileError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)

    try:
        candidates, display_title = _query_candidates(track, file_path, provider)
    except ProviderError as e:
        console.print(f"[bold red]Provider Error:[/bold red] {e}")
        sys.exit(3)

    if not candidates:
        console.print(
            f"[yellow]No match candidates found on {provider} for '{display_title}'.[/yellow]"
        )
        sys.exit(1)

    best_match = matching_engine.rank_candidates(track, candidates)[0]
    tag_plan = planner.create_plan(
        track=track,
        candidate=best_match.candidate,
        confidence=best_match.confidence,
        total_score=best_match.score.total_score,
    )

    if output:
        out_path = planner.save_plan_file(tag_plan, output)
        console.print(f"[bold green]✓ Plan saved to:[/bold green] {out_path}")

    if json_out or not output:
        click.echo(planner.export_plan_to_json(tag_plan))


@cli.command()
@click.argument(
    "plan_or_file",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
@click.option(
    "--dry-run", is_flag=True, help="Simulate mutation without writing to disk"
)
@click.option(
    "--provider",
    "-p",
    default="musicbrainz",
    help="Provider if passing an audio file directly",
)
@click.option(
    "--json-out",
    "--json",
    is_flag=True,
    help="Output apply result in JSON format",
)
def apply(plan_or_file: str, dry_run: bool, provider: str, json_out: bool) -> None:
    """Apply a plan or best candidate match to an audio file."""
    path = Path(plan_or_file)

    if path.suffix.lower() == ".json":
        # Load from saved plan file
        tag_plan = planner.load_plan_from_json(path.read_text(encoding="utf-8"))
        audio_path = tag_plan.file_path
    else:
        # Match and create plan on the fly
        audio_path = str(path)
        track = backend.read_metadata(audio_path)
        candidates, _ = _query_candidates(track, audio_path, provider)
        if not candidates:
            console.print("[yellow]No candidates found to apply.[/yellow]")
            sys.exit(1)
        best = matching_engine.rank_candidates(track, candidates)[0]
        tag_plan = planner.create_plan(
            track, best.candidate, best.confidence, best.score.total_score
        )

    track_before = backend.read_metadata(audio_path)

    # Collect tags to apply
    updates = {}
    for diff in tag_plan.diffs:
        if diff.status in (FieldDiffStatus.ADDED, FieldDiffStatus.MODIFIED):
            updates[diff.field_name] = diff.new_value

    if dry_run:
        updated = backend.write_tags(audio_path, updates, dry_run=True)
        console.print(
            f"[bold yellow]DRY-RUN:[/bold yellow] Simulated tags on {Path(audio_path).name}"
        )
        if json_out:
            click.echo(updated.model_dump_json(indent=2))
        return

    # Apply mutation and log in audit history
    updated = backend.write_tags(audio_path, updates, dry_run=False)
    audit_rec = audit_journal.record_apply(tag_plan, track_before, updated)

    if json_out:
        click.echo(audit_rec.model_dump_json(indent=2))
        return

    console.print(
        f"[bold green]✓ Successfully applied plan to {Path(audio_path).name}[/bold green]"
    )
    console.print(f"[dim]Operation ID: {audit_rec.operation_id}[/dim]")


@cli.command("plan-dir")
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
@click.option(
    "--provider",
    "-p",
    default="musicbrainz",
    help="Provider (musicbrainz, deezer, spotify)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    help="Path to save batch plan JSON file",
)
@click.option("--json-out", "--json", is_flag=True, help="Output batch plan in JSON")
def plan_dir(directory: str, provider: str, output: str | None, json_out: bool) -> None:
    """Generate a batch mutation plan across an entire directory."""
    batch_plan = batch_service.generate_batch_plan(directory, provider_name=provider)

    if output:
        out_path = batch_service.export_batch_plan(batch_plan, output)
        console.print(f"[bold green]✓ Batch plan saved to:[/bold green] {out_path}")

    if json_out or not output:
        click.echo(batch_plan.model_dump_json(indent=2))


@cli.command("apply-dir")
@click.argument(
    "plan_file", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    "--dry-run", is_flag=True, help="Simulate batch mutation without writing to disk"
)
@click.option(
    "--json-out", "--json", is_flag=True, help="Output applied batch records in JSON"
)
def apply_dir(plan_file: str, dry_run: bool, json_out: bool) -> None:
    """Apply a batch plan across an entire music library."""
    batch_plan = batch_service.load_batch_plan(plan_file)
    records = batch_service.apply_batch_plan(batch_plan, dry_run=dry_run)

    if json_out:
        click.echo(json.dumps([r.model_dump() for r in records], indent=2, default=str))
        return

    if dry_run:
        console.print(
            f"[bold yellow]DRY-RUN:[/bold yellow] Simulated batch tagging for {len(batch_plan.matched_plans)} tracks."
        )
    else:
        console.print(
            f"[bold green]✓ Successfully applied batch plan to {len(records)} tracks.[/bold green]"
        )


@cli.command("reason")
@click.argument(
    "file_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    "--json-out", "--json", is_flag=True, help="Output reasoning in JSON format"
)
def reason_cmd(file_path: str, json_out: bool) -> None:
    """Analyze filename patterns and suggest tag improvements using reasoning heuristics."""
    try:
        track = backend.read_metadata(file_path)
    except AudioFileError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)

    inference = reasoner.parse_filename(Path(file_path).name)
    suggestions = reasoner.suggest_tag_improvements(track)

    if json_out:
        click.echo(
            json.dumps(
                {"inference": inference.model_dump(), "suggestions": suggestions},
                indent=2,
            )
        )
        return

    table = Table(title=f"Filename & Tag Reasoning: {Path(file_path).name}")
    table.add_column("Property", style="cyan")
    table.add_column("Inferred Value", style="green")

    table.add_row("Suggested Title", inference.suggested_title or "—")
    table.add_row("Suggested Artist", inference.suggested_artist or "—")
    table.add_row(
        "Suggested Track #",
        str(inference.suggested_track_number)
        if inference.suggested_track_number
        else "—",
    )
    table.add_row("Heuristic Confidence", inference.confidence)

    console.print(table)

    if suggestions:
        console.print("\n[bold yellow]Suggestions & Potential Fixes:[/bold yellow]")
        for s in suggestions:
            console.print(f" • {s}")


@cli.command()
@click.argument("operation_id", required=False)
@click.option("--latest", is_flag=True, help="Roll back the most recent operation")
@click.option(
    "--path",
    "-p",
    help="Roll back all operations on a specific file or directory",
)
@click.option(
    "--json-out", "--json", is_flag=True, help="Output rollback outcome in JSON"
)
def rollback(
    operation_id: str | None, latest: bool, path: str | None, json_out: bool
) -> None:
    """Roll back audio mutations using Operation ID, --latest, or --path."""
    try:
        if latest:
            restored = audit_journal.rollback_latest(backend)
            if json_out:
                click.echo(restored.model_dump_json(indent=2))
                return
            console.print(
                f"[bold green]✓ Restored tags for {restored.path.name} (latest)[/bold green]"
            )
        elif path:
            restored_list = audit_journal.rollback_path(path, backend)
            if json_out:
                click.echo(
                    json.dumps(
                        [t.model_dump() for t in restored_list],
                        indent=2,
                        default=str,
                    )
                )
                return
            console.print(
                f"[bold green]✓ Restored {len(restored_list)} tracks matching {path}[/bold green]"
            )
        elif operation_id:
            restored = audit_journal.rollback_operation(operation_id, backend)
            if json_out:
                click.echo(restored.model_dump_json(indent=2))
                return
            console.print(
                f"[bold green]✓ Restored tags for {restored.path.name} from operation {operation_id}[/bold green]"
            )
        else:
            console.print(
                "[bold red]Please specify an OPERATION_ID, --latest, or --path.[/bold red]"
            )
            sys.exit(1)
    except PataNgomaError as e:
        console.print(f"[bold red]Rollback failed:[/bold red] {e}")
        sys.exit(1)


@cli.command("demo-library")
@click.argument("directory", type=click.Path())
def demo_library(directory: str) -> None:
    """Generate a sample test music library with valid, missing, and corrupt audio files."""
    from patangoma.services.sample_generator import generate_sample_library

    created = generate_sample_library(directory)
    total = sum(len(files) for files in created.values())
    console.print(
        Panel(
            f"[bold green]✓ Created sample library with {total} test audio files at '{directory}'[/bold green]\n\n"
            f" • Complete: {len(created['complete'])}\n"
            f" • Missing Metadata: {len(created['missing_metadata'])}\n"
            f" • Unicode/Multilingual: {len(created['unicode'])}\n"
            f" • Corrupt Header: {len(created['corrupt'])}",
            title="Sample Library Generator",
        )
    )


@cli.command("check-file")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--json-out", "--json", is_flag=True, help="Output report in JSON")
def check_file(file_path: str, json_out: bool) -> None:
    """Pre-flight file header integrity and corruption inspection."""
    from patangoma.services.validator import FileValidator

    report = FileValidator.validate_file(file_path)
    if json_out:
        click.echo(report.model_dump_json(indent=2))
        return

    table = Table(title=f"File Integrity: {Path(file_path).name}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green" if report.is_readable else "red")

    table.add_row("Format", report.detected_format.upper())
    table.add_row("Size", f"{report.file_size_bytes} bytes")
    table.add_row("Header Valid", "✓ Yes" if report.header_valid else "✗ No")
    table.add_row("Audio Readable", "✓ Yes" if report.is_readable else "✗ No")
    if report.error_message:
        table.add_row("Error", f"[red]{report.error_message}[/red]")

    console.print(table)


@cli.command()
@click.option("--limit", "-n", default=20, help="Maximum history records to display")
@click.option("--json-out", "--json", is_flag=True, help="Output history in JSON")
def history(limit: int, json_out: bool) -> None:
    """List recent metadata mutations from the audit journal."""
    records = audit_journal.list_history(limit=limit)

    if json_out:
        click.echo(json.dumps([r.model_dump() for r in records], indent=2, default=str))
        return

    if not records:
        console.print("[dim]No audit history records found.[/dim]")
        return

    table = Table(title="Audit Log & Mutation History")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Operation ID", style="dim")
    table.add_column("File Name", style="green")
    table.add_column("Modified Fields", style="yellow")

    for rec in records:
        table.add_row(
            rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            rec.operation_id[:8] + "...",
            Path(rec.file_path).name,
            ", ".join(rec.applied_tags.keys()) if rec.applied_tags else "None",
        )

    console.print(table)


@cli.command("export-audit")
@click.argument("output_file", type=click.Path())
@click.option(
    "--format",
    "-f",
    type=click.Choice(["html", "csv"], case_sensitive=False),
    default="html",
    help="Export format (html or csv)",
)
@click.option("--limit", "-n", default=500, help="Maximum records to export")
def export_audit(output_file: str, format: str, limit: int) -> None:
    """Export audit log history to HTML or CSV report."""
    if format.lower() == "csv":
        out = audit_journal.export_history_csv(output_file, limit=limit)
    else:
        out = audit_journal.export_history_html(output_file, limit=limit)
    console.print(
        f"[bold green]✓ Exported {format.upper()} audit report to '{out.resolve()}'[/bold green]"
    )


@cli.command("duplicates")
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
@click.option("--json-out", "--json", is_flag=True, help="Output duplicates in JSON")
def duplicates(directory: str, json_out: bool) -> None:
    """Detect duplicate audio files across formats, bitrates, and subdirectories."""
    from patangoma.services.duplicates import DuplicateDetector

    scanner = LibraryScanner(backend)
    tracks, _ = scanner.scan_directory(directory)
    dup_groups = DuplicateDetector.find_duplicates(tracks)

    if json_out:
        click.echo(
            json.dumps([g.model_dump() for g in dup_groups], indent=2, default=str)
        )
        return

    if not dup_groups:
        console.print(
            f"[bold green]✓ No duplicate audio files detected in {directory}[/bold green]"
        )
        return

    console.print(
        f"[bold yellow]Found {len(dup_groups)} duplicate clusters in {directory}:[/bold yellow]\n"
    )
    for i, g in enumerate(dup_groups, 1):
        table = Table(title=f"Cluster #{i}: {g.reason}")
        table.add_column("Role", style="cyan")
        table.add_column("File Path", style="dim")
        table.add_column("Format", style="green")
        table.add_column("Bitrate", style="yellow")

        table.add_row(
            "[bold green]Primary (Keeper)[/bold green]",
            Path(g.primary_track.file_path).name,
            (g.primary_track.file_format or "").upper(),
            f"{g.primary_track.bitrate or 0} bps",
        )
        for dup in g.duplicate_tracks:
            table.add_row(
                "[bold red]Duplicate[/bold red]",
                Path(dup.file_path).name,
                (dup.file_format or "").upper(),
                f"{dup.bitrate or 0} bps",
            )
        console.print(table)
        console.print()


@cli.command("rename")
@click.argument("target", type=click.Path(exists=True, resolve_path=True))
@click.option(
    "--pattern",
    "-p",
    default="{track_number:02d} - {artist} - {title}.{file_format}",
    help="Naming template format string",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Preview renames without moving"
)
def rename(target: str, pattern: str, dry_run: bool) -> None:
    """Rename audio file or directory according to structured metadata pattern."""
    from patangoma.services.renamer import RenamerService

    renamer = RenamerService()
    p = Path(target)

    if p.is_file():
        track = backend.read_metadata(p)
        old_p, new_p = renamer.rename_track(track, pattern=pattern, dry_run=dry_run)
        if dry_run:
            console.print(
                f"[dim]Dry-run rename:[/dim] {old_p.name} -> [bold green]{new_p.name}[/bold green]"
            )
        else:
            console.print(
                f"[bold green]✓ Renamed:[/bold green] {old_p.name} -> [bold green]{new_p.name}[/bold green]"
            )
    else:
        scanner = LibraryScanner(backend)
        tracks, _ = scanner.scan_directory(p)
        table = Table(title=f"Renaming Plan ({'Dry-Run' if dry_run else 'Applying'})")
        table.add_column("Original Filename", style="dim")
        table.add_column("Target Filename", style="green")

        for track in tracks:
            old_p, new_p = renamer.rename_track(track, pattern=pattern, dry_run=dry_run)
            table.add_row(old_p.name, new_p.name)

        console.print(table)
        if dry_run:
            console.print(
                f"[yellow]Previewed {len(tracks)} files. Run without --dry-run to apply.[/yellow]"
            )
        else:
            console.print(
                f"[bold green]✓ Renamed {len(tracks)} files successfully.[/bold green]"
            )


@cli.command("lyrics")
@click.argument("file_path", type=click.Path(exists=True, resolve_path=True))
@click.option(
    "--embed", is_flag=True, default=False, help="Embed fetched lyrics into file"
)
def get_lyrics(file_path: str, embed: bool) -> None:
    """Fetch plain and synchronized lyrics for an audio track."""
    from patangoma.providers.lyrics import LyricsProvider

    track = backend.read_metadata(file_path)
    if not track.title:
        console.print("[bold red]Track missing title tag.[/bold red]")
        sys.exit(1)

    prov = LyricsProvider()
    plain, synced = prov.fetch_lyrics(
        title=track.title,
        artist=track.artist or "",
        album=track.album,
    )

    if not plain and not synced:
        console.print(
            f"[dim]No lyrics found online for '{track.title}' by '{track.artist}'.[/dim]"
        )
        return

    lyrics_text = plain or synced or ""
    console.print(
        Panel(
            lyrics_text,
            title=f"Lyrics: {track.title} - {track.artist}",
            subtitle="Synced LRC" if synced else "Plain Text",
        )
    )

    if embed and plain:
        backend.write_tags(file_path, {"lyrics": plain}, dry_run=False)
        console.print(
            f"[bold green]✓ Embedded lyrics into {Path(file_path).name}[/bold green]"
        )


@cli.command()
@click.option(
    "--json-out", "--json", is_flag=True, help="Output diagnostics in JSON format"
)
def doctor(json_out: bool) -> None:
    """Diagnose system environment, audio backend, and provider configurations."""
    report = run_diagnostics()

    if json_out:
        click.echo(report.model_dump_json(indent=2))
        return

    table = Table(title="PataNgoma Environment Diagnostics")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    for chk in report.checks:
        if chk.status == "OK":
            status_text = "[bold green]✓ OK[/bold green]"
        elif chk.status == "WARNING":
            status_text = "[bold yellow]⚠ WARNING[/bold yellow]"
        else:
            status_text = "[bold red]✗ ERROR[/bold red]"

        table.add_row(chk.name, status_text, chk.message)

    console.print(table)


@cli.command()
@click.argument("path", type=click.Path(exists=True, resolve_path=True))
@click.option(
    "--json-out", "--json", is_flag=True, help="Output verification report in JSON"
)
def verify(path: str, json_out: bool) -> None:
    """Verify integrity and readability of audio files in a directory or file."""
    scanner = LibraryScanner(backend)
    target = Path(path)

    files = [target] if target.is_file() else scanner.discover_files(target)

    readable = 0
    corrupt = 0
    errors = []

    for f in files:
        try:
            backend.read_metadata(f)
            readable += 1
        except AudioFileError as e:
            corrupt += 1
            errors.append({"file": str(f), "error": str(e)})

    res = {
        "total_files": len(files),
        "verified_readable": readable,
        "corrupt_or_invalid": corrupt,
        "errors": errors,
    }

    if json_out:
        click.echo(json.dumps(res, indent=2))
        return

    if corrupt == 0:
        console.print(
            f"[bold green]✓ All {readable} files verified successfully![/bold green]"
        )
    else:
        console.print(
            f"[bold yellow]Verification completed with issues: {readable} valid, [red]{corrupt} corrupt[/red].[/bold yellow]"
        )


# -------------------------------------------------------------------------
# Legacy Interactive UI Helpers
# -------------------------------------------------------------------------


def _is_valid_audio(file_path: str) -> bool:
    """Check if file is valid audio."""
    try:
        MediaFile(file_path)
        return True
    except Exception:
        click.secho("\nERROR: Invalid or unsupported file format\n", fg="red")
        return False


def _interactive_select_path() -> str:
    """Prompt user for file path."""
    load_dotenv()
    music_dir = os.getenv("MUSIC_PATH") or os.getcwd()
    filename = inquirer.filepath(
        message="Please enter a path or select file from list:\n",
        amark="✔️ ",
        qmark="\n> ",
        validate=PathValidator(is_file=True, message="Input is not a file"),
        default=f"{music_dir}",
        instruction="Press <tab> to list directory contents",
    ).execute()
    return os.path.expanduser(filename)


def _main_menu(ctx: click.Context) -> None:
    """Main interactive menu."""
    action = inquirer.select(
        message="Select an action:",
        choices=[
            "Show-Tags",
            "Update-Tags",
            "Delete-Tags",
            "Search",
            Choice(value=None, name="Exit"),
        ],
        default=None,
        qmark="\n> ",
        amark="✔️ ",
    ).execute()
    fp = ctx.obj

    if action == "Show-Tags":
        _submenu_show(ctx)
    elif action == "Update-Tags":
        _submenu_update(ctx)
    elif action == "Search":
        _submenu_search(ctx)
    elif action == "Delete-Tags":
        ctx.invoke(delete, file_path=fp)


def _submenu_show(ctx: click.Context) -> None:
    fp = ctx.obj
    choice = inquirer.select(
        message="Select a 'Show-Tags' option:",
        choices=[
            Choice(name="Show all metadata", value="all"),
            Choice(name="Show existing metadata", value="existing"),
            Choice(name="Show missing metadata", value="missing"),
            Choice(name="Go back", value="Back"),
        ],
        default="Back",
    ).execute()

    if choice == "all":
        ctx.invoke(show, file_path=fp, all_t=True)
    elif choice == "existing":
        ctx.invoke(show, file_path=fp, existing=True)
    elif choice == "missing":
        ctx.invoke(show, file_path=fp, missing=True)
    elif choice == "Back":
        _main_menu(ctx)


def _submenu_update(ctx: click.Context) -> None:
    fp = ctx.obj
    valid_fields = ["artist", "album", "title", "track", "genre", "year", "comment"]
    selected = inquirer.fuzzy(
        message="Select fields:",
        choices=valid_fields,
        multiselect=True,
    ).execute()

    updates = []
    for key in selected:
        val = inquirer.text(message=f"{key}:").execute()
        updates.append(f"{key}={val}")

    ctx.invoke(update, file_path=fp, updates=tuple(updates))


def _submenu_search(ctx: click.Context) -> None:
    source = inquirer.select(
        message="Select a service to use:",
        choices=["spotify", "musicbrainz", "deezer"],
    ).execute()
    ctx.invoke(search, file_path=ctx.obj, source=source)


@cli.command()
@click.option("--all_t", "-a", is_flag=True, default=False, help="Show all metadata.")
@click.option(
    "--existing", "-e", is_flag=True, default=True, help="Show only existing metadata."
)
@click.option(
    "--missing", "-m", is_flag=True, default=False, help="Show missing metadata."
)
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
@click.pass_context
def show(
    ctx: click.Context,
    file_path: str,
    all_t: bool,
    existing: bool,
    missing: bool,
) -> None:
    """Show metadata for a media file <file_path>."""
    ctx.invoke(inspect, file_path=file_path, json_out=False)


@cli.command()
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
@click.argument("updates", nargs=-1)
def update(file_path: str, updates: tuple[str, ...]) -> None:
    """Update metadata for a media file <file_path>."""
    tag_dict: dict[str, Any] = {}
    for item in updates:
        if "=" in item:
            k, v = item.split("=", 1)
            tag_dict[k.strip()] = v.strip()

    if not tag_dict:
        console.print("[yellow]No key=value update arguments provided.[/yellow]")
        return

    try:
        backend.write_tags(file_path, tag_dict, dry_run=False)
        console.print(
            f"[bold green]✓ Updated tags for {Path(file_path).name}:[/bold green] {list(tag_dict.keys())}"
        )
    except Exception as e:
        console.print(f"[bold red]Failed to update tags:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def delete(file_path: str) -> None:
    """Delete all metadata from the media file <file_path>."""
    proceed = inquirer.confirm(
        message="Are you sure you want to delete all tags?", default=False
    ).execute()
    if proceed:
        try:
            # Clear standard tags
            empty_tags = {
                "title": None,
                "artist": None,
                "album": None,
                "year": None,
                "genre": None,
                "track_number": None,
            }
            backend.write_tags(file_path, empty_tags, dry_run=False)
            console.print(f"[green]Deleted tags for {file_path}[/green]")
        except Exception as e:
            console.print(f"[bold red]Failed to delete tags:[/bold red] {e}")
            sys.exit(1)


@cli.command()
@click.pass_context
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
@click.option("--source", "-s", help="Source service to use for search")
def search(ctx: click.Context, file_path: str, source: str | None) -> None:
    """Search for music information using the provided audio file."""
    ctx.invoke(match, file_path=file_path, provider=source or "musicbrainz")


if __name__ == "__main__":
    cli()
