import uuid
from typing import Any, cast

import structlog
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agentic.agent_factory import create_agent_for_datasource
from app.agentic.tools.plotly_registry import finish_chart_capture, start_chart_capture
from app.models import DataSource

logger = structlog.get_logger(__name__)


def chat(
    data_source_id: int, message: str, thread_id: str | None, db: Session
) -> tuple[str, str, list[dict[str, Any]]]:
    """
    Send a message to the agent for a given data source.
    Returns response text, thread ID, and chart payloads captured during the run.
    """
    data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not data_source:
        logger.error("chat_datasource_not_found", data_source_id=data_source_id)
        raise HTTPException(status_code=404, detail="Data source not found")

    agent = create_agent_for_datasource(data_source)

    if not thread_id:
        thread_id = uuid.uuid4().hex

    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    chart_capture_token = start_chart_capture()
    try:
        logger.info(
            "agent_invoke_started",
            data_source_id=data_source_id,
            thread_id=thread_id,
            message_length=len(message),
        )
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=cast(Any, config),
        )
    except Exception as exc:
        logger.error(
            "agent_invoke_failed",
            data_source_id=data_source_id,
            thread_id=thread_id,
            error=str(exc),
        )
        raise
    finally:
        charts = finish_chart_capture(chart_capture_token)

    ai_message = result["messages"][-1]
    logger.info(
        "agent_invoke_completed",
        data_source_id=data_source_id,
        thread_id=thread_id,
        charts_count=len(charts),
    )
    return ai_message.content, thread_id, charts
