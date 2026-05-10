import os
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.logging_config import configure_logging
from app.routers import ingestion, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create local storage directories when the FastAPI app starts."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    yield


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


app.include_router(ingestion.router)
app.include_router(chat.router)
app.mount(
    "/exports",
    StaticFiles(directory=settings.EXPORT_DIR, check_dir=False),
    name="exports",
)


@app.get("/health")
def health_check():
    """Return a simple health signal for uptime checks."""
    return {"status": "ok"}
