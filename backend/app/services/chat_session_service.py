from datetime import datetime, timezone
from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ChatSession, DataSource, User
from app.schemas import (
    AiMessageModel,
    ChatSessionDetailResponse,
    ChatSessionSummaryResponse,
    HumanMessageModel,
    MessageContentModel,
    SaveChatSessionResponse,
)
from app.services.checkpoint_snapshot_service import CheckpointSnapshotService
from app.services.session_cache_service import SessionCacheService
from app.utils.ids import new_uuid7


class ChatSessionService:
    """Coordinate authorized chat sessions across Postgres and Redis."""

    def __init__(
        self,
        cache_service: SessionCacheService | None = None,
        checkpoint_service: CheckpointSnapshotService | None = None,
    ):
        """Create the service with cache and checkpoint collaborators."""
        self.cache = cache_service or SessionCacheService()
        self.checkpoints = checkpoint_service or CheckpointSnapshotService()

    def get_user_data_source(
        self, db: Session, user: User, data_source_id: int
    ) -> DataSource:
        """Return a data source only when it belongs to the current user."""
        data_source = (
            db.query(DataSource)
            .filter(DataSource.id == data_source_id, DataSource.user_id == user.id)
            .first()
        )
        if not data_source:
            raise HTTPException(status_code=404, detail="Data source not found")
        return cast(DataSource, data_source)

    def get_or_create_session(
        self,
        db: Session,
        user: User,
        data_source_id: int,
        thread_id: str | None,
        first_message: str,
    ) -> ChatSession:
        """Resolve an existing session or create a new one for the data source."""
        self.get_user_data_source(db, user, data_source_id)
        if thread_id:
            session = (
                db.query(ChatSession)
                .filter(
                    ChatSession.thread_id == thread_id,
                    ChatSession.user_id == user.id,
                    ChatSession.data_source_id == data_source_id,
                )
                .first()
            )
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            self.restore_session_cache_if_needed(session)
            return cast(ChatSession, session)

        title = first_message.strip()[:80] or "New chat"
        session = ChatSession(
            thread_id=new_uuid7(),
            user_id=user.id,
            data_source_id=data_source_id,
            title=title,
            chat_history=[],
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        self.cache.restore_history(str(user.id), str(session.thread_id), [], data_source_id)
        return session

    def restore_session_cache_if_needed(self, session: ChatSession) -> None:
        """Restore Redis history and checkpoint keys from Postgres when absent."""
        user_id = str(session.user_id)
        thread_id = str(session.thread_id)
        cached_history = self.cache.load_history(user_id, thread_id)
        if cached_history:
            return
        history = list(session.chat_history or [])
        self.cache.restore_history(
            user_id,
            thread_id,
            history,
            int(session.data_source_id),
        )
        self.checkpoints.import_thread(cast(str | None, session.checkpoint_json))

    def append_exchange(
        self,
        session: ChatSession,
        human_text: str,
        ai_text: str,
        charts: list[dict[str, Any]],
    ) -> tuple[HumanMessageModel, AiMessageModel]:
        """Append a human/AI exchange to Redis history for later persistence."""
        human_message = HumanMessageModel(
            content=MessageContentModel(message=human_text)
        )
        ai_message = AiMessageModel(
            content=MessageContentModel(message=ai_text, metadata={"charts": charts})
        )
        serialized_messages = [
            human_message.model_dump(mode="json"),
            ai_message.model_dump(mode="json"),
        ]
        self.cache.append_messages(
            str(session.user_id),
            str(session.thread_id),
            int(session.data_source_id),
            serialized_messages,
        )
        return human_message, ai_message

    def save_session(
        self,
        db: Session,
        user_id: str,
        thread_id: str,
    ) -> SaveChatSessionResponse:
        """Persist Redis chat history and checkpoint state into Postgres."""
        session = (
            db.query(ChatSession)
            .filter(ChatSession.thread_id == thread_id, ChatSession.user_id == user_id)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        history = self.cache.load_history(user_id, thread_id)
        if not history:
            history = list(session.chat_history or [])

        session.chat_history = history
        session.checkpoint_json = self.checkpoints.export_thread(thread_id)
        session.last_persisted_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)
        db.add(session)
        db.commit()
        db.refresh(session)
        self.cache.clear_dirty(user_id, thread_id)
        return SaveChatSessionResponse(
            thread_id=thread_id,
            saved=True,
            last_persisted_at=session.last_persisted_at,
        )

    def list_sessions(
        self, db: Session, user: User
    ) -> list[ChatSessionSummaryResponse]:
        """Return chat sessions owned by the current user."""
        sessions = (
            db.query(ChatSession)
            .join(DataSource, ChatSession.data_source_id == DataSource.id)
            .filter(ChatSession.user_id == user.id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
            .all()
        )
        return [
            ChatSessionSummaryResponse(
                thread_id=cast(str, session.thread_id),
                data_source_id=cast(int, session.data_source_id),
                data_source_name=cast(str, session.data_source.name),
                title=cast(str, session.title),
                created_at=session.created_at,
                updated_at=session.updated_at,
                last_persisted_at=session.last_persisted_at,
            )
            for session in sessions
        ]

    def get_session_detail(
        self, db: Session, user: User, thread_id: str
    ) -> ChatSessionDetailResponse:
        """Return one chat session and ensure its Redis state is warm."""
        session = (
            db.query(ChatSession)
            .filter(ChatSession.thread_id == thread_id, ChatSession.user_id == user.id)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        session = cast(ChatSession, session)
        self.restore_session_cache_if_needed(session)
        history = self.cache.load_history(str(user.id), thread_id) or list(
            session.chat_history or []
        )
        return ChatSessionDetailResponse(
            thread_id=cast(str, session.thread_id),
            data_source_id=cast(int, session.data_source_id),
            data_source_name=cast(str, session.data_source.name),
            title=cast(str, session.title),
            history=history,
        )
