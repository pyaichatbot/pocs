"""
Observability Module - Phase 1: Comprehensive Logging

Provides OpenTelemetry-compatible logging decorators for method instrumentation.
"""

from .logging_decorator import log_execution, LoggingDecorator

__all__ = [
    "log_execution",
    "LoggingDecorator",
]

