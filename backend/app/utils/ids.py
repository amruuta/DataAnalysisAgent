import secrets
import time
import uuid


def new_uuid7() -> str:
    """Return a UUIDv7 string without depending on Python 3.14's uuid module."""
    try:
        from uuid6 import uuid7

        return str(uuid7())
    except ImportError:
        timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)
        rand_a = secrets.randbits(12)
        rand_b = secrets.randbits(62)
        value = (
            (timestamp_ms << 80)
            | (0x7 << 76)
            | (rand_a << 64)
            | (0b10 << 62)
            | rand_b
        )
        return str(uuid.UUID(int=value))
