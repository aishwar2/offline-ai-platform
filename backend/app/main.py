"""FastAPI application entrypoint with security, observability, and API routers."""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1 import auth, chat, conversations, health, rag, users
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_ctx
from app.core.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize structured logging and database tables on startup."""
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    logger.info("Offline AI Platform backend started (default_model=%s)", settings.default_model)
    yield


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Offline ChatGPT-style AI platform powered by Ollama (TinyLlama / Qwen2.5 0.5B), "
            "PostgreSQL, JWT authentication, optional ChromaDB RAG, and Prometheus metrics."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(req_id)
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        path = request.url.path
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method, path=path, status=str(response.status_code)
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, path=path).observe(duration)

        response.headers["X-Request-ID"] = req_id
        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            path,
            response.status_code,
            duration * 1000.0,
        )
        request_id_ctx.reset(token)
        return response

    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(users.router, prefix=settings.api_v1_prefix)
    app.include_router(conversations.router, prefix=settings.api_v1_prefix)
    app.include_router(chat.router, prefix=settings.api_v1_prefix)
    app.include_router(rag.router, prefix=settings.api_v1_prefix)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        """Expose Prometheus metrics in OpenMetrics/text format."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
