import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, PlotlyChartResponse
from app.services import agent_service

router = APIRouter(tags=["chat"])
logger = structlog.get_logger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """Handle a chat request and return the agent response plus chart payloads."""
    logger.info(
        "chat_request_received",
        data_source_id=request.data_source_id,
        has_thread_id=bool(request.thread_id),
        message_length=len(request.message),
    )

    try:
        response_text, thread_id, charts = agent_service.chat(
            data_source_id=request.data_source_id,
            message=request.message,
            thread_id=request.thread_id,
            db=db,
        )
    except Exception as exc:
        logger.error(
            "chat_request_failed",
            data_source_id=request.data_source_id,
            has_thread_id=bool(request.thread_id),
            error=str(exc),
        )
        raise

    chart_items = [PlotlyChartResponse.model_validate(chart) for chart in charts]
    logger.info(
        "chat_response_generated",
        thread_id=thread_id,
        response_length=len(response_text),
        charts_count=len(chart_items),
    )

    return ChatResponse(response=response_text, thread_id=thread_id, charts=chart_items)
