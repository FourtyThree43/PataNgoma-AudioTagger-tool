"""Background jobs listing and task management commands."""

from __future__ import annotations

import json

import click
from rich.table import Table

from patangoma.bootstrap.application import create_application
from patangoma.frontends.cli.state import console


@click.group("jobs")
def jobs_group() -> None:
    """Manage and inspect background jobs."""
    pass


@jobs_group.command("list")
@click.option("--limit", "-n", default=20, help="Maximum jobs to list")
@click.option("--json-out", "--json", is_flag=True, help="Output jobs in JSON")
def list_jobs_cmd(limit: int, json_out: bool) -> None:
    """List recent background jobs and their execution states."""
    app = create_application()
    jobs = app.list_jobs(limit=limit)

    if json_out:
        click.echo(json.dumps([j.model_dump() for j in jobs], indent=2, default=str))
        return

    if not jobs:
        console.print("[dim]No background jobs found.[/dim]")
        return

    table = Table(title="Background Jobs")
    table.add_column("Job ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("State")
    table.add_column("Progress", style="yellow")

    for j in jobs:
        state_color = {
            "RUNNING": "green",
            "COMPLETED": "bold green",
            "FAILED": "bold red",
            "CANCELLED": "yellow",
            "PENDING": "cyan",
        }.get(j.state.value, "white")

        table.add_row(
            j.id[:8] + "...",
            j.name,
            j.job_type,
            f"[{state_color}]{j.state.value}[/{state_color}]",
            f"{j.progress * 100:.0f}%",
        )

    console.print(table)


@jobs_group.command("cancel")
@click.argument("job_id")
def cancel_job_cmd(job_id: str) -> None:
    """Cancel a running background job."""
    app = create_application()
    res = app.cancel_job(job_id)
    if res:
        console.print(f"[bold green]✓ Job {job_id} cancelled.[/bold green]")
    else:
        console.print(
            f"[bold red]✗ Failed to cancel job {job_id} (not found or already completed).[/bold red]"
        )
