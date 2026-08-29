"""Capability plugins listing and inspection commands."""

from __future__ import annotations

import json

import click
from rich.table import Table

from patangoma.frontends.cli.state import console
from patangoma.plugins.discovery import create_default_plugin_registry


@click.group("plugins")
def plugins_group() -> None:
    """Manage and inspect capability plugins."""
    pass


@plugins_group.command("list")
@click.option("--json-out", "--json", is_flag=True, help="Output plugins in JSON")
def list_plugins_cmd(json_out: bool) -> None:
    """List all registered capability plugins and their operational status."""
    registry = create_default_plugin_registry()
    plugins = registry.list_plugins()
    health = registry.health_all()

    if json_out:
        data = []
        for p in plugins:
            data.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "version": p.version,
                    "capabilities": [c.value for c in p.capabilities],
                    "health": health.get(p.id, {}),
                }
            )
        click.echo(json.dumps(data, indent=2))
        return

    table = Table(title="Registered Capability Plugins")
    table.add_column("ID", style="cyan")
    table.add_column("Plugin Name", style="bold")
    table.add_column("Version", style="dim")
    table.add_column("Capabilities", style="yellow")
    table.add_column("Status")

    for p in plugins:
        h = health.get(p.id, {})
        status = h.get("status", "UNKNOWN")
        status_text = (
            "[bold green]HEALTHY[/bold green]"
            if status == "HEALTHY"
            else f"[bold yellow]{status}[/bold yellow]"
        )
        caps = ", ".join(c.value for c in p.capabilities)
        table.add_row(p.id, p.name, p.version, caps, status_text)

    console.print(table)
