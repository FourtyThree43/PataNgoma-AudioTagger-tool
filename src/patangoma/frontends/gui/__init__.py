"""GUI frontend package for PataNgoma."""

from patangoma.frontends.gui.app import PataNgomaGUIApp
from patangoma.frontends.gui.view_models import (
    DiagnosticsViewModel,
    JobMonitorViewModel,
    LibraryViewModel,
    TagEditorViewModel,
)

__all__ = [
    "DiagnosticsViewModel",
    "JobMonitorViewModel",
    "LibraryViewModel",
    "PataNgomaGUIApp",
    "TagEditorViewModel",
]
