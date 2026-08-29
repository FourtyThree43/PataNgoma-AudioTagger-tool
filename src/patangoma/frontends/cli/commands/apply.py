"""Tag plan execution and batch apply commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from patangoma.domain.models import FieldDiffStatus
from patangoma.frontends.cli.helpers import query_candidates
from patangoma.frontends.cli.state import (
    audit_journal,
    backend,
    batch_service,
    console,
    matching_engine,
    planner,
)
from patangoma.services.artwork import ArtworkService


@click.command("apply")
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
    "--embed-artwork",
    is_flag=True,
    help="Download and embed album artwork from match candidate",
)
@click.option(
    "--json-out",
    "--json",
    is_flag=True,
    help="Output apply result in JSON format",
)
def apply_cmd(
    plan_or_file: str,
    dry_run: bool,
    provider: str,
    embed_artwork: bool,
    json_out: bool,
) -> None:
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
        candidates, _ = query_candidates(track, audio_path, provider)
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
    if (
        embed_artwork
        and tag_plan.candidate_metadata
        and tag_plan.candidate_metadata.artwork_url
    ):
        try:
            art_svc = ArtworkService()
            img_data = art_svc.download_and_validate_artwork(
                tag_plan.candidate_metadata.artwork_url
            )
            if img_data:
                backend.write_artwork(audio_path, img_data)
                console.print(
                    f"[bold green]✓ Embedded artwork into {Path(audio_path).name}[/bold green]"
                )
        except Exception:
            pass

    audit_rec = audit_journal.record_apply(tag_plan, track_before, updated)

    if json_out:
        click.echo(audit_rec.model_dump_json(indent=2))
        return

    console.print(
        f"[bold green]✓ Successfully applied plan to {Path(audio_path).name}[/bold green]"
    )
    console.print(f"[dim]Operation ID: {audit_rec.operation_id}[/dim]")


@click.command("apply-dir")
@click.argument(
    "plan_file", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    "--dry-run", is_flag=True, help="Simulate batch mutation without writing to disk"
)
@click.option(
    "--embed-artwork",
    is_flag=True,
    help="Download and embed album artwork for each track in batch plan",
)
@click.option(
    "--json-out", "--json", is_flag=True, help="Output applied batch records in JSON"
)
def apply_dir_cmd(
    plan_file: str, dry_run: bool, embed_artwork: bool, json_out: bool
) -> None:
    """Apply a batch plan across an entire music library."""
    batch_plan = batch_service.load_batch_plan(plan_file)
    records = batch_service.apply_batch_plan(batch_plan, dry_run=dry_run)

    if embed_artwork and not dry_run:
        art_svc = ArtworkService()
        for p in batch_plan.matched_plans:
            if p.candidate_metadata and p.candidate_metadata.artwork_url:
                try:
                    img = art_svc.download_and_validate_artwork(
                        p.candidate_metadata.artwork_url
                    )
                    if img:
                        backend.write_artwork(p.file_path, img)
                except Exception:
                    pass

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
