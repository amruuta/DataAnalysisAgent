from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.ids import new_uuid7


def utc_now() -> datetime:
    """Return the current UTC timestamp for API models."""
    return datetime.now(timezone.utc)


class UserRegisterRequest(BaseModel):
    """Payload used to create a new user account."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize and validate the email address used for login."""
        email = value.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Provide a valid email address")
        return email

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Require a minimally strong password for local authentication."""
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value


class UserLoginRequest(BaseModel):
    """Payload used to authenticate an existing user."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize the email address before authentication."""
        return value.strip().lower()


class UserResponse(BaseModel):
    """Public user details returned to the frontend."""

    id: str
    email: str
    created_at: datetime | None = None


class AuthResponse(BaseModel):
    """Authentication response containing the current user."""

    user: UserResponse


class FileUploadResponse(BaseModel):
    """Response returned after a file is ingested."""

    id: int
    name: str
    table_name: str
    file_path: str
    message: str


class DatabaseConnectionRequest(BaseModel):
    """Payload used to register an external database connection."""

    name: str
    db_host: Optional[str] = None
    db_port: int = 5432
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_url: Optional[str] = None
    table_name: Optional[str] = None

    @model_validator(mode="after")
    def validate_connection(self):
        """Build or validate the database URL from connection fields."""
        if self.db_url:
            return self
        if all([self.db_host, self.db_name, self.db_user, self.db_password]):
            self.db_url = (
                f"postgresql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
            return self
        raise ValueError(
            "Provide either 'db_url' or all of 'db_host', 'db_name', 'db_user', 'db_password'"
        )


class DatabaseConnectionResponse(BaseModel):
    """Response returned after an external database is registered."""

    id: int
    name: str
    db_url: str
    table_name: Optional[str]
    message: str


class DataSourceResponse(BaseModel):
    """Public data source details scoped to the current user."""

    id: int
    name: str
    source_type: str
    table_name: str
    file_path: Optional[str] = None
    db_url: Optional[str] = None
    created_at: datetime


class ChatRequest(BaseModel):
    """Payload used to send a message to an agent thread."""

    data_source_id: int
    message: str
    thread_id: Optional[str] = None


class PlotlyChartResponse(BaseModel):
    """Plotly chart payload returned alongside an AI chat message."""

    chart_id: str
    title: str
    chart_type: str
    figure: dict[str, Any]


class MessageContentModel(BaseModel):
    """Structured chat message content persisted in history."""

    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class HumanMessageModel(BaseModel):
    """Persisted human chat message with server-generated metadata."""

    id: str = Field(default_factory=new_uuid7)
    timestamp: datetime = Field(default_factory=utc_now)
    role: Literal["human"] = "human"
    content: MessageContentModel


class AiMessageModel(BaseModel):
    """Persisted AI chat message with server-generated metadata."""

    id: str = Field(default_factory=new_uuid7)
    timestamp: datetime = Field(default_factory=utc_now)
    role: Literal["ai"] = "ai"
    content: MessageContentModel


ChatHistoryMessage = HumanMessageModel | AiMessageModel


class ChatResponse(BaseModel):
    """Response returned after invoking the data analysis agent."""

    response: str
    thread_id: str
    charts: list[PlotlyChartResponse] = Field(default_factory=list)
    human_message: HumanMessageModel | None = None
    ai_message: AiMessageModel | None = None


class ChatSessionSummaryResponse(BaseModel):
    """Compact chat session details for the history list."""

    thread_id: str
    data_source_id: int
    data_source_name: str
    title: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_persisted_at: datetime | None = None


class ChatSessionDetailResponse(BaseModel):
    """Full chat session payload including persisted message history."""

    thread_id: str
    data_source_id: int
    data_source_name: str
    title: str
    history: list[ChatHistoryMessage] = Field(default_factory=list)


class SaveChatSessionResponse(BaseModel):
    """Response returned after forcing a chat session persistence flush."""

    thread_id: str
    saved: bool
    last_persisted_at: datetime | None = None
