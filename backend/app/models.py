from sqlalchemy import Column, Integer, String, DateTime, func

from app.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # "file" or "database"
    file_path = Column(String, nullable=True)
    table_name = Column(String, nullable=False)
    db_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
