"""Audio-centric commands for lyrics retrieval, ReplayGain tagging, verification, and quality transcoding inspection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table

from patangoma.domain.exceptions import AudioFileError
from patangoma.frontends.cli.state import audit_journal, backend, console
from patangoma.providers.registry import get_provider
from patangoma.services.quality import QualityInspector
from patangoma.services.replaygain import ReplayGainService
from patangoma.services.scanner import LibraryScanner


@click.command("lyrics")
@click.argument("file_path", type=click.Path(exists=True, resolve_path=True))
@click.option(
    "--embed", is_flag=True, default=False, help="Embed fetched lyrics into file"
)
def lyrics_cmd(file_path: str, embed: bool) -> None:
    """Fetch plain and synchronized lyrics for an audio track."""
    track = backend.read_metadata(file_path)
    if not track.title:
        console.print("[bold red]Track missing title tag.[/bold red]")
        sys.exit(1)

    prov = get_provider("lyrics")
    plain, synced = (
        prov.fetch_lyrics_pair(
            title=track.title,
            artist=track.artist or "",
            album=track.album,
        )
        if hasattr(prov, "fetch_lyrics_pair")
        else (prov.fetch_lyrics(track.title, track.artist or ""), None)
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


@click.command("replaygain")
@click.argument("target", type=click.Path(exists=True, resolve_path=True))
@click.option("--dry-run", is_flag=True, help="Simulate without writing")
def replaygain_cmd(target: str, dry_run: bool) -> None:
    """Calculate loudness peak/gain and write standard ReplayGain tags."""
    rg_svc = ReplayGainService(backend, audit_journal)
    p = Path(target)
    files = [p] if p.is_file() else LibraryScanner(backend).discover_files(p)

    table = Table(title=f"ReplayGain Analysis ({len(files)} files)")
    table.add_column("File", style="cyan")
    table.add_column("Gain (dB)", style="bold yellow")
    table.add_column("Peak", style="green")

    for f in files:
        res = rg_svc.calculate_track_gain(f)
        rg_svc.apply_replaygain_tags(f, res, dry_run=dry_run)
        table.add_row(
            Path(f).name, f"{res.track_gain_db:+.2f} dB", f"{res.track_peak:.4f}"
        )

    console.print(table)
    if dry_run:
        console.print("[yellow]DRY-RUN: Tags were not written to disk.[/yellow]")
    else:
        console.print(
            f"[bold green]✓ Applied ReplayGain tags to {len(files)} files.[/bold green]"
        )


@click.command("verify")
@click.argument("path", type=click.Path(exists=True, resolve_path=True))
@click.option(
    "--json-out", "--json", is_flag=True, help="Output verification report in JSON"
)
def verify_cmd(path: str, json_out: bool) -> None:
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


@click.command("transcode-check")
@click.argument("path", type=click.Path(exists=True, resolve_path=True))
def transcode_check_cmd(path: str) -> None:
    """Inspect audio stream encoding quality and check for transcode anomalies."""
    qi = QualityInspector(backend)
    p = Path(path)
    files = [p] if p.is_file() else LibraryScanner(backend).discover_files(p)

    table = Table(title=f"Audio Encoding & Quality Check ({len(files)} files)")
    table.add_column("File", style="cyan")
    table.add_column("Format", style="dim")
    table.add_column("Bitrate", style="yellow")
    table.add_column("Sample Rate", style="green")
    table.add_column("Grade", style="bold")
    table.add_column("Issues", style="red")

    for f in files:
        rep = qi.inspect_file(f)
        grade_color = (
            "green"
            if rep.quality_grade in ("LOSSLESS", "HIGH_BITRATE")
            else ("yellow" if rep.quality_grade == "MEDIUM_BITRATE" else "red")
        )
        table.add_row(
            Path(f).name,
            rep.format.upper(),
            f"{rep.bitrate_kbps} kbps" if rep.bitrate_kbps else "—",
            f"{rep.sample_rate_hz} Hz" if rep.sample_rate_hz else "—",
            f"[{grade_color}]{rep.quality_grade}[/{grade_color}]",
            "; ".join(rep.issues) if rep.issues else "✓ Clean",
        )

    console.print(table)
