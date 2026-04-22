"""Request logging middleware."""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request


logger = logging.getLogger(__name__)


def add_logging_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
