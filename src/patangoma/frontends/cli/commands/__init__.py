"""CLI commands registration package."""

from patangoma.frontends.cli.commands.audio import (
    lyrics_cmd,
    replaygain_cmd,
    transcode_check_cmd,
    verify_cmd,
)
from patangoma.frontends.cli.commands.doctor import doctor_cmd
from patangoma.frontends.cli.commands.interactive import (
    gui_cmd,
    interactive_session_loop,
    repl_cmd,
    session_cmd,
    show_cmd,
    tui_cmd,
    update_cmd,
)
from patangoma.frontends.cli.commands.jobs import jobs_group
from patangoma.frontends.cli.commands.library import (
    cue_inspect_cmd,
    delete_cmd,
    demo_library_cmd,
    duplicates_cmd,
    edit_cmd,
    export_catalog_cmd,
    normalize_genres_cmd,
    playlist_export_cmd,
    rename_cmd,
    search_cmd,
)
from patangoma.frontends.cli.commands.match import (
    match_cmd,
    reason_cmd,
    tag_cmd,
)
from patangoma.frontends.cli.commands.plan import plan_cmd, plan_dir_cmd
from patangoma.frontends.cli.commands.plugins import plugins_group
from patangoma.frontends.cli.commands.rollback import (
    export_audit_cmd,
    history_cmd,
    rollback_cmd,
)
from patangoma.frontends.cli.commands.scan import (
    check_file_cmd,
    inspect_cmd,
    scan_cmd,
)

__all__ = [
    "check_file_cmd",
    "cue_inspect_cmd",
    "delete_cmd",
    "demo_library_cmd",
    "doctor_cmd",
    "duplicates_cmd",
    "edit_cmd",
    "export_audit_cmd",
    "export_catalog_cmd",
    "gui_cmd",
    "history_cmd",
    "inspect_cmd",
    "interactive_session_loop",
    "jobs_group",
    "lyrics_cmd",
    "match_cmd",
    "normalize_genres_cmd",
    "plan_cmd",
    "plan_dir_cmd",
    "playlist_export_cmd",
    "plugins_group",
    "reason_cmd",
    "rename_cmd",
    "repl_cmd",
    "replaygain_cmd",
    "rollback_cmd",
    "scan_cmd",
    "search_cmd",
    "session_cmd",
    "show_cmd",
    "tag_cmd",
    "transcode_check_cmd",
    "tui_cmd",
    "update_cmd",
    "verify_cmd",
]
