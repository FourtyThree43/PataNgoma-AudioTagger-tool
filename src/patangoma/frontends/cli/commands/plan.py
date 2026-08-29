"""Tag planning commands for single files and batch directories."""

from __future__ import annotations

import sys

import click

from patangoma.domain.exceptions import AudioFileError, ProviderError
from patangoma.frontends.cli.helpers import query_candidates
from patangoma.frontends.cli.state import (
    backend,
    batch_service,
    console,
    matching_engine,
    planner,
)


@click.command("plan")
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
def plan_cmd(file_path: str, provider: str, output: str | None, json_out: bool) -> None:
    """Generate a deterministic mutation plan for an audio file."""
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


@click.command("plan-dir")
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
def plan_dir_cmd(
    directory: str, provider: str, output: str | None, json_out: bool
) -> None:
    """Generate a batch mutation plan across an entire directory."""
    batch_plan = batch_service.generate_batch_plan(directory, provider_name=provider)

    if output:
        out_path = batch_service.export_batch_plan(batch_plan, output)
        console.print(f"[bold green]✓ Batch plan saved to:[/bold green] {out_path}")

    if json_out or not output:
        click.echo(batch_plan.model_dump_json(indent=2))
