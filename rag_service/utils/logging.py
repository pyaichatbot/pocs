"""
Logging utilities for the RAG service.

The service uses structured JSON logging for easy ingestion by
observability platforms.  Each log record is formatted as a JSON
object with at least a timestamp, log level, service name and message
fields.  Additional context can be provided via keyword arguments.

To use in your code, obtain a logger via ``get_logger(__name__)`` and
call ``logger.info(...)`` or ``logger.error(...)``.  If you want to
log structured data use the ``log_event`` convenience function.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict


_SERVICE_NAME = "markdown-rag"


def get_logger(name: str) -> logging.Logger:
    """Create or return a logger with a simple JSON formatter.

    The logger writes to standard output and is configured only once.  If
    called repeatedly for the same name the existing logger is returned.

    Args:
        name: Module or context name.
    Returns:
        A configured ``logging.Logger`` instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def log_event(
    logger: logging.Logger, event: str, **kwargs: Any
) -> None:
    """Log a structured event as a JSON object.

    Args:
        logger: A logger created via ``get_logger``.
        event: A short identifier for the event type (e.g. ``"index_start"``).
        kwargs: Additional context to include in the log entry.
    """
    payload: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": _SERVICE_NAME,
        "event": event,
        **kwargs,
    }
    logger.info(json.dumps(payload))
