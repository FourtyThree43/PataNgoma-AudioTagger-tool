"""Audit history viewing, report export, and transactional rollback commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.table import Table

from patangoma.domain.exceptions import PataNgomaError
from patangoma.frontends.cli.state import audit_journal, backend, console


@click.command("rollback")
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
def rollback_cmd(
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


@click.command("history")
@click.option("--limit", "-n", default=20, help="Maximum history records to display")
@click.option("--json-out", "--json", is_flag=True, help="Output history in JSON")
def history_cmd(limit: int, json_out: bool) -> None:
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


@click.command("export-audit")
@click.argument("output_file", type=click.Path())
@click.option(
    "--format",
    "-f",
    type=click.Choice(["html", "csv"], case_sensitive=False),
    default="html",
    help="Export format (html or csv)",
)
@click.option("--limit", "-n", default=500, help="Maximum records to export")
def export_audit_cmd(output_file: str, format: str, limit: int) -> None:
    """Export audit log history to HTML or CSV report."""
    if format.lower() == "csv":
        out = audit_journal.export_history_csv(output_file, limit=limit)
    else:
        out = audit_journal.export_history_html(output_file, limit=limit)
    console.print(
        f"[bold green]✓ Exported {format.upper()} audit report to '{out.resolve()}'[/bold green]"
    )
