import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionDetailResponse,
    ChatSessionSummaryResponse,
    PlotlyChartResponse,
    SaveChatSessionResponse,
)
from app.services import agent_service
from app.services.chat_session_service import ChatSessionService

router = APIRouter(tags=["chat"])
logger = structlog.get_logger(__name__)
chat_sessions = ChatSessionService()


@router.get("/chat/sessions", response_model=list[ChatSessionSummaryResponse])
def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List chat sessions owned by the authenticated user."""
    return chat_sessions.list_sessions(db, current_user)


@router.get("/chat/sessions/{thread_id}", response_model=ChatSessionDetailResponse)
def get_chat_session(
    thread_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return one chat session and restore Redis state when needed."""
    return chat_sessions.get_session_detail(db, current_user, thread_id)


@router.post("/chat/sessions/{thread_id}/save", response_model=SaveChatSessionResponse)
def save_chat_session(
    thread_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Force persistence of a cached chat session into Postgres."""
    return chat_sessions.save_session(db, str(current_user.id), thread_id)


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Handle a chat request and return the agent response plus chart payloads."""
    logger.info(
        "chat_request_received",
        data_source_id=request.data_source_id,
        user_id=current_user.id,
        has_thread_id=bool(request.thread_id),
        message_length=len(request.message),
    )

    try:
        response_text, thread_id, charts, human_message, ai_message = agent_service.chat(
            data_source_id=request.data_source_id,
            message=request.message,
            thread_id=request.thread_id,
            db=db,
            user=current_user,
        )
    except Exception as exc:
        logger.error(
            "chat_request_failed",
            data_source_id=request.data_source_id,
            user_id=current_user.id,
            has_thread_id=bool(request.thread_id),
            error=str(exc),
        )
        raise

    chart_items = [PlotlyChartResponse.model_validate(chart) for chart in charts]
    logger.info(
        "chat_response_generated",
        thread_id=thread_id,
        user_id=current_user.id,
        response_length=len(response_text),
        charts_count=len(chart_items),
    )

    return ChatResponse(
        response=response_text,
        thread_id=thread_id,
        charts=chart_items,
        human_message=human_message,
        ai_message=ai_message,
    )
