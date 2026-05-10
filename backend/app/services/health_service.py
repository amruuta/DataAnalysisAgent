from sqlalchemy import text

from app.agentic.agent_factory import get_checkpointer
from app.cache import get_redis_client
from app.database import engine


def check_database() -> bool:
    """Return whether Postgres responds to a basic query."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def check_cache() -> bool:
    """Return whether Redis responds to a ping."""
    return bool(get_redis_client().ping())


def check_checkpointer() -> bool:
    """Return whether the LangGraph Redis checkpointer can be initialized."""
    get_checkpointer()
    return True


def run_health_checks() -> dict[str, bool]:
    """Run database, cache, and checkpointer health checks."""
    checks: dict[str, bool] = {}
    for name, checker in {
        "database": check_database,
        "cache": check_cache,
        "checkpointer": check_checkpointer,
    }.items():
        try:
            checks[name] = checker()
        except Exception:
            checks[name] = False
    return checks
