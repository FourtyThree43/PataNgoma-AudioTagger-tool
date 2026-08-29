"""Root Click CLI entrypoint registering all modular command groups."""

from __future__ import annotations

import click

from patangoma.frontends.cli.commands import (
    check_file_cmd,
    cue_inspect_cmd,
    delete_cmd,
    demo_library_cmd,
    doctor_cmd,
    duplicates_cmd,
    edit_cmd,
    export_audit_cmd,
    export_catalog_cmd,
    gui_cmd,
    history_cmd,
    inspect_cmd,
    interactive_session_loop,
    jobs_group,
    lyrics_cmd,
    match_cmd,
    normalize_genres_cmd,
    plan_cmd,
    plan_dir_cmd,
    playlist_export_cmd,
    plugins_group,
    reason_cmd,
    rename_cmd,
    repl_cmd,
    replaygain_cmd,
    rollback_cmd,
    scan_cmd,
    search_cmd,
    session_cmd,
    show_cmd,
    tag_cmd,
    transcode_check_cmd,
    tui_cmd,
    update_cmd,
    verify_cmd,
)
from patangoma.frontends.cli.commands.apply import apply_cmd, apply_dir_cmd
from patangoma.frontends.cli.state import app_info


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, dir_okay=True, resolve_path=True),
    help="Path to the audio file or its parent directory",
)
def cli(ctx: click.Context, path: str | None) -> None:
    """PataNgoma AudioTagger CLI."""
    if ctx.invoked_subcommand is None:
        app_info()
        interactive_session_loop(ctx, initial_path=path)


# Register all subcommands
cli.add_command(scan_cmd, name="scan")
cli.add_command(inspect_cmd, name="inspect")
cli.add_command(check_file_cmd, name="check-file")
cli.add_command(match_cmd, name="match")
cli.add_command(reason_cmd, name="reason")
cli.add_command(tag_cmd, name="tag")
cli.add_command(plan_cmd, name="plan")
cli.add_command(plan_dir_cmd, name="plan-dir")
cli.add_command(apply_cmd, name="apply")
cli.add_command(apply_dir_cmd, name="apply-dir")
cli.add_command(rollback_cmd, name="rollback")
cli.add_command(history_cmd, name="history")
cli.add_command(export_audit_cmd, name="export-audit")
cli.add_command(duplicates_cmd, name="duplicates")
cli.add_command(rename_cmd, name="rename")
cli.add_command(normalize_genres_cmd, name="normalize-genres")
cli.add_command(playlist_export_cmd, name="playlist-export")
cli.add_command(cue_inspect_cmd, name="cue-inspect")
cli.add_command(edit_cmd, name="edit")
cli.add_command(export_catalog_cmd, name="export-catalog")
cli.add_command(demo_library_cmd, name="demo-library")
cli.add_command(delete_cmd, name="delete")
cli.add_command(search_cmd, name="search")
cli.add_command(lyrics_cmd, name="lyrics")
cli.add_command(replaygain_cmd, name="replaygain")
cli.add_command(verify_cmd, name="verify")
cli.add_command(transcode_check_cmd, name="transcode-check")
cli.add_command(doctor_cmd, name="doctor")
cli.add_command(plugins_group, name="plugins")
cli.add_command(jobs_group, name="jobs")
cli.add_command(session_cmd, name="session")
cli.add_command(repl_cmd, name="repl")
cli.add_command(tui_cmd, name="tui")
cli.add_command(gui_cmd, name="gui")
cli.add_command(show_cmd, name="show")
cli.add_command(update_cmd, name="update")
