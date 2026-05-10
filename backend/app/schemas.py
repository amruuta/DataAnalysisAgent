from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class FileUploadResponse(BaseModel):
    id: int
    name: str
    table_name: str
    file_path: str
    message: str


class DatabaseConnectionRequest(BaseModel):
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
    id: int
    name: str
    db_url: str
    table_name: Optional[str]
    message: str


class DataSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    table_name: str
    file_path: Optional[str] = None
    db_url: Optional[str] = None
    created_at: datetime


class ChatRequest(BaseModel):
    data_source_id: int
    message: str
    thread_id: Optional[str] = None


class PlotlyChartResponse(BaseModel):
    chart_id: str
    title: str
    chart_type: str
    figure: dict[str, Any]


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    charts: list[PlotlyChartResponse] = Field(default_factory=list)
