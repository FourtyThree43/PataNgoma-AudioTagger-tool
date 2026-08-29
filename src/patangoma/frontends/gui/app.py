"""GUI Desktop Workstation interface placeholder for PataNgoma."""

from __future__ import annotations

from patangoma.application.facade import PataNgomaApplication
from patangoma.bootstrap.application import create_application
from patangoma.frontends.gui.view_models import (
    DiagnosticsViewModel,
    JobMonitorViewModel,
    LibraryViewModel,
    TagEditorViewModel,
)


class PataNgomaGUIApp:
    """Desktop workstation presentation adapter over PataNgomaApplication."""

    def __init__(self, app: PataNgomaApplication | None = None) -> None:
        self.app = app or create_application()
        self.library_vm = LibraryViewModel(self.app)
        self.editor_vm = TagEditorViewModel(self.app)
        self.jobs_vm = JobMonitorViewModel(self.app)
        self.diagnostics_vm = DiagnosticsViewModel(self.app)

    def run(self) -> None:
        """Launch the GUI desktop application workstation."""
        try:
            import ttkbootstrap as ttk

            # Full ttkbootstrap desktop application setup placeholder
            root = ttk.Window(title="PataNgoma Audio Workstation", themename="darkly")
            root.geometry("1024x768")
            ttk.Label(
                root, text="PataNgoma Desktop Workstation", font=("Helvetica", 16)
            ).pack(pady=20)
            root.mainloop()
        except ImportError as e:
            raise RuntimeError(
                "ttkbootstrap is not installed. Install it with: uv sync --extra gui"
            ) from e
