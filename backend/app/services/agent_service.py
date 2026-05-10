from typing import Any, cast

import structlog
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agentic.agent_factory import create_agent_for_datasource
from app.agentic.tools.plotly_registry import finish_chart_capture, start_chart_capture
from app.models import User
from app.schemas import AiMessageModel, HumanMessageModel
from app.services.chat_session_service import ChatSessionService

logger = structlog.get_logger(__name__)
chat_sessions = ChatSessionService()


def chat(
    data_source_id: int,
    message: str,
    thread_id: str | None,
    db: Session,
    user: User,
) -> tuple[str, str, list[dict[str, Any]], HumanMessageModel, AiMessageModel]:
    """
    Send a message to the agent for a given data source.
    Returns response text, thread ID, and chart payloads captured during the run.
    """
    session = chat_sessions.get_or_create_session(
        db=db,
        user=user,
        data_source_id=data_source_id,
        thread_id=thread_id,
        first_message=message,
    )
    data_source = session.data_source
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    agent = create_agent_for_datasource(data_source)

    resolved_thread_id = str(session.thread_id)
    config: dict[str, Any] = {"configurable": {"thread_id": resolved_thread_id}}

    chart_capture_token = start_chart_capture()
    try:
        logger.info(
            "agent_invoke_started",
            data_source_id=data_source_id,
            thread_id=resolved_thread_id,
            user_id=user.id,
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
            thread_id=resolved_thread_id,
            user_id=user.id,
            error=str(exc),
        )
        raise
    finally:
        charts = finish_chart_capture(chart_capture_token)

    ai_message = result["messages"][-1]
    response_text = str(ai_message.content)
    human_history_message, ai_history_message = chat_sessions.append_exchange(
        session=session,
        human_text=message,
        ai_text=response_text,
        charts=charts,
    )
    logger.info(
        "agent_invoke_completed",
        data_source_id=data_source_id,
        thread_id=resolved_thread_id,
        user_id=user.id,
        charts_count=len(charts),
    )
    return (
        response_text,
        resolved_thread_id,
        charts,
        human_history_message,
        ai_history_message,
    )
