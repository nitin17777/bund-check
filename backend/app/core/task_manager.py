"""
In-Memory Async Task Manager.

Provides an abstract TaskManager interface + concrete InMemoryTaskManager
backed by asyncio background tasks and thread-safe state storage.

Design constraints (Phase 7 / 9):
- Abstracted so Redis/Celery can be dropped in later without changing API contracts.
- Tasks identified by UUIDs; state stored in a module-level dict protected by asyncio.Lock.
- Results held until explicitly expired (TTL: 30 minutes) to allow polling.
- No task result ever persists document text to disk — results contain only analysis metadata.

Usage:
    from backend.app.core.task_manager import task_manager

    task_id = await task_manager.submit(my_coroutine_or_callable, *args, **kwargs)
    status = await task_manager.get_status(task_id)
    result = await task_manager.get_result(task_id)
"""

import asyncio
import uuid
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field

from backend.app.core.logging import get_logger

logger = get_logger(__name__)

# Task result TTL: 30 minutes in seconds
TASK_RESULT_TTL_SECONDS = 30 * 60


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskRecord:
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.monotonic)
    completed_at: Optional[float] = None
    _asyncio_task: Optional[asyncio.Task] = field(default=None, repr=False)

    @property
    def estimated_time_ms(self) -> int:
        """Rough estimate based on elapsed time and progress."""
        if self.progress <= 0:
            return 3000
        elapsed = time.monotonic() - self.created_at
        if self.progress >= 1.0:
            return 0
        remaining = (elapsed / self.progress) * (1.0 - self.progress)
        return int(remaining * 1000)

    @property
    def is_expired(self) -> bool:
        if self.completed_at is None:
            return False
        return (time.monotonic() - self.completed_at) > TASK_RESULT_TTL_SECONDS


class InMemoryTaskManager:
    """
    Thread-safe, in-memory task manager backed by asyncio tasks.

    Limitations documented:
    - Single-process only. For multi-instance deployments, replace with
      Redis-backed storage and Celery worker pool.
    - Tasks are lost on server restart (in-memory only).
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock_obj: Optional[asyncio.Lock] = None
        self._lock_loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def _lock(self) -> asyncio.Lock:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if self._lock_obj is None or self._lock_loop is not loop:
            self._lock_obj = asyncio.Lock()
            self._lock_loop = loop
        return self._lock_obj

    def _generate_task_id(self) -> str:
        return f"task_{uuid.uuid4().hex[:12]}"

    async def submit(
        self,
        fn: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Submit a synchronous callable to run in a thread pool.
        Returns a task_id immediately.
        """
        task_id = self._generate_task_id()
        record = TaskRecord(task_id=task_id)

        async with self._lock:
            self._tasks[task_id] = record

        async def _runner() -> None:
            async with self._lock:
                record.status = TaskStatus.PROCESSING
                record.progress = 0.1
            try:
                result = await asyncio.to_thread(fn, *args, **kwargs)
                async with self._lock:
                    record.status = TaskStatus.COMPLETED
                    record.progress = 1.0
                    record.result = result
                    record.completed_at = time.monotonic()
                logger.info("task_completed", task_id=task_id)
            except Exception as exc:
                async with self._lock:
                    record.status = TaskStatus.FAILED
                    record.error = str(exc)
                    record.completed_at = time.monotonic()
                logger.error("task_failed", task_id=task_id, error=str(exc))

        asyncio_task = asyncio.create_task(_runner())
        async with self._lock:
            record._asyncio_task = asyncio_task

        logger.info("task_submitted", task_id=task_id)
        return task_id

    async def get_status(self, task_id: str) -> Optional[TaskRecord]:
        """Return the TaskRecord for the given task_id, or None if not found."""
        async with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                return None
            # Expire and remove stale completed tasks
            if record.is_expired:
                del self._tasks[task_id]
                return None
            return record

    async def update_progress(self, task_id: str, progress: float) -> None:
        """Update the progress fraction [0.0, 1.0] for a running task."""
        async with self._lock:
            record = self._tasks.get(task_id)
            if record and record.status == TaskStatus.PROCESSING:
                record.progress = max(0.0, min(1.0, progress))

    async def cleanup_expired(self) -> int:
        """Remove expired task records. Returns count removed."""
        removed = 0
        async with self._lock:
            expired_ids = [
                tid for tid, rec in self._tasks.items() if rec.is_expired
            ]
            for tid in expired_ids:
                del self._tasks[tid]
                removed += 1
        if removed:
            logger.info("tasks_expired_cleaned", count=removed)
        return removed

    @property
    def active_task_count(self) -> int:
        return len(self._tasks)


# Module-level singleton
task_manager = InMemoryTaskManager()
