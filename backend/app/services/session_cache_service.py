import json
from typing import Any

from redis import Redis

from app.cache import get_redis_client
from app.config import settings


class SessionCacheService:
    """Manage Redis chat history, session metadata, and dirty-session tracking."""

    dirty_key = "chat:sessions:dirty"

    def __init__(self, redis_client: Redis | None = None):
        """Create the service with an explicit or shared Redis client."""
        self.redis = redis_client or get_redis_client()

    def history_key(self, user_id: str, thread_id: str) -> str:
        """Return the Redis key for a user's chat history in one thread."""
        return f"chat:session:{user_id}:{thread_id}:history"

    def meta_key(self, user_id: str, thread_id: str) -> str:
        """Return the Redis key for a user's chat session metadata."""
        return f"chat:session:{user_id}:{thread_id}:meta"

    def load_history(self, user_id: str, thread_id: str) -> list[dict[str, Any]]:
        """Load chat history from Redis, returning an empty list when absent."""
        raw_history = self.redis.get(self.history_key(user_id, thread_id))
        if not raw_history:
            return []
        loaded = json.loads(raw_history)
        return loaded if isinstance(loaded, list) else []

    def restore_history(
        self,
        user_id: str,
        thread_id: str,
        history: list[dict[str, Any]],
        data_source_id: int,
    ) -> None:
        """Restore a session's history and metadata into Redis with a fresh TTL."""
        self.redis.setex(
            self.history_key(user_id, thread_id),
            settings.SESSION_TTL_SECONDS,
            json.dumps(history),
        )
        self.redis.setex(
            self.meta_key(user_id, thread_id),
            settings.SESSION_TTL_SECONDS,
            json.dumps(
                {
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "data_source_id": data_source_id,
                }
            ),
        )

    def append_messages(
        self,
        user_id: str,
        thread_id: str,
        data_source_id: int,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Append messages to cached history and mark the session dirty."""
        history = self.load_history(user_id, thread_id)
        history.extend(messages)
        self.restore_history(user_id, thread_id, history, data_source_id)
        self.mark_dirty(user_id, thread_id)
        return history

    def mark_dirty(self, user_id: str, thread_id: str) -> None:
        """Mark a session as needing persistence to Postgres."""
        self.redis.sadd(self.dirty_key, f"{user_id}|{thread_id}")

    def clear_dirty(self, user_id: str, thread_id: str) -> None:
        """Clear a session from the dirty-session set."""
        self.redis.srem(self.dirty_key, f"{user_id}|{thread_id}")

    def dirty_sessions(self) -> list[tuple[str, str]]:
        """Return all dirty user/thread pairs currently tracked in Redis."""
        raw_items = self.redis.smembers(self.dirty_key)
        sessions: list[tuple[str, str]] = []
        for item in raw_items:
            if "|" not in item:
                continue
            user_id, thread_id = item.split("|", 1)
            sessions.append((user_id, thread_id))
        return sessions
