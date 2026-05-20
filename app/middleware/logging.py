"""Request logging middleware with correlation IDs."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import structlog

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()

        with structlog.contextvars.bound_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        ):
            logger.info("request_started")
            try:
                response = await call_next(request)
                duration_ms = (time.perf_counter() - start_time) * 1000
                response.headers["X-Correlation-ID"] = correlation_id
                response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
                logger.info(
                    "request_completed",
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2),
                )
                return response
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    "request_failed",
                    error=str(exc),
                    duration_ms=round(duration_ms, 2),
                    exc_info=True,
                )
                raise
