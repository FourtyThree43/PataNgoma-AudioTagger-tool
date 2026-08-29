"""System diagnostics and environment health check command."""

from __future__ import annotations

import click
from rich.table import Table

from patangoma.frontends.cli.state import console
from patangoma.services.doctor import run_diagnostics


@click.command("doctor")
@click.option(
    "--json-out", "--json", is_flag=True, help="Output diagnostics in JSON format"
)
def doctor_cmd(json_out: bool) -> None:
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
