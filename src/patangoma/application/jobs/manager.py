"""Background job management and task execution."""

from __future__ import annotations

import concurrent.futures
import threading
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from patangoma.domain.exceptions import JobNotFoundError
from patangoma.domain.models import JobDescriptor, JobProgress, JobStatus
from patangoma.infrastructure.persistence.contracts import JobRepository
from patangoma.infrastructure.persistence.memory_repo import InMemoryJobRepository


class JobManager:
    """Manager for scheduling, executing, and tracking background operations."""

    def __init__(
        self,
        repository: JobRepository | None = None,
        max_workers: int = 4,
    ) -> None:
        self._repo = repository or InMemoryJobRepository()
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="patangoma-worker"
        )
        self._active_futures: dict[str, concurrent.futures.Future] = {}
        self._cancel_flags: dict[str, threading.Event] = {}

    def create_job(self, name: str, operation: str) -> JobDescriptor:
        """Create a new job record in PENDING state."""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        job = JobDescriptor(
            job_id=job_id,
            name=name,
            operation=operation,
            status=JobStatus.PENDING,
            progress=JobProgress(current_item=0, total_items=0, percentage=0.0),
        )
        self._repo.save(job)
        self._cancel_flags[job_id] = threading.Event()
        return job

    def start_job(
        self,
        job_id: str,
        target: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> JobDescriptor:
        """Submit job target to thread pool and begin execution."""
        job = self._repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(f"Job '{job_id}' not found")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        self._repo.save(job)

        cancel_event = self._cancel_flags.setdefault(job_id, threading.Event())

        def _worker_wrapper() -> Any:
            try:
                result = target(cancel_event, *args, **kwargs)
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                if isinstance(result, dict):
                    job.result_summary = result
                self._repo.save(job)
                return result
            except Exception as e:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                job.error_message = str(e)
                self._repo.save(job)
                raise

        future = self._executor.submit(_worker_wrapper)
        self._active_futures[job_id] = future
        return job

    def update_progress(
        self,
        job_id: str,
        current: int,
        total: int,
        message: str = "",
        label: str = "",
    ) -> None:
        """Update progress metrics of a running job."""
        job = self._repo.get_by_id(job_id)
        if not job:
            return

        pct = (current / total * 100.0) if total > 0 else 0.0
        job.progress = JobProgress(
            current_item=current,
            total_items=total,
            percentage=round(pct, 2),
            message=message,
            current_label=label,
        )
        self._repo.save(job)

    def get_job(self, job_id: str) -> JobDescriptor | None:
        """Retrieve job descriptor by ID."""
        return self._repo.get_by_id(job_id)

    def list_jobs(self, limit: int = 50) -> list[JobDescriptor]:
        """List recent jobs."""
        return self._repo.list_all(limit=limit)

    def cancel_job(self, job_id: str) -> bool:
        """Signal job cancellation."""
        job = self._repo.get_by_id(job_id)
        if not job:
            return False

        if flag := self._cancel_flags.get(job_id):
            flag.set()

        if future := self._active_futures.get(job_id):
            future.cancel()

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        self._repo.save(job)
        return True

    def shutdown(self, wait: bool = False) -> None:
        """Gracefully shut down the executor pool."""
        self._executor.shutdown(wait=wait)
