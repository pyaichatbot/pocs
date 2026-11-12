"""Watch the real request/response boundary in your runserver terminal."""
import logging
from time import perf_counter

from django.conf import settings

logger = logging.getLogger("django.server")


class RequestTraceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.TRACE_REQUESTS:
            return self.get_response(request)
        started = perf_counter()
        logger.info("→ %s %s", request.method, request.path)
        # Everything inside this call happens before the response comes back.
        response = self.get_response(request)
        match = request.resolver_match
        view = match.view_name if match else "early response / no route"
        elapsed = (perf_counter() - started) * 1000
        logger.info("← %s | view=%s | %.0f ms", response.status_code, view, elapsed)
        return response
