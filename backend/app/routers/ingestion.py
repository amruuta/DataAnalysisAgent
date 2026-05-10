import re
from datetime import datetime
from typing import Optional, cast

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DataSource
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

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    data_source = await ingest_file(file, name, db)
    return FileUploadResponse(
        id=cast(int, data_source.id),
        name=cast(str, data_source.name),
        table_name=cast(str, data_source.table_name),
        file_path=cast(str, data_source.file_path),
        message="File ingested successfully",
    )


def _mask_password(url: str) -> str:
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)


def _to_data_source_response(data_source: DataSource) -> DataSourceResponse:
    return DataSourceResponse(
        id=cast(int, data_source.id),
        name=cast(str, data_source.name),
        source_type=cast(str, data_source.source_type),
        table_name=cast(str, data_source.table_name),
        file_path=cast(Optional[str], data_source.file_path),
        db_url=(
            _mask_password(cast(str, data_source.db_url))
            if data_source.db_url is not None
            else None
        ),
        created_at=cast(datetime, data_source.created_at),
    )


@router.post("/database", response_model=DatabaseConnectionResponse)
def connect_database(
    config: DatabaseConnectionRequest,
    db: Session = Depends(get_db),
):
    data_source = ingest_database(config, db)
    return DatabaseConnectionResponse(
        id=cast(int, data_source.id),
        name=cast(str, data_source.name),
        db_url=_mask_password(cast(str, data_source.db_url)),
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
):
    data_sources = list_data_sources(db=db, source_type=source_type)
    return [_to_data_source_response(data_source) for data_source in data_sources]


@router.get("/datasources/{data_source_id}", response_model=DataSourceResponse)
def get_data_source_details(
    data_source_id: int,
    db: Session = Depends(get_db),
):
    data_source = get_data_source_by_id(data_source_id=data_source_id, db=db)
    return _to_data_source_response(data_source)
