"""Shared state and singletons for the PataNgoma CLI frontend."""

from __future__ import annotations

import warnings
from importlib.metadata import PackageNotFoundError, version

from rich.console import Console
from rich.panel import Panel

from patangoma.matching.matcher import MatchingEngine
from patangoma.services.ai_reasoner import MetadataReasoner
from patangoma.services.audio_backend import AudioBackend
from patangoma.services.audit import AuditJournal
from patangoma.services.batch import BatchService
from patangoma.services.planner import PlanEngine

# Suppress non-official JSON warnings from upstream libraries
warnings.filterwarnings(
    "ignore", message="The json format is non-official", category=UserWarning
)

console = Console()
backend = AudioBackend()
planner = PlanEngine()
audit_journal = AuditJournal()
matching_engine = MatchingEngine()
batch_service = BatchService(backend, planner, matching_engine, audit_journal)
reasoner = MetadataReasoner()


def get_app_info() -> tuple[str, str]:
    """Get application name and version."""
    app_name = "PataNgoma"
    try:
        app_version = version("patangoma")
    except PackageNotFoundError:
        app_version = "1.5.0"
    return app_name, app_version or "1.5.0"


def app_info() -> None:
    """Print welcome banner to console."""
    app_name, app_version = get_app_info()
    console.print(
        Panel.fit(
            f"[bold red]♥[/bold red] [bold yellow]{app_name}[/bold yellow] - [bold white]v{app_version}[/bold white] [bold red]♥[/bold red]\n"
            "[cyan]Deterministic Music Metadata Intelligence Platform[/cyan]",
            border_style="red",
        )
    )
