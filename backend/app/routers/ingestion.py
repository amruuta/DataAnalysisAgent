import re
from datetime import datetime
from typing import Optional, cast

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import DataSource, User
from app.schemas import (
    DataSourceResponse,
    DatabaseConnectionRequest,
    DatabaseConnectionResponse,
    FileUploadResponse,
)
from app.services.ingestion_service import (
    get_data_source_by_id,
    ingest_database,
    ingest_file,
    list_data_sources,
)
from app.services.security_service import decrypt_secret

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a tabular file and register it as a data source."""
    data_source = await ingest_file(file, name, db, current_user)
    return FileUploadResponse(
        id=cast(int, data_source.id),
        name=cast(str, data_source.name),
        table_name=cast(str, data_source.table_name),
        file_path=cast(str, data_source.file_path),
        message="File ingested successfully",
    )


def _mask_password(url: str) -> str:
    """Mask the password segment of a database URL for API responses."""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)


def _to_data_source_response(data_source: DataSource) -> DataSourceResponse:
    """Convert a DataSource model into its public API response schema."""
    db_url = (
        _mask_password(decrypt_secret(cast(str, data_source.db_url)))
        if data_source.db_url is not None
        else None
    )
    return DataSourceResponse(
        id=cast(int, data_source.id),
        name=cast(str, data_source.name),
        source_type=cast(str, data_source.source_type),
        table_name=cast(str, data_source.table_name),
        file_path=cast(Optional[str], data_source.file_path),
        db_url=db_url,
        created_at=cast(datetime, data_source.created_at),
    )


@router.post("/database", response_model=DatabaseConnectionResponse)
def connect_database(
    config: DatabaseConnectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate and register an external database as a data source."""
    data_source = ingest_database(config, db, current_user)
    return DatabaseConnectionResponse(
        id=cast(int, data_source.id),
        name=cast(str, data_source.name),
        db_url=_mask_password(config.db_url or ""),
        table_name=cast(Optional[str], data_source.table_name),
        message="Database connection registered successfully",
    )


@router.get("/datasources", response_model=list[DataSourceResponse])
def get_data_sources(
    source_type: Optional[str] = Query(
        default=None,
        description="Optional filter by source type: file or database",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List registered data sources, optionally filtered by source type."""
    data_sources = list_data_sources(db=db, user=current_user, source_type=source_type)
    return [_to_data_source_response(data_source) for data_source in data_sources]


@router.get("/datasources/{data_source_id}", response_model=DataSourceResponse)
def get_data_source_details(
    data_source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return details for a single registered data source."""
    data_source = get_data_source_by_id(
        data_source_id=data_source_id, db=db, user=current_user
    )
    return _to_data_source_response(data_source)
