from contextvars import ContextVar, Token
from typing import Any

_chart_capture_context: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "chart_capture_context", default=None
)


def start_chart_capture() -> Token:
    """Start collecting chart payloads for the current agent invocation."""
    return _chart_capture_context.set([])


def register_chart(chart_payload: dict[str, Any]) -> None:
    """Register a chart payload if chart capture is active in this context."""
    charts = _chart_capture_context.get()
    if charts is not None:
        charts.append(chart_payload)


def finish_chart_capture(token: Token) -> list[dict[str, Any]]:
    """Stop chart capture and return charts collected for this invocation."""
    charts = _chart_capture_context.get() or []
    _chart_capture_context.reset(token)
    return charts
