"""OpenTelemetry-compatible logging configuration.

This module sets up structured logging using OpenTelemetry SDK
for observability. NO exporters are configured - logging only.
"""

import logging
import sys
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace import Tracer


class NoOpSpanExporter:
    """A no-op span exporter that discards all spans.
    
    This ensures we use OpenTelemetry SDK for structured logging
    but do not export any telemetry data.
    """
    
    def export(self, spans):
        """Discard spans - no export."""
        pass
    
    def shutdown(self):
        """No-op shutdown."""
        pass


def setup_logging(
    level: str = "INFO",
    service_name: str = "deepteam_demo",
    enable_console: bool = False,
) -> tuple[logging.Logger, Tracer]:
    """Setup OpenTelemetry-compatible logging infrastructure.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name of the service for logging context
        enable_console: If True, enable console span exporter for debugging
        
    Returns:
        Tuple of (logger, tracer) for use in application code
    """
    # Configure Python logging
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    
    # Suppress noisy OpenTelemetry exporter logs
    logging.getLogger("opentelemetry.exporter").setLevel(logging.CRITICAL)
    
    # Setup OpenTelemetry TracerProvider
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        trace.set_tracer_provider(TracerProvider())
    
    tracer_provider = trace.get_tracer_provider()
    
    # Add span processor with no-op exporter (no telemetry export)
    if enable_console:
        # Only for debugging - console output
        console_exporter = ConsoleSpanExporter()
        span_processor = BatchSpanProcessor(console_exporter)
    else:
        # No-op exporter - no telemetry export
        noop_exporter = NoOpSpanExporter()
        span_processor = BatchSpanProcessor(noop_exporter)
    
    tracer_provider.add_span_processor(span_processor)
    
    # Create tracer for the service
    tracer = trace.get_tracer(service_name)
    
    # Get logger
    logger = logging.getLogger(service_name)
    
    logger.info(
        f"Logging initialized: level={level}, service={service_name}, "
        f"console_export={enable_console}"
    )
    
    return logger, tracer

