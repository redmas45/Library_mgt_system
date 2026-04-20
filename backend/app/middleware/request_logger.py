"""
Request logger middleware — logs all incoming requests with timing.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.utils.logger import logger


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Logs every HTTP request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)

        # Log the request
        logger.info(
            f"{'→':>2} {request.method} {request.url.path} "
            f"[{response.status_code}] {duration_ms}ms"
        )

        # Add timing header
        response.headers["X-Process-Time"] = str(duration_ms)

        return response
