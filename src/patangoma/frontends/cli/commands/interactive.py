"""Interactive REPL session, guided TUI loop, and GUI/TUI launchers."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from mediafile import MediaFile
from rich.panel import Panel
from rich.table import Table

from patangoma.frontends.cli.state import backend, console


def is_valid_audio(file_path: str) -> bool:
    """Check if file is valid audio."""
    try:
        MediaFile(file_path)
        return True
    except Exception:
        return False


def interactive_select_path() -> str:
    """Prompt user for file or folder path with tab-completion."""
    load_dotenv()
    music_dir = os.getenv("MUSIC_PATH") or os.getcwd()
    filename = inquirer.filepath(
        message="Please enter a path or select file/folder:\n",
        amark="✓ ",
        qmark="📁",
        default=f"{music_dir}",
        instruction="Press <tab> to browse filesystem",
    ).execute()
    return os.path.expanduser(filename) if filename else ""


def interactive_session_loop(
    ctx: click.Context, initial_path: str | None = None
) -> None:
    """Continuous interactive TUI loop with multi-action navigation."""
    from patangoma.frontends.cli.commands.audio import (
        lyrics_cmd,
        replaygain_cmd,
    )
    from patangoma.frontends.cli.commands.doctor import doctor_cmd
    from patangoma.frontends.cli.commands.library import (
        edit_cmd,
        normalize_genres_cmd,
        rename_cmd,
    )
    from patangoma.frontends.cli.commands.match import tag_cmd
    from patangoma.frontends.cli.commands.plan import plan_dir_cmd
    from patangoma.frontends.cli.commands.rollback import (
        history_cmd,
        rollback_cmd,
    )
    from patangoma.frontends.cli.commands.scan import inspect_cmd

    current_target = initial_path or interactive_select_path()
    if not current_target or not Path(current_target).exists():
        console.print("[yellow]No valid file or directory selected. Exiting.[/yellow]")
        return

    while True:
        target_name = Path(current_target).name
        target_is_file = Path(current_target).is_file()

        console.print(
            f"\n[bold cyan]Selected Target:[/bold cyan] [bold yellow]{current_target}[/bold yellow]"
        )
        action = inquirer.select(
            message=f"Action for '{target_name}':",
            choices=[
                Choice("match_tag", "🎯 Match & Tag Track (7 Providers)"),
                Choice("inspect", "👁️ Inspect Metadata & Technical Properties"),
                Choice("edit", "✏️ Edit Tags Interactively"),
                Choice("replaygain", "📊 ReplayGain & Loudness Scan"),
                Choice("rename", "📂 Rename / Organize by Pattern"),
                Choice("lyrics", "📜 Fetch Plain & Synced Lyrics"),
                Choice("normalize_genres", "🧹 Normalize Genre to Canonical Taxonomy"),
                Choice("history", "📜 View Audit History"),
                Choice("rollback", "⏪ Rollback Last Mutation"),
                Choice("change_file", "📁 Choose Another File / Directory"),
                Choice("launch_repl", "💻 Switch to Power-User REPL Shell (/commands)"),
                Choice("doctor", "🩺 Run System Diagnostics (Doctor)"),
                Choice(None, "🚪 Exit"),
            ],
            default="match_tag",
            qmark="🎵",
            amark="✓",
        ).execute()

        if action is None:
            console.print("[bold green]Goodbye![/bold green]")
            break

        if action == "launch_repl":
            ctx.invoke(session_cmd)
            break

        if action == "match_tag":
            if not target_is_file:
                console.print(
                    "[yellow]Batch match on directory: Generating batch plan...[/yellow]"
                )
                ctx.invoke(
                    plan_dir_cmd,
                    directory=current_target,
                    provider="multi",
                    output=None,
                    json_out=False,
                )
            else:
                prov = inquirer.select(
                    message="Select Metadata Provider:",
                    choices=[
                        Choice(
                            "multi",
                            "🌟 Multi-Provider Aggregator (iTunes + MB + Discogs + Deezer)",
                        ),
                        Choice("itunes", "🍏 Apple iTunes (Fast & High-Res Cover Art)"),
                        Choice("musicbrainz", "🎼 MusicBrainz (Authoritative DB)"),
                        Choice("discogs", "💿 Discogs (Vinyl & Release Data)"),
                        Choice("deezer", "📻 Deezer (Global Music Catalog)"),
                        Choice("spotify", "🎧 Spotify (Streaming Catalog)"),
                        Choice(
                            "acoustid", "🌊 AcoustID (Acoustic Fingerprint via fpcalc)"
                        ),
                    ],
                    default="multi",
                    qmark="🔍",
                ).execute()
                ctx.invoke(
                    tag_cmd,
                    file_path=current_target,
                    provider=prov,
                    interactive=True,
                    dry_run=False,
                )

        elif action == "inspect":
            ctx.invoke(inspect_cmd, file_path=current_target, json_out=False)

        elif action == "edit":
            if target_is_file:
                ctx.invoke(edit_cmd, file_path=current_target)
            else:
                console.print(
                    "[yellow]Edit command applies to single audio files.[/yellow]"
                )

        elif action == "replaygain":
            ctx.invoke(replaygain_cmd, target=current_target, dry_run=False)

        elif action == "rename":
            pattern = inquirer.text(
                message="Naming template pattern:",
                default="{track_number:02d} - {artist} - {title}.{file_format}",
            ).execute()
            ctx.invoke(
                rename_cmd, target=current_target, pattern=pattern, dry_run=False
            )

        elif action == "lyrics":
            if target_is_file:
                ctx.invoke(
                    lyrics_cmd,
                    file_path=current_target,
                    embed=False,
                )
            else:
                console.print(
                    "[yellow]Lyrics command applies to single audio files.[/yellow]"
                )

        elif action == "normalize_genres":
            ctx.invoke(normalize_genres_cmd, target=current_target, dry_run=False)

        elif action == "history":
            ctx.invoke(history_cmd, limit=10, json_out=False)

        elif action == "rollback":
            ctx.invoke(
                rollback_cmd,
                operation_id=None,
                latest=True,
                path=None,
                json_out=False,
            )

        elif action == "change_file":
            new_target = interactive_select_path()
            if new_target and Path(new_target).exists():
                current_target = new_target

        elif action == "doctor":
            ctx.invoke(doctor_cmd, json_out=False)


@click.command("session")
@click.pass_context
def session_cmd(ctx: click.Context) -> None:
    """Launch interactive REPL session with slash commands and Claude-style TUI."""
    from patangoma.frontends.cli.commands.audio import replaygain_cmd
    from patangoma.frontends.cli.commands.doctor import doctor_cmd
    from patangoma.frontends.cli.commands.match import match_cmd, tag_cmd
    from patangoma.frontends.cli.commands.rollback import history_cmd
    from patangoma.frontends.cli.commands.scan import inspect_cmd

    console.print(
        Panel.fit(
            "[bold red]PataNgoma[/bold red] [bold white]Interactive REPL Session[/bold white]\n"
            "[dim]A Music Collector's Best Friend — Determinism Before Intelligence[/dim]\n\n"
            "Type [bold cyan]/help[/bold cyan] for slash commands or [bold cyan]/exit[/bold cyan] to quit.\n"
            "[dim]Commands: /inspect, /match, /tag, /plan, /apply, /replaygain, /rename, /doctor, /history[/dim]",
            border_style="red",
        )
    )

    while True:
        try:
            cmd_input = inquirer.text(
                message="patangoma>",
                qmark="🎵",
                amark="✓",
            ).execute()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            break

        if not cmd_input or not cmd_input.strip():
            continue

        raw = cmd_input.strip()
        parts = raw.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("/exit", "/quit", "exit", "quit"):
            console.print("[bold green]Goodbye![/bold green]")
            break

        if cmd in ("/help", "help"):
            table = Table(title="PataNgoma REPL Command Reference")
            table.add_column("Command", style="bold cyan")
            table.add_column("Description")
            table.add_row(
                "/inspect <file>", "Inspect track metadata and audio properties"
            )
            table.add_row(
                "/match <file>", "Search metadata providers and rank candidates"
            )
            table.add_row(
                "/tag <file>", "Interactively select candidate and apply tags"
            )
            table.add_row("/plan <file>", "Generate mutation plan diff")
            table.add_row("/apply <file>", "Apply best candidate or plan to file")
            table.add_row("/replaygain <path>", "Calculate loudness and peak gain tags")
            table.add_row(
                "/rename <path>", "Organize and rename file by template pattern"
            )
            table.add_row("/doctor", "Run system diagnostics and fpcalc check")
            table.add_row("/history", "View recent mutation audit journal records")
            table.add_row("/menu", "Switch to Guided TUI Wizard (Arrow-key menus)")
            table.add_row("/clear", "Clear terminal screen")
            table.add_row("/exit", "Exit the interactive session")
            console.print(table)

        elif cmd in ("/menu", "/wizard", "menu", "wizard"):
            interactive_session_loop(ctx)

        elif cmd in ("/clear", "/cls", "clear", "cls"):
            console.clear()

        elif cmd == "/inspect":
            if not args:
                console.print("[yellow]Usage: /inspect <file_path>[/yellow]")
                continue
            t0 = time.perf_counter()
            with console.status(
                f"[bold cyan]Reading audio metadata for {args[0]}...[/bold cyan]"
            ):
                try:
                    ctx.invoke(inspect_cmd, file_path=args[0], json_out=False)
                except Exception as e:
                    console.print(f"[red]Error:[/red] {e}")
            console.print(f"[dim]Finished in {time.perf_counter() - t0:.2f}s[/dim]")

        elif cmd == "/match":
            if not args:
                console.print("[yellow]Usage: /match <file_path> [provider][/yellow]")
                continue
            prov = args[1] if len(args) > 1 else "multi"
            t0 = time.perf_counter()
            with console.status(
                f"[bold cyan]Querying {prov} providers for {args[0]}...[/bold cyan]"
            ):
                try:
                    ctx.invoke(match_cmd, file_path=args[0], provider=prov)
                except Exception as e:
                    console.print(f"[red]Error:[/red] {e}")
            console.print(
                f"[dim]Completed query in {time.perf_counter() - t0:.2f}s[/dim]"
            )

        elif cmd == "/tag":
            if not args:
                console.print("[yellow]Usage: /tag <file_path> [provider][/yellow]")
                continue
            prov = args[1] if len(args) > 1 else "multi"
            try:
                ctx.invoke(
                    tag_cmd,
                    file_path=args[0],
                    provider=prov,
                    interactive=True,
                    dry_run=False,
                )
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

        elif cmd == "/replaygain":
            if not args:
                console.print("[yellow]Usage: /replaygain <file_or_directory>[/yellow]")
                continue
            try:
                ctx.invoke(replaygain_cmd, target=args[0], dry_run=False)
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

        elif cmd == "/doctor":
            ctx.invoke(doctor_cmd, json_out=False)

        elif cmd == "/history":
            ctx.invoke(history_cmd, limit=10, json_out=False)

        elif cmd.startswith("@"):
            file_target = cmd.lstrip("@")
            try:
                ctx.invoke(inspect_cmd, file_path=file_target, json_out=False)
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

        else:
            console.print(
                f"[yellow]Unknown command '{cmd}'. Type /help for available commands.[/yellow]"
            )


@click.command("repl")
@click.pass_context
def repl_cmd(ctx: click.Context) -> None:
    """Alias for 'session'."""
    ctx.invoke(session_cmd)


@click.command("tui")
def tui_cmd() -> None:
    """Launch the Textual full-terminal TUI workstation."""
    from patangoma.bootstrap.application import create_application
    from patangoma.frontends.tui.app import PataNgomaTUIApp

    app_platform = create_application()
    tui_app = PataNgomaTUIApp(app_platform)
    tui_app.run()


@click.command("gui")
def gui_cmd() -> None:
    """Launch the desktop GUI workstation."""
    from patangoma.frontends.gui.app import PataNgomaGUIApp

    gui_app = PataNgomaGUIApp()
    gui_app.run()


@click.command("show")
@click.option("--all_t", "-a", is_flag=True, default=False, help="Show all metadata.")
@click.option(
    "--existing", "-e", is_flag=True, default=True, help="Show only existing metadata."
)
@click.option(
    "--missing", "-m", is_flag=True, default=False, help="Show missing metadata."
)
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
@click.pass_context
def show_cmd(
    ctx: click.Context,
    file_path: str,
    all_t: bool,
    existing: bool,
    missing: bool,
) -> None:
    """Show metadata for a media file <file_path>."""
    from patangoma.frontends.cli.commands.scan import inspect_cmd

    ctx.invoke(inspect_cmd, file_path=file_path, json_out=False)


@click.command("update")
@click.argument(
    "file_path", type=click.Path(exists=True, resolve_path=True, dir_okay=False)
)
@click.argument("updates", nargs=-1)
def update_cmd(file_path: str, updates: tuple[str, ...]) -> None:
    """Update metadata for a media file <file_path>."""
    tag_dict: dict[str, Any] = {}
    for item in updates:
        if "=" in item:
            k, v = item.split("=", 1)
            tag_dict[k.strip()] = v.strip()

    if not tag_dict:
        console.print("[yellow]No key=value update arguments provided.[/yellow]")
        return

    try:
        backend.write_tags(file_path, tag_dict, dry_run=False)
        console.print(
            f"[bold green]✓ Updated tags for {Path(file_path).name}:[/bold green] {list(tag_dict.keys())}"
        )
    except Exception as e:
        console.print(f"[bold red]Failed to update tags:[/bold red] {e}")
        sys.exit(1)
