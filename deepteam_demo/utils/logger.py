"""Logger wrapper with OpenTelemetry context support."""

import logging
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.trace import Span, Tracer


class Logger:
    """Logger wrapper that integrates with OpenTelemetry spans.
    
    This provides structured logging with span context for observability
    without exporting telemetry data.
    """
    
    def __init__(self, name: str, tracer: Optional[Tracer] = None):
        """Initialize logger.
        
        Args:
            name: Logger name
            tracer: OpenTelemetry tracer (optional)
        """
        self._logger = logging.getLogger(name)
        self._tracer = tracer or trace.get_tracer(name)
        self._name = name
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional span attributes."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional span attributes."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional span attributes."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional span attributes."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional span attributes."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        **kwargs
    ):
        """Log message with OpenTelemetry span context.
        
        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional context as key-value pairs
        """
        # Get current span if available
        try:
            span = trace.get_current_span()
            # Add attributes to current span if it's recording
            if span and hasattr(span, 'is_recording') and span.is_recording() and kwargs:
                for key, value in kwargs.items():
                    # Convert value to string for span attributes
                    span.set_attribute(f"log.{key}", str(value))
        except Exception:
            # If span operations fail, just continue with logging
            pass
        
        # Build log message with context
        if kwargs:
            context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} | {context_str}"
        else:
            full_message = message
        
        # Log using standard Python logging
        self._logger.log(level, full_message)
    
    def start_span(self, name: str, **attributes):
        """Start a new span for operation tracking.
        
        Args:
            name: Span name
            **attributes: Span attributes
            
        Returns:
            Context manager for the span
        """
        span = self._tracer.start_as_current_span(name)
        try:
            if span and hasattr(span, 'is_recording') and span.is_recording():
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
        except Exception:
            pass
        return span
    
    @property
    def logger(self) -> logging.Logger:
        """Get underlying Python logger."""
        return self._logger


def get_logger(name: str, tracer: Optional[Tracer] = None) -> Logger:
    """Get or create a logger instance.
    
    Args:
        name: Logger name
        tracer: OpenTelemetry tracer (optional)
        
    Returns:
        Logger instance
    """
    return Logger(name, tracer)

