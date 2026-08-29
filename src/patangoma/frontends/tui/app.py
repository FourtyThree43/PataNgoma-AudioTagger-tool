"""Textual TUI Workstation interface for PataNgoma."""

from __future__ import annotations

from patangoma.application.facade import PataNgomaApplication
from patangoma.bootstrap.application import create_application


class PataNgomaTUIApp:
    """Terminal workstation presentation adapter over PataNgomaApplication."""

    def __init__(self, app: PataNgomaApplication | None = None) -> None:
        self.app = app or create_application()

    def run(self) -> None:
        """Launch the Textual interactive terminal application."""
        try:
            from textual.app import App, ComposeResult
            from textual.widgets import Footer, Header, Static

            class _TextualWorkstation(App):
                TITLE = "PataNgoma Audio Workstation"
                SUB_TITLE = "Terminal UI"

                def compose(self) -> ComposeResult:
                    yield Header()
                    yield Static("PataNgoma Terminal Workstation - Active")
                    yield Footer()

            ui = _TextualWorkstation()
            ui.run()
        except ImportError as e:
            raise RuntimeError(
                "Textual is not installed. Install it with: uv sync --extra tui"
            ) from e
