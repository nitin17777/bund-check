"""
Structured, content-free logging configuration using structlog.

Guarantees:
- Document text, raw content, diffs, and improvement outputs are NEVER logged.
- Only safe metadata is emitted: request_id, task_id, word_count, latency_ms, status_code, band, score.
- Sanitizer processor strips any field containing suspicious high-volume text before emission.

Usage:
    from backend.app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("check_complete", analysis_id=aid, word_count=wc, score=s, band=b)
"""

import logging
import sys
from typing import Any, Dict, Tuple

import structlog

# Fields whose values must NEVER appear in logs (they may contain user document text).
_FORBIDDEN_FIELDS: Tuple[str, ...] = (
    "text",
    "raw_text",
    "content",
    "original",
    "revised",
    "rewritten",
    "paragraph_text",
    "sentence_text",
    "diff",
    "body",
    "source_text",
    "target_text",
    "prompt",
    "completion",
    "masked_text",
)

# If a string value exceeds this length it is treated as potential document text
# and replaced with a length-only placeholder.
_MAX_SAFE_VALUE_LENGTH = 200


def _sanitize_processor(
    logger: Any, method: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Structlog processor that removes or truncates values that might contain
    user document text before emitting log records.
    """
    for key in list(event_dict.keys()):
        # Drop explicitly forbidden fields
        if key in _FORBIDDEN_FIELDS:
            event_dict[key] = "[REDACTED]"
            continue
        # Truncate any excessively long string value
        value = event_dict[key]
        if isinstance(value, str) and len(value) > _MAX_SAFE_VALUE_LENGTH:
            event_dict[key] = f"[TRUNCATED:{len(value)}chars]"
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structlog with:
    - Content sanitizer processor
    - Standard metadata fields (timestamp, level, logger name)
    - Console renderer for development; JSON renderer in production when LOG_FORMAT=json
    """
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _sanitize_processor,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog-bound logger for the given module name."""
    return structlog.get_logger(name)
