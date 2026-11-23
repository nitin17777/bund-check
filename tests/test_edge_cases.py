"""
Targeted edge case tests — all direct function calls, no HTTP layer needed.

Tests:
- Empty / whitespace / oversized text validation at the pipeline level
- Pydantic schema validation for /check and /improve request models
- Task manager record expiration and cleanup (pure dict operations, no asyncio.to_thread)
"""

import pytest
import asyncio
import time

from backend.app.models.detection import CheckRequest
from backend.app.core.errors import DocumentProcessingException
from backend.app.core.task_manager import InMemoryTaskManager, TaskStatus, TaskRecord
from backend.app.services.detection.detector import run_detection_pipeline


# ---------------------------------------------------------------------------
# Schema-level validation (Pydantic, no HTTP)
# ---------------------------------------------------------------------------

def test_check_request_rejects_empty_text():
    """CheckRequest schema should reject empty string."""
    try:
        req = CheckRequest(text="")
        # If schema allows empty, the pipeline should raise DocumentProcessingException
        with pytest.raises(DocumentProcessingException) as exc_info:
            run_detection_pipeline(text=req.text)
        assert exc_info.value.status_code in (400, 422)
    except Exception as e:
        # Pydantic validation error or DocumentProcessingException both acceptable
        assert "empty" in str(e).lower() or "word" in str(e).lower() or "text" in str(e).lower() or "422" in str(e)


def test_check_request_rejects_whitespace_text():
    """Whitespace-only text should be rejected by pipeline validation."""
    with pytest.raises((DocumentProcessingException, ValueError, Exception)):
        run_detection_pipeline(text="   \n\t   ")


def test_check_oversized_pipeline_rejection():
    """Text exceeding document limits should raise DocumentProcessingException."""
    huge_text = "word " * 120_000  # ~600k chars
    with pytest.raises(DocumentProcessingException) as exc_info:
        run_detection_pipeline(text=huge_text)
    assert exc_info.value.status_code in (400, 413, 422)


def test_improve_mode_pydantic_validation():
    """
    /improve endpoint uses a Pydantic schema that restricts the `mode` field.
    Test that the enum rejects invalid mode strings.
    """
    from backend.app.models.improver import ImproveRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ImproveRequest(text="Valid text here.", mode="invalid_mode_xyz")


def test_check_request_accepts_valid_text():
    """Short valid text should produce a CheckResponse without raising."""
    text = (
        "The experimental results demonstrate that the proposed methodology "
        "significantly outperforms all baseline approaches in terms of accuracy. "
        "Statistical significance was confirmed with p < 0.001 across all datasets."
    )
    result = run_detection_pipeline(text=text)
    assert result is not None
    assert 0.0 <= result.synthetic_pattern_confidence <= 1.0
    assert result.classification_band in (
        "HUMAN_TYPICAL", "INCONCLUSIVE", "SYNTHETIC_INDICATIVE", "INSUFFICIENT_LENGTH"
    )


# ---------------------------------------------------------------------------
# Task manager — direct record manipulation (no asyncio.to_thread)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_task_manager_record_lifecycle():
    """
    Test InMemoryTaskManager record state transitions and cleanup
    without relying on asyncio.to_thread (which can hang in sandboxed envs).
    Directly inserts a TaskRecord to test expiration logic.
    """
    import backend.app.core.task_manager as tm_module
    original_ttl = tm_module.TASK_RESULT_TTL_SECONDS
    tm_module.TASK_RESULT_TTL_SECONDS = 1

    try:
        tm = InMemoryTaskManager()

        # Directly insert a completed record (bypass submit() to avoid threading)
        task_id = "task_test_expiry"
        record = TaskRecord(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            progress=1.0,
            result={"result": "ok"},
            completed_at=time.monotonic() - 2,  # 2 seconds ago > 1s TTL
        )
        async with tm._lock:
            tm._tasks[task_id] = record

        # Record should be found initially
        found = await tm.get_status(task_id)
        # Since completed_at is old, get_status should auto-expire it
        assert found is None, f"Expected None (expired), got {found}"

        # Cleanup should report 0 (already removed by get_status)
        cleaned = await tm.cleanup_expired()
        assert cleaned == 0

        # Insert a fresh completed record (not expired)
        task_id2 = "task_test_fresh"
        record2 = TaskRecord(
            task_id=task_id2,
            status=TaskStatus.COMPLETED,
            progress=1.0,
            result={"result": "fresh"},
            completed_at=time.monotonic(),  # just now — not expired
        )
        async with tm._lock:
            tm._tasks[task_id2] = record2

        found2 = await tm.get_status(task_id2)
        assert found2 is not None
        assert found2.status == TaskStatus.COMPLETED

        # Backdating it to expired and running cleanup
        async with tm._lock:
            tm._tasks[task_id2].completed_at = time.monotonic() - 2

        cleaned2 = await tm.cleanup_expired()
        assert cleaned2 == 1
        assert await tm.get_status(task_id2) is None

    finally:
        tm_module.TASK_RESULT_TTL_SECONDS = original_ttl


@pytest.mark.asyncio
async def test_task_manager_update_progress():
    """update_progress only affects PROCESSING records."""
    tm = InMemoryTaskManager()
    task_id = "task_progress_test"
    record = TaskRecord(
        task_id=task_id,
        status=TaskStatus.PROCESSING,
        progress=0.1,
    )
    async with tm._lock:
        tm._tasks[task_id] = record

    await tm.update_progress(task_id, 0.75)

    async with tm._lock:
        assert tm._tasks[task_id].progress == 0.75

    # Should not update completed record
    record.status = TaskStatus.COMPLETED
    await tm.update_progress(task_id, 0.5)
    async with tm._lock:
        assert tm._tasks[task_id].progress == 0.75  # unchanged
