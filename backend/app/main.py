import os
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.logging_config import configure_logging
from app.routers import auth, chat, ingestion
from app.services.health_service import (
    check_cache,
    check_checkpointer,
    check_database,
    run_health_checks,
)
from app.services.scheduler_service import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create local storage directories when the FastAPI app starts."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    check_database()
    check_cache()
    check_checkpointer()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


configure_logging()
logger = structlog.get_logger(__name__)


app = FastAPI(title="Data Analysis Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log request lifecycle metadata around each HTTP request."""
    start_time = time.perf_counter()
    client_host = request.client.host if request.client else "unknown"

    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client=client_host,
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            client=client_host,
            duration_ms=round(duration_ms, 2),
            error=str(exc),
        )
        raise

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        client=client_host,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    return response


app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(ingestion.router)
app.mount(
    "/exports",
    StaticFiles(directory=settings.EXPORT_DIR, check_dir=False),
    name="exports",
)


@app.get("/health")
def health_check():
    """Return application, database, cache, and checkpointer health."""
    checks = run_health_checks()
    status = "ok" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
