import os
import re
import uuid

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

from app.config import settings
from app.database import engine
from app.models import DataSource
from app.schemas import DatabaseConnectionRequest


def _sanitize_table_name(name: str) -> str:
    """Convert a file name into a safe PostgreSQL table name."""
    name = os.path.splitext(name)[0]
    name = re.sub(r"[^a-zA-Z0-9]", "_", name).lower().strip("_")
    name = re.sub(r"_+", "_", name)
    return f"ds_{name}"


def _read_csv_with_fallback(file_path: str) -> pd.DataFrame:
    """Read CSV files using a small set of common encodings."""
    encodings = ("utf-8", "utf-8-sig", "cp1252", "latin-1")
    last_error: UnicodeDecodeError | None = None

    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error

    raise HTTPException(
        status_code=400,
        detail=(
            "Could not read the CSV file. Supported encodings attempted: "
            f"{', '.join(encodings)}. Last error: {last_error}"
        ),
    )


async def ingest_file(file: UploadFile, name: str, db: Session) -> DataSource:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    if not file.filename:
        raise HTTPException(
            status_code=400, detail="Uploaded file must include a filename"
        )

    filename = file.filename

    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(
            status_code=400, detail="Only CSV and Excel files are supported"
        )

    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    if ext == ".csv":
        df = _read_csv_with_fallback(file_path)
    else:
        df = pd.read_excel(file_path)

    table_name = _sanitize_table_name(filename)
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    data_source = DataSource(
        name=name,
        source_type="file",
        file_path=file_path,
        table_name=table_name,
    )
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


def ingest_database(config: DatabaseConnectionRequest, db: Session) -> DataSource:
    if not config.db_url:
        raise HTTPException(status_code=400, detail="Database URL is required")

    db_url = config.db_url
    test_engine = None

    try:
        test_engine = create_engine(db_url)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Could not connect to database: {e}"
        )
    finally:
        if test_engine is not None:
            test_engine.dispose()

    table_name = config.table_name or "all_tables"

    data_source = DataSource(
        name=config.name,
        source_type="database",
        db_url=db_url,
        table_name=table_name,
    )
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


def get_data_source_by_id(data_source_id: int, db: Session) -> DataSource:
    data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_source


def list_data_sources(db: Session, source_type: str | None = None) -> list[DataSource]:
    query = db.query(DataSource)

    if source_type is not None:
        normalized_source_type = source_type.lower()
        if normalized_source_type not in {"file", "database"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid source_type. Use 'file' or 'database'.",
            )
        query = query.filter(DataSource.source_type == normalized_source_type)

    return query.order_by(DataSource.created_at.desc()).all()
