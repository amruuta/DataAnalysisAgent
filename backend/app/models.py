from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """Application user that owns data sources and chat sessions."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    data_sources = relationship(
        "DataSource", back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )


class DataSource(Base):
    """Registered file or database source available to one user."""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # "file" or "database"
    file_path = Column(String, nullable=True)
    table_name = Column(String, nullable=False)
    db_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="data_sources")
    chat_sessions = relationship(
        "ChatSession", back_populates="data_source", cascade="all, delete-orphan"
    )


class ChatSession(Base):
    """Durable chat thread with serialized history and checkpoint snapshots."""

    __tablename__ = "chat_sessions"

    thread_id = Column(String, primary_key=True)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data_source_id = Column(
        Integer,
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String, nullable=False)
    chat_history = Column(JSONB, nullable=False, default=list)
    checkpoint_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_persisted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="chat_sessions")
    data_source = relationship("DataSource", back_populates="chat_sessions")
