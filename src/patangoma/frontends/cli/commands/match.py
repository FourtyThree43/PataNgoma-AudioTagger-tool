"""Metadata matching, explainable AI reasoning, and interactive tagging wizard commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.table import Table

from patangoma.domain.exceptions import AudioFileError, ProviderError
from patangoma.domain.models import ConfidenceLevel, FieldDiffStatus
from patangoma.frontends.cli.helpers import query_candidates
from patangoma.frontends.cli.state import (
    audit_journal,
    backend,
    console,
    matching_engine,
    planner,
    reasoner,
)


@click.command("match")
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
def match_cmd(file_path: str, provider: str, json_out: bool) -> None:
    """Search provider and compute explainable match confidence scores."""
    try:
        track = backend.read_metadata(file_path)
    except AudioFileError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)

    try:
        candidates, display_title = query_candidates(track, file_path, provider)
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


@click.command("reason")
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


@click.command("tag")
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
@click.option(
    "--provider",
    "-p",
    default="multi",
    help="Provider (itunes, musicbrainz, multi, etc.)",
)
@click.option(
    "--interactive/--no-interactive",
    "-i/-I",
    default=True,
    help="Interactive terminal candidate selector",
)
@click.option("--dry-run", is_flag=True, help="Simulate without writing")
def tag_cmd(file_path: str, provider: str, interactive: bool, dry_run: bool) -> None:
    """Interactively match, select, and tag an audio file."""
    track = backend.read_metadata(file_path)
    candidates, display_title = query_candidates(track, file_path, provider)
    if not candidates:
        console.print(f"[yellow]No candidates found for '{display_title}'.[/yellow]")
        return

    results = matching_engine.rank_candidates(track, candidates)
    if interactive and len(results) > 1:
        choices = []
        for res in results[:10]:
            c = res.candidate
            label = f"[{res.confidence.value}] {c.title} — {c.primary_artist} ({c.album or 'No Album'}, {c.year or 'N/A'}) - {res.score.total_score * 100:.0f}%"
            choices.append(Choice(value=res, name=label))
        choices.append(Choice(value=None, name="Cancel"))

        selected = inquirer.select(
            message=f"Select match for '{display_title}':",
            choices=choices,
        ).execute()

        if not selected:
            console.print("[dim]Tagging cancelled.[/dim]")
            return
        best = selected
    else:
        best = results[0]

    tag_plan = planner.create_plan(
        track, best.candidate, best.confidence, best.score.total_score
    )
    updates = {
        diff.field_name: diff.new_value
        for diff in tag_plan.diffs
        if diff.status in (FieldDiffStatus.ADDED, FieldDiffStatus.MODIFIED)
    }
    if not updates:
        console.print("[green]✓ File is already perfectly tagged.[/green]")
        return

    table = Table(title=f"Tag Updates: {Path(file_path).name}")
    table.add_column("Field", style="cyan")
    table.add_column("Current Tag", style="dim")
    table.add_column("New Tag", style="bold green")
    for diff in tag_plan.diffs:
        if diff.status in (FieldDiffStatus.ADDED, FieldDiffStatus.MODIFIED):
            table.add_row(
                diff.field_name, str(diff.old_value or "—"), str(diff.new_value)
            )
    console.print(table)

    if dry_run:
        console.print("[yellow]DRY-RUN: No changes written to disk.[/yellow]")
    else:
        updated = backend.write_tags(file_path, updates, dry_run=False)
        audit_journal.record_apply(tag_plan, track, updated)
        console.print(
            f"[bold green]✓ Successfully applied tags to {Path(file_path).name}[/bold green]"
        )
