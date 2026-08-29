"""Command Line Interface entrypoint for PataNgoma AudioTagger."""

from __future__ import annotations

from patangoma.frontends.cli.commands import (
    check_file_cmd as check_file,
)
from patangoma.frontends.cli.commands import (
    cue_inspect_cmd as cue_inspect,
)
from patangoma.frontends.cli.commands import (
    delete_cmd as delete,
)
from patangoma.frontends.cli.commands import (
    demo_library_cmd as demo_library,
)
from patangoma.frontends.cli.commands import (
    doctor_cmd as doctor,
)
from patangoma.frontends.cli.commands import (
    duplicates_cmd as duplicates,
)
from patangoma.frontends.cli.commands import (
    edit_cmd as edit,
)
from patangoma.frontends.cli.commands import (
    export_audit_cmd as export_audit,
)
from patangoma.frontends.cli.commands import (
    export_catalog_cmd as export_catalog,
)
from patangoma.frontends.cli.commands import (
    gui_cmd as gui,
)
from patangoma.frontends.cli.commands import (
    history_cmd as history,
)
from patangoma.frontends.cli.commands import (
    inspect_cmd as inspect,
)
from patangoma.frontends.cli.commands import (
    lyrics_cmd as get_lyrics,
)
from patangoma.frontends.cli.commands import (
    match_cmd as match,
)
from patangoma.frontends.cli.commands import (
    normalize_genres_cmd as normalize_genres,
)
from patangoma.frontends.cli.commands import (
    plan_cmd as plan,
)
from patangoma.frontends.cli.commands import (
    plan_dir_cmd as plan_dir,
)
from patangoma.frontends.cli.commands import (
    playlist_export_cmd as playlist_export,
)
from patangoma.frontends.cli.commands import (
    reason_cmd as reason,
)
from patangoma.frontends.cli.commands import (
    rename_cmd as rename,
)
from patangoma.frontends.cli.commands import (
    repl_cmd as repl_alias,
)
from patangoma.frontends.cli.commands import (
    replaygain_cmd as replaygain,
)
from patangoma.frontends.cli.commands import (
    rollback_cmd as rollback,
)
from patangoma.frontends.cli.commands import (
    scan_cmd as scan,
)
from patangoma.frontends.cli.commands import (
    search_cmd as search,
)
from patangoma.frontends.cli.commands import (
    session_cmd,
)
from patangoma.frontends.cli.commands import (
    show_cmd as show,
)
from patangoma.frontends.cli.commands import (
    tag_cmd as tag,
)
from patangoma.frontends.cli.commands import (
    transcode_check_cmd as transcode_check,
)
from patangoma.frontends.cli.commands import (
    tui_cmd as tui,
)
from patangoma.frontends.cli.commands import (
    update_cmd as update,
)
from patangoma.frontends.cli.commands import (
    verify_cmd as verify,
)
from patangoma.frontends.cli.commands.apply import (
    apply_cmd as apply,
)
from patangoma.frontends.cli.commands.apply import (
    apply_dir_cmd as apply_dir,
)
from patangoma.frontends.cli.helpers import query_candidates as _query_candidates
from patangoma.frontends.cli.root import cli
from patangoma.frontends.cli.state import (
    app_info,
    audit_journal,
    backend,
    batch_service,
    console,
    get_app_info,
    matching_engine,
    planner,
    reasoner,
)

__all__ = [
    "_query_candidates",
    "app_info",
    "apply",
    "apply_dir",
    "audit_journal",
    "backend",
    "batch_service",
    "check_file",
    "cli",
    "console",
    "cue_inspect",
    "delete",
    "demo_library",
    "doctor",
    "duplicates",
    "edit",
    "export_audit",
    "export_catalog",
    "get_app_info",
    "get_lyrics",
    "gui",
    "history",
    "inspect",
    "match",
    "matching_engine",
    "normalize_genres",
    "plan",
    "plan_dir",
    "planner",
    "playlist_export",
    "reason",
    "reasoner",
    "rename",
    "repl_alias",
    "replaygain",
    "rollback",
    "scan",
    "search",
    "session_cmd",
    "show",
    "tag",
    "transcode_check",
    "tui",
    "update",
    "verify",
]

if __name__ == "__main__":
    cli()
