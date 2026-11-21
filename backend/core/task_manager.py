"""
Asynchronous In-Memory Task Manager.

Provides a clean task management abstraction for long-running document analyses
and multi-stage verification jobs:
- Dispatches tasks to background asyncio worker.
- Provides thread-safe task status and result retrieval.
- Exposes task IDs and polling states.
- Cleanly decoupled via TaskManagerBase so it can be swapped for Redis / Celery in Phase 9.

IMPORTANT MVP LIMITATIONS:
- In-memory tasks are bound to the process lifecycle.
- Server restart, crash, or worker termination will result in task loss.
- Suitable for local development and single-instance deployments; distributed horizontal
  scaling requires the Phase 9 Celery/Redis persistent adapter.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Coroutine
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskRecord(BaseModel):
    task_id: str
    status: TaskStatus
    progress: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskManagerBase(ABC):
    """Abstract interface for task scheduling and state tracking."""

    @abstractmethod
    async def enqueue(self, coroutine_func: Callable[..., Coroutine], *args: Any, **kwargs: Any) -> str:
        """Enqueue a background task and return unique task_id."""
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """Retrieve the current state of a task."""
        pass


class InMemoryTaskManager(TaskManagerBase):
    """
    In-memory task manager for Phase 0-7.
    """

    def __init__(self):
        self._tasks: Dict[str, TaskRecord] = {}

    async def enqueue(self, coroutine_func: Callable[..., Coroutine], *args: Any, **kwargs: Any) -> str:
        task_id = f"task_{uuid.uuid4().hex}"
        record = TaskRecord(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0.0,
        )
        self._tasks[task_id] = record

        # Launch background execution using ensure_future / create_task on active loop
        loop = asyncio.get_running_loop()
        loop.create_task(self._run_task(task_id, coroutine_func, *args, **kwargs))
        return task_id

    async def _run_task(self, task_id: str, coroutine_func: Callable[..., Coroutine], *args: Any, **kwargs: Any) -> None:
        record = self._tasks[task_id]
        record.status = TaskStatus.PROCESSING
        record.progress = 0.1

        try:
            result = await coroutine_func(*args, **kwargs)
            record.status = TaskStatus.COMPLETED
            record.progress = 1.0
            record.result = result if isinstance(result, dict) else {"data": result}
            record.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            record.status = TaskStatus.FAILED
            record.error = str(e)
            record.completed_at = datetime.now(timezone.utc)

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return self._tasks.get(task_id)


# Global task manager instance
task_manager = InMemoryTaskManager()
