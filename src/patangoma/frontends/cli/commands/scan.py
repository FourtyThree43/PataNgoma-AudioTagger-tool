"""Library scanning, track inspection, and file integrity check commands."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.table import Table

from patangoma.domain.exceptions import AudioFileError
from patangoma.frontends.cli.state import backend, console
from patangoma.services.scanner import LibraryScanner
from patangoma.services.validator import FileValidator


@click.command("scan")
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
def scan_cmd(path: str, recursive: bool, json_out: bool) -> None:
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


@click.command("inspect")
@click.argument(
    "file_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    "--json-out", "--json", is_flag=True, help="Output metadata in JSON format"
)
def inspect_cmd(file_path: str, json_out: bool) -> None:
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


@click.command("check-file")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--json-out", "--json", is_flag=True, help="Output report in JSON")
def check_file_cmd(file_path: str, json_out: bool) -> None:
    """Pre-flight file header integrity and corruption inspection."""
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
