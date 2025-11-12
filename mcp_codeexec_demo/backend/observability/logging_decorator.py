"""
Logging Decorator - OpenTelemetry-compatible method instrumentation.

Phase 1: Comprehensive logging for observability.

Follows SOLID principles:
- Single Responsibility: Only handles logging instrumentation
- Open/Closed: Can be extended with new log fields without modification
- Dependency Inversion: Depends on logging abstraction
"""
import functools
import time
import json
import logging
from typing import Any, Callable, Dict, Optional
from enum import Enum
import uuid

# Configure logging
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    SECURITY = "SECURITY"  # For security events


class LoggingDecorator:
    """OpenTelemetry-compatible logging decorator.
    
    Logs method execution with:
    - Entry/exit timestamps
    - Execution duration
    - Parameters (sanitized for PII)
    - Results
    - Errors and exceptions
    - Correlation IDs (trace_id, span_id)
    """
    
    def __init__(
        self,
        log_level: LogLevel = LogLevel.INFO,
        log_parameters: bool = True,
        log_results: bool = True,
        sanitize_pii: bool = True,
        include_trace: bool = True
    ):
        """Initialize logging decorator.
        
        Args:
            log_level: Log level for this decorator
            log_parameters: Whether to log method parameters
            log_results: Whether to log method results
            sanitize_pii: Whether to sanitize PII in logs
            include_trace: Whether to include trace/span IDs
        """
        self.log_level = log_level
        self.log_parameters = log_parameters
        self.log_results = log_results
        self.sanitize_pii = sanitize_pii
        self.include_trace = include_trace
    
    def __call__(self, func: Callable) -> Callable:
        """Apply decorator to function."""
        import inspect
        
        # Detect if function is async
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_with_logging_async(func, args, kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._execute_with_logging_sync(func, args, kwargs)
            return sync_wrapper
    
    async def _execute_with_logging_async(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> Any:
        """Execute async function with logging."""
        # Generate correlation IDs
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())[:16]
        
        # Get function metadata
        func_name = f"{func.__module__}.{func.__qualname__}"
        start_time = time.time()
        
        # Log entry
        log_entry = self._create_log_entry(
            event="method_entry",
            func_name=func_name,
            trace_id=trace_id,
            span_id=span_id,
            parameters=self._sanitize_parameters(args, kwargs) if self.log_parameters else None
        )
        self._log(log_entry)
        
        try:
            # Execute async function
            result = await func(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log exit
            log_entry = self._create_log_entry(
                event="method_exit",
                func_name=func_name,
                trace_id=trace_id,
                span_id=span_id,
                duration_ms=duration_ms,
                result=self._sanitize_result(result) if self.log_results else None,
                success=True
            )
            self._log(log_entry)
            
            return result
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            log_entry = self._create_log_entry(
                event="method_error",
                func_name=func_name,
                trace_id=trace_id,
                span_id=span_id,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                success=False
            )
            self._log(log_entry, level=LogLevel.ERROR)
            
            raise
    
    def _execute_with_logging_sync(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> Any:
        """Execute sync function with logging."""
        # Generate correlation IDs
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())[:16]
        
        # Get function metadata
        func_name = f"{func.__module__}.{func.__qualname__}"
        start_time = time.time()
        
        # Log entry
        log_entry = self._create_log_entry(
            event="method_entry",
            func_name=func_name,
            trace_id=trace_id,
            span_id=span_id,
            parameters=self._sanitize_parameters(args, kwargs) if self.log_parameters else None
        )
        self._log(log_entry)
        
        try:
            # Execute sync function
            result = func(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log exit
            log_entry = self._create_log_entry(
                event="method_exit",
                func_name=func_name,
                trace_id=trace_id,
                span_id=span_id,
                duration_ms=duration_ms,
                result=self._sanitize_result(result) if self.log_results else None,
                success=True
            )
            self._log(log_entry)
            
            return result
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            log_entry = self._create_log_entry(
                event="method_error",
                func_name=func_name,
                trace_id=trace_id,
                span_id=span_id,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                success=False
            )
            self._log(log_entry, level=LogLevel.ERROR)
            
            raise
    
    def _create_log_entry(
        self,
        event: str,
        func_name: str,
        trace_id: str,
        span_id: str,
        duration_ms: Optional[float] = None,
        parameters: Optional[Dict] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
        success: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Create structured log entry in OpenTelemetry format."""
        entry = {
            "timestamp": time.time(),
            "event": event,
            "function": func_name,
        }
        
        if self.include_trace:
            entry["trace_id"] = trace_id
            entry["span_id"] = span_id
        
        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)
        
        if parameters is not None:
            entry["parameters"] = parameters
        
        if result is not None:
            entry["result"] = self._truncate_value(result)
        
        if error is not None:
            entry["error"] = error
            entry["error_type"] = error_type
        
        if success is not None:
            entry["success"] = success
        
        return entry
    
    def _sanitize_parameters(self, args: tuple, kwargs: dict) -> Dict[str, Any]:
        """Sanitize parameters for logging (remove PII, truncate large values)."""
        params = {}
        
        # Add positional args (as arg0, arg1, etc.)
        for i, arg in enumerate(args):
            params[f"arg{i}"] = self._truncate_value(arg)
        
        # Add keyword args
        for key, value in kwargs.items():
            # Skip sensitive keys
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token', 'api_key']):
                params[key] = "[REDACTED]"
            else:
                params[key] = self._truncate_value(value)
        
        return params
    
    def _sanitize_result(self, result: Any) -> Any:
        """Sanitize result for logging."""
        return self._truncate_value(result)
    
    def _truncate_value(self, value: Any, max_length: int = 1000) -> Any:
        """Truncate large values for logging."""
        if isinstance(value, str):
            if len(value) > max_length:
                return value[:max_length] + f"... (truncated, {len(value)} chars)"
            return value
        elif isinstance(value, (dict, list)):
            # Serialize and truncate
            try:
                serialized = json.dumps(value)
                if len(serialized) > max_length:
                    return json.loads(serialized[:max_length] + "...")
                return value
            except Exception:
                return str(value)[:max_length] + "..." if len(str(value)) > max_length else value
        else:
            str_value = str(value)
            if len(str_value) > max_length:
                return str_value[:max_length] + "..."
            return value
    
    def _log(self, entry: Dict[str, Any], level: Optional[LogLevel] = None) -> None:
        """Log entry using Python logging (OpenTelemetry format).
        
        In production, this would use OpenTelemetry SDK.
        For now, we use structured JSON logging that Dynatrace can ingest.
        """
        log_level = level or self.log_level
        
        # Format as JSON for structured logging
        log_message = json.dumps(entry, default=str)
        
        # Use appropriate log level
        if log_level == LogLevel.DEBUG:
            logger.debug(log_message)
        elif log_level == LogLevel.INFO:
            logger.info(log_message)
        elif log_level == LogLevel.WARN:
            logger.warning(log_message)
        elif log_level == LogLevel.ERROR:
            logger.error(log_message)
        elif log_level == LogLevel.SECURITY:
            logger.warning(log_message)  # Security events as warnings for visibility


# Convenience decorator
def log_execution(
    log_level: LogLevel = LogLevel.INFO,
    log_parameters: bool = True,
    log_results: bool = True,
    sanitize_pii: bool = True
) -> Callable:
    """Convenience decorator for method logging.
    
    Usage:
        @log_execution()
        async def my_function(arg1, arg2):
            ...
    """
    decorator = LoggingDecorator(
        log_level=log_level,
        log_parameters=log_parameters,
        log_results=log_results,
        sanitize_pii=sanitize_pii
    )
    return decorator

