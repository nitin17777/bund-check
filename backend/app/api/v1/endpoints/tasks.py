"""
Task Status Polling Endpoint.

GET /api/v1/tasks/{task_id}
  - Returns task status, progress, and result when complete.
  - Used for async check and improve operations exceeding the sync threshold.

Contracts match API_SPEC.md § 3.4.
"""

from fastapi import APIRouter, Request

from backend.app.core.task_manager import task_manager, TaskStatus
from backend.app.core.errors import DocumentProcessingException, ErrorDetail
from backend.app.core.security import get_limiter
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
limiter = get_limiter()
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "/{task_id}",
    responses={
        200: {"description": "Task status and optional result."},
        404: {"description": "Task not found or expired."},
        429: {"description": "Rate limit exceeded."},
    },
)
@limiter.limit("120/minute")
async def get_task_status(task_id: str, request: Request):
    """
    Poll the status of an asynchronous task.

    Returns:
      - status: pending | processing | completed | failed
      - progress: float [0.0, 1.0] when processing
      - result: populated when status == completed
      - error: populated when status == failed
    """
    record = await task_manager.get_status(task_id)
    if record is None:
        raise DocumentProcessingException(
            status_code=404,
            code="TASK_NOT_FOUND",
            message=f"Task '{task_id}' not found or has expired (TTL: 30 minutes).",
            details=[ErrorDetail(field="task_id", issue="Unknown or expired task identifier.")],
        )

    logger.info(
        "task_poll",
        task_id=task_id,
        status=record.status,
        progress=record.progress,
    )

    response: dict = {
        "task_id": record.task_id,
        "status": record.status.value,
        "progress": record.progress,
        "created_at": record.created_at,
        "estimated_time_ms": record.estimated_time_ms,
    }

    if record.status == TaskStatus.COMPLETED:
        # Serialize pydantic result if present
        result = record.result
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        response["result"] = result

    if record.status == TaskStatus.FAILED:
        response["error"] = record.error

    return response
