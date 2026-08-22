#!/usr/bin/env python3
"""Modern CLI interface for PataNgoma AudioTagger."""

from __future__ import annotations

import json
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

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
    QueryParameters,
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
from patangoma.track import TrackInfo

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


@cli.command()
@click.argument(
    "file_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    "--provider",
    "-p",
    default="musicbrainz",
    help="Provider (musicbrainz, deezer, spotify)",
)
@click.option(
    "--json-out", "--json", is_flag=True, help="Output match results in JSON format"
)
def match(file_path: str, provider: str, json_out: bool) -> None:
    """Search provider and compute explainable match confidence scores."""
    try:
        track = backend.read_metadata(file_path)
    except AudioFileError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)

    try:
        prov = get_provider(provider)
        candidates = prov.search_tracks(
            QueryParameters(title=track.title, artist=track.artist, album=track.album)
        )
    except ProviderError as e:
        console.print(f"[bold red]Provider Error:[/bold red] {e}")
        sys.exit(3)

    if not candidates:
        console.print(
            f"[yellow]No candidates found on {provider} for {track.title} by {track.artist}.[/yellow]"
        )
        return

    results = matching_engine.rank_candidates(track, candidates)

    if json_out:
        click.echo(json.dumps([r.model_dump() for r in results], indent=2, default=str))
        return

    table = Table(title=f"Metadata Matches for '{track.title}' (via {provider})")
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
    "file_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
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
        prov = get_provider(provider)
        candidates = prov.search_tracks(
            QueryParameters(title=track.title, artist=track.artist, album=track.album)
        )
    except ProviderError as e:
        console.print(f"[bold red]Provider Error:[/bold red] {e}")
        sys.exit(3)

    if not candidates:
        console.print(f"[yellow]No match candidates found on {provider}.[/yellow]")
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
    "plan_or_file", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
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
    "--json-out", "--json", is_flag=True, help="Output apply result in JSON format"
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
        prov = get_provider(provider)
        candidates = prov.search_tracks(
            QueryParameters(title=track.title, artist=track.artist, album=track.album)
        )
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
@click.argument("operation_id")
@click.option(
    "--json-out", "--json", is_flag=True, help="Output rollback outcome in JSON"
)
def rollback(operation_id: str, json_out: bool) -> None:
    """Roll back an audio mutation using its Operation ID."""
    try:
        restored = audit_journal.rollback_operation(operation_id, backend)
        if json_out:
            click.echo(restored.model_dump_json(indent=2))
            return
        console.print(
            f"[bold green]✓ Restored tags for {restored.path.name} from operation {operation_id}[/bold green]"
        )
    except PataNgomaError as e:
        console.print(f"[bold red]Rollback failed:[/bold red] {e}")
        sys.exit(1)


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
def show(file_path: str, all_t: bool, existing: bool, missing: bool) -> None:
    """Show metadata for a media file <file_path>."""
    if _is_valid_audio(file_path):
        track = TrackInfo(file_path)
        if all_t:
            track.show_all_metadata()
        elif missing:
            track.show_missing_metadata()
        else:
            track.show_existing_metadata()
    else:
        sys.exit(1)


@cli.command()
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
@click.argument("updates", nargs=-1)
def update(file_path: str, updates: tuple[str, ...]) -> None:
    """Update metadata for a media file <file_path>."""
    if _is_valid_audio(file_path):
        track = TrackInfo(file_path)
        md_pre_update = track.as_dict()
        track.batch_update_metadata(updates)

        if track.has_changed(track.as_dict(), md_pre_update):
            click.echo(f"\nMetadata changes for {track.metadata.filename}:\n")
            for key, value in track.as_dict().items():
                if key != "images" and md_pre_update.get(key) != value:
                    click.echo(f"{key}: {md_pre_update.get(key)} -> {value}")

            if click.confirm("\nDo you want to save these changes?"):
                track.save()
                click.echo("Changes saved.")
            else:
                click.echo("Changes not saved.")
        else:
            click.echo("No changes to save.")
    else:
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def delete(file_path: str) -> None:
    """Delete all metadata from the media file <file_path>."""
    if _is_valid_audio(file_path):
        track = TrackInfo(file_path)
        proceed = inquirer.confirm(
            message="Are you sure you want to delete all tags?", default=False
        ).execute()
        if proceed:
            track.delete()
            console.print(f"[green]Deleted tags for {file_path}[/green]")
    else:
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
