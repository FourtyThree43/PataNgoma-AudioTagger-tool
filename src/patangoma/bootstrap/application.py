"""Composition root for constructing the PataNgoma application graph."""

from __future__ import annotations

from pathlib import Path

from patangoma.application.events.bus import EventBus
from patangoma.application.facade import PataNgomaApplication
from patangoma.application.jobs.manager import JobManager
from patangoma.infrastructure.configuration.manager import (
    ConfigurationManager,
    default_config_path,
)
from patangoma.infrastructure.logging.logger import get_logger
from patangoma.infrastructure.media.backend import MediaFileAudioBackend
from patangoma.infrastructure.persistence.sqlite_repo import (
    SQLiteJobRepository,
)
from patangoma.plugins.discovery import create_default_plugin_registry
from patangoma.services.audit import AuditJournal, default_audit_db_path


def create_application(
    config_path: Path | None = None,
    audit_db_path: Path | None = None,
) -> PataNgomaApplication:
    """Build and return a fully wired PataNgomaApplication instance."""
    cfg = ConfigurationManager(config_path=config_path or default_config_path())
    logger = get_logger("patangoma")

    audit_path = audit_db_path or default_audit_db_path()
    audit_journal = AuditJournal(db_path=audit_path)
    job_repo = SQLiteJobRepository(db_path=audit_path)

    backend = MediaFileAudioBackend()
    plugin_registry = create_default_plugin_registry()
    job_manager = JobManager(repository=job_repo)
    event_bus = EventBus()

    app = PataNgomaApplication(
        backend=backend,
        plugin_registry=plugin_registry,
        config=cfg,
        audit_journal=audit_journal,
        job_manager=job_manager,
        event_bus=event_bus,
    )

    logger.debug("PataNgoma application graph constructed successfully")
    return app
