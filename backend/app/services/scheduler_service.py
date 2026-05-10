import asyncio
import structlog
from typing import Any

from fastapi import HTTPException

from app.config import settings
from app.database import SessionLocal
from app.services.chat_session_service import ChatSessionService
from app.services.session_cache_service import SessionCacheService

logger = structlog.get_logger(__name__)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError:
    AsyncIOScheduler = None

_scheduler: Any | None = None
_scheduler_task: asyncio.Task | None = None


def save_dirty_chat_sessions() -> None:
    """Persist all dirty Redis chat sessions to Postgres."""
    cache = SessionCacheService()
    chat_sessions = ChatSessionService(cache_service=cache)
    for user_id, thread_id in cache.dirty_sessions():
        db = SessionLocal()
        try:
            chat_sessions.save_session(db, user_id, thread_id)
            logger.info("dirty_chat_session_saved", user_id=user_id, thread_id=thread_id)
        except HTTPException as exc:
            logger.warning(
                "dirty_chat_session_missing",
                user_id=user_id,
                thread_id=thread_id,
                status_code=exc.status_code,
            )
            cache.clear_dirty(user_id, thread_id)
        except Exception as exc:
            logger.error(
                "dirty_chat_session_save_failed",
                user_id=user_id,
                thread_id=thread_id,
                error=str(exc),
            )
        finally:
            db.close()


async def _autosave_loop() -> None:
    """Run the autosave job on an asyncio interval when APScheduler is absent."""
    while True:
        await asyncio.sleep(settings.SCHEDULER_INTERVAL_SECONDS)
        save_dirty_chat_sessions()


def start_scheduler() -> Any:
    """Start the APScheduler instance used for chat autosave."""
    global _scheduler
    global _scheduler_task
    if AsyncIOScheduler is None:
        if _scheduler_task and not _scheduler_task.done():
            return _scheduler_task
        _scheduler_task = asyncio.create_task(_autosave_loop())
        logger.warning("scheduler_fallback_started")
        return _scheduler_task

    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        save_dirty_chat_sessions,
        "interval",
        seconds=settings.SCHEDULER_INTERVAL_SECONDS,
        id="save_dirty_chat_sessions",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "scheduler_started",
        interval_seconds=settings.SCHEDULER_INTERVAL_SECONDS,
    )
    return _scheduler


def stop_scheduler() -> None:
    """Stop the APScheduler instance if it is running."""
    global _scheduler
    global _scheduler_task
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
    _scheduler = None
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("scheduler_fallback_stopped")
    _scheduler_task = None
