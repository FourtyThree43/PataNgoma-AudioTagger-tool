"""Textual TUI Workstation interface for PataNgoma."""

from __future__ import annotations

from typing import ClassVar

from patangoma.application.facade import PataNgomaApplication
from patangoma.bootstrap.application import create_application
from patangoma.frontends.tui.screens import TUIScreenModel


class PataNgomaTUIApp:
    """Terminal workstation presentation adapter over PataNgomaApplication."""

    def __init__(self, app: PataNgomaApplication | None = None) -> None:
        self.app = app or create_application()
        self.model = TUIScreenModel(self.app)

    def run(self) -> None:
        """Launch the Textual interactive terminal application."""
        try:
            from textual.app import App, ComposeResult
            from textual.binding import Binding
            from textual.widgets import (
                DataTable,
                Footer,
                Header,
                Input,
                Label,
                Static,
                TabbedContent,
                TabPane,
            )

            class TextualWorkstation(App):
                TITLE = "PataNgoma Audio Workstation"
                SUB_TITLE = "Multi-Provider Audio Intelligence"
                CSS = """
                Screen {
                    background: $surface;
                }
                #sidebar {
                    width: 32;
                    dock: left;
                    background: $panel;
                    padding: 1;
                }
                #main-content {
                    padding: 1;
                }
                DataTable {
                    height: 1fr;
                }
                """

                BINDINGS: ClassVar[list[Binding]] = [
                    Binding("q", "quit", "Quit", show=True),
                    Binding("d", "switch_tab('dashboard')", "Dashboard", show=True),
                    Binding("l", "switch_tab('library')", "Library", show=True),
                    Binding("m", "switch_tab('matching')", "Match", show=True),
                    Binding("j", "switch_tab('jobs')", "Jobs", show=True),
                    Binding("h", "switch_tab('health')", "Health", show=True),
                ]

                def compose(self) -> ComposeResult:
                    yield Header()
                    with TabbedContent(initial="dashboard", id="tabs"):
                        with TabPane("Dashboard", id="dashboard"):
                            yield Static(
                                "♥ PataNgoma Audio Intelligence Workstation ♥",
                                classes="title",
                            )
                            yield Label(
                                "Press 'l' for Library, 'm' for Matching, 'j' for Jobs, 'h' for Health"
                            )

                        with TabPane("Library", id="library"):
                            yield Input(
                                placeholder="Enter folder path to scan...",
                                id="path-input",
                            )
                            yield DataTable(id="library-table")

                        with TabPane("Matching", id="matching"):
                            yield Label("Metadata Candidates & Match Inspector")
                            yield DataTable(id="candidate-table")

                        with TabPane("Jobs", id="jobs"):
                            yield Label("Active Background Jobs")
                            yield DataTable(id="jobs-table")

                        with TabPane("Health", id="health"):
                            yield Label("System Diagnostics & Provider Status")
                            yield Static(id="health-details")

                    yield Footer()

                def action_switch_tab(self, tab_id: str) -> None:
                    tabs = self.query_one(TabbedContent)
                    tabs.active = tab_id

            ui = TextualWorkstation()
            ui.run()
        except ImportError as e:
            raise RuntimeError(
                "Textual is not installed. Install it with: uv sync --extra tui"
            ) from e
