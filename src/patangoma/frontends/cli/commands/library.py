"""Library organization, renaming, duplicate detection, genre normalization, and playlist commands."""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import click
from InquirerPy import inquirer
from rich.panel import Panel
from rich.table import Table

from patangoma.frontends.cli.state import backend, console
from patangoma.services.duplicates import DuplicateDetector
from patangoma.services.genre import GenreNormalizer
from patangoma.services.playlist import PlaylistService
from patangoma.services.renamer import RenamerService
from patangoma.services.sample_generator import generate_sample_library
from patangoma.services.scanner import LibraryScanner


@click.command("duplicates")
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
@click.option("--json-out", "--json", is_flag=True, help="Output duplicates in JSON")
def duplicates_cmd(directory: str, json_out: bool) -> None:
    """Detect duplicate audio files across formats, bitrates, and subdirectories."""
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


@click.command("rename")
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
def rename_cmd(target: str, pattern: str, dry_run: bool) -> None:
    """Rename audio file or directory according to structured metadata pattern."""
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


@click.command("normalize-genres")
@click.argument("target", type=click.Path(exists=True, resolve_path=True))
@click.option("--dry-run", is_flag=True, help="Preview without writing")
def normalize_genres_cmd(target: str, dry_run: bool) -> None:
    """Standardize messy genre tags to canonical taxonomy."""
    normalizer = GenreNormalizer()
    p = Path(target)
    files = [p] if p.is_file() else LibraryScanner(backend).discover_files(p)

    table = Table(title=f"Genre Normalization ({len(files)} files)")
    table.add_column("File", style="dim")
    table.add_column("Original Genre", style="yellow")
    table.add_column("Canonical Genre", style="bold green")

    updated_count = 0
    for f in files:
        meta = backend.read_metadata(f)
        if not meta.genre:
            continue
        res = normalizer.normalize(meta.genre)
        if res.changed:
            updated_count += 1
            table.add_row(Path(f).name, res.raw_genre, res.canonical_genre)
            if not dry_run:
                backend.write_tags(f, {"genre": res.canonical_genre}, dry_run=False)

    console.print(table)
    if dry_run:
        console.print(
            f"[yellow]Previewed {updated_count} updates. Run without --dry-run to write tags.[/yellow]"
        )
    else:
        console.print(
            f"[bold green]✓ Normalized {updated_count} genre tags.[/bold green]"
        )


@click.command("playlist-export")
@click.argument("directory", type=click.Path(exists=True, resolve_path=True))
@click.option("--output", "-o", default="playlist.m3u8", help="Output playlist file")
@click.option(
    "--absolute", is_flag=True, help="Use absolute file paths instead of relative"
)
def playlist_export_cmd(directory: str, output: str, absolute: bool) -> None:
    """Export scanned audio files to an extended UTF-8 M3U8 playlist."""
    files = LibraryScanner(backend).discover_files(directory)
    ps = PlaylistService(backend)
    out = ps.export_m3u8(files, output, relative_paths=not absolute)
    console.print(
        f"[bold green]✓ Exported {len(files)} tracks to playlist:[/bold green] {out}"
    )


