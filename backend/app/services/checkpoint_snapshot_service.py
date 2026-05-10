import json
from typing import Any

from redis import Redis

from app.cache import get_redis_client
from app.config import settings


class CheckpointSnapshotService:
    """Export and restore LangGraph Redis checkpointer keys for a thread."""

    def __init__(self, redis_client: Redis | None = None):
        """Create the service with an explicit or shared Redis client."""
        self.redis = redis_client or get_redis_client()

    def _thread_patterns(self, thread_id: str) -> list[str]:
        """Return Redis key patterns containing checkpointer state for a thread."""
        return [
            f"checkpoint:{thread_id}:*",
            f"checkpoint_write:{thread_id}:*",
            f"checkpoint_latest:{thread_id}:*",
        ]

    def _type_name(self, key: str) -> str:
        """Return the Redis type name for a key as a string."""
        key_type = self.redis.type(key)
        return key_type.decode("utf-8") if isinstance(key_type, bytes) else str(key_type)

    def _read_key(self, key: str) -> dict[str, Any] | None:
        """Read a supported Redis key into a JSON-serializable snapshot entry."""
        key_type = self._type_name(key)
        ttl = self.redis.ttl(key)
        if key_type in {"ReJSON-RL", "JSON"}:
            value = self.redis.json().get(key)
        elif key_type == "string":
            value = self.redis.get(key)
        else:
            return None
        return {"key": key, "type": key_type, "ttl": ttl, "value": value}

    def export_thread(self, thread_id: str) -> str:
        """Serialize all checkpointer Redis keys for a thread as a JSON string."""
        entries: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        for pattern in self._thread_patterns(thread_id):
            for key in self.redis.scan_iter(match=pattern):
                key_text = key.decode("utf-8") if isinstance(key, bytes) else str(key)
                if key_text in seen_keys:
                    continue
                seen_keys.add(key_text)
                entry = self._read_key(key_text)
                if entry is not None:
                    entries.append(entry)
        return json.dumps({"thread_id": thread_id, "entries": entries})

    def clear_thread(self, thread_id: str) -> None:
        """Delete supported checkpointer Redis keys for a thread."""
        keys: list[str] = []
        for pattern in self._thread_patterns(thread_id):
            keys.extend(
                key.decode("utf-8") if isinstance(key, bytes) else str(key)
                for key in self.redis.scan_iter(match=pattern)
            )
        if keys:
            self.redis.delete(*keys)

    def import_thread(self, checkpoint_json: str | None) -> None:
        """Restore checkpointer Redis keys from a JSON snapshot string."""
        if not checkpoint_json:
            return

        payload = json.loads(checkpoint_json)
        thread_id = str(payload.get("thread_id") or "")
        if thread_id:
            self.clear_thread(thread_id)

        for entry in payload.get("entries", []):
            key = str(entry["key"])
            key_type = str(entry["type"])
            value = entry.get("value")
            if key_type in {"ReJSON-RL", "JSON"}:
                self.redis.json().set(key, "$", value)
            elif key_type == "string":
                self.redis.set(key, value)
            else:
                continue

            ttl = int(entry.get("ttl") or settings.SESSION_TTL_SECONDS)
            if ttl > 0:
                self.redis.expire(key, min(ttl, settings.SESSION_TTL_SECONDS))
