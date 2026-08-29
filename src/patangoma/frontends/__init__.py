"""Frontends package providing CLI, TUI, and GUI presentation adapters."""

from patangoma.frontends.cli import cli
from patangoma.frontends.gui import PataNgomaGUIApp
from patangoma.frontends.tui import PataNgomaTUIApp

__all__ = [
    "PataNgomaGUIApp",
    "PataNgomaTUIApp",
    "cli",
]