@click.command("cue-inspect")
@click.argument(
    "cue_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
def cue_inspect_cmd(cue_path: str) -> None:
    """Inspect and display tracks from a Cue sheet."""
    ps = PlaylistService(backend)
    tracks = ps.parse_cue_sheet(cue_path)
    if not tracks:
        console.print("[yellow]No tracks found in Cue sheet.[/yellow]")
        return

    table = Table(title=f"Cue Sheet: {Path(cue_path).name}")
    table.add_column("#", style="dim")
    table.add_column("Title", style="bold cyan")
    table.add_column("Artist", style="green")
    table.add_column("Index 01", style="magenta")

    for t in tracks:
        table.add_row(
            str(t.track_number), t.title, t.artist or "—", t.index_time or "—"
        )

    console.print(table)


@click.command("edit")
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
def edit_cmd(file_path: str) -> None:
    """Interactively edit metadata fields for an audio file."""
    meta = backend.read_metadata(file_path)
    console.print(f"[bold cyan]Editing tags for:[/bold cyan] {Path(file_path).name}")

    new_title = inquirer.text(message="Title:", default=meta.title or "").execute()
    new_artist = inquirer.text(message="Artist:", default=meta.artist or "").execute()
    new_album = inquirer.text(message="Album:", default=meta.album or "").execute()
    new_year = inquirer.text(message="Year:", default=str(meta.year or "")).execute()
    new_track = inquirer.text(
        message="Track Number:", default=str(meta.track_number or "")
    ).execute()
    new_genre = inquirer.text(message="Genre:", default=meta.genre or "").execute()

    updates: dict[str, Any] = {}
    if new_title != (meta.title or ""):
        updates["title"] = new_title or None
    if new_artist != (meta.artist or ""):
        updates["artist"] = new_artist or None
    if new_album != (meta.album or ""):
        updates["album"] = new_album or None
    if new_year != str(meta.year or ""):
        updates["year"] = int(new_year) if new_year.isdigit() else None
    if new_track != str(meta.track_number or ""):
        updates["track_number"] = int(new_track) if new_track.isdigit() else None
    if new_genre != (meta.genre or ""):
        updates["genre"] = new_genre or None

    if not updates:
        console.print("[dim]No changes made.[/dim]")
        return

    backend.write_tags(file_path, updates, dry_run=False)
    console.print(f"[bold green]✓ Updated tags:[/bold green] {list(updates.keys())}")


@click.command("export-catalog")
@click.argument("directory", type=click.Path(exists=True, resolve_path=True))
@click.option(
    "--format", "-f", type=click.Choice(["json", "csv", "sqlite"]), default="json"
)
@click.option("--output", "-o", default="catalog.json", help="Output catalog file path")
def export_catalog_cmd(directory: str, format: str, output: str) -> None:
    """Export complete library catalog to JSON, CSV, or SQLite."""
    files = LibraryScanner(backend).discover_files(directory)
    records = []
    for f in files:
        try:
            m = backend.read_metadata(f)
            records.append(m.model_dump())
        except Exception:
            pass

    out_p = Path(output)
    if format == "json":
        out_p.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
    elif format == "csv":
        if records:
            keys = list(records[0].keys())
            with out_p.open("w", newline="", encoding="utf-8") as f_csv:
                writer = csv.DictWriter(f_csv, fieldnames=keys)
                writer.writeheader()
                for r in records:
                    writer.writerow(
                        {k: str(v) if v is not None else "" for k, v in r.items()}
                    )
    elif format == "sqlite":
        conn = sqlite3.connect(out_p)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS catalog (file_path TEXT PRIMARY KEY, title TEXT, artist TEXT, album TEXT, year INTEGER, genre TEXT, bitrate INTEGER, duration REAL)"
        )
        for r in records:
            cur.execute(
                "INSERT OR REPLACE INTO catalog VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    r.get("file_path"),
                    r.get("title"),
                    r.get("artist"),
                    r.get("album"),
                    r.get("year"),
                    r.get("genre"),
                    r.get("bitrate"),
                    r.get("duration_seconds"),
                ),
            )
        conn.commit()
        conn.close()

    console.print(
        f"[bold green]✓ Catalog exported ({len(records)} tracks) to {out_p}[/bold green]"
    )


@click.command("demo-library")
@click.argument("directory", type=click.Path())
def demo_library_cmd(directory: str) -> None:
    """Generate a sample test music library with valid, missing, and corrupt audio files."""
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


@click.command("delete")
@click.argument("file_path", type=click.Path(exists=True))
def delete_cmd(file_path: str) -> None:
    """Delete all metadata from the media file."""
    proceed = inquirer.confirm(
        message="Are you sure you want to delete all tags?", default=False
    ).execute()
    if proceed:
        try:
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


@click.command("search")
@click.pass_context
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
@click.option("--source", "-s", help="Source service to use for search")
def search_cmd(ctx: click.Context, file_path: str, source: str | None) -> None:
    """Search for music information using the provided audio file."""
    from patangoma.frontends.cli.commands.match import match_cmd

    ctx.invoke(match_cmd, file_path=file_path, provider=source or "musicbrainz")
