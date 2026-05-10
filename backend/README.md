Get started from scratch:
alembic revision --autogenerate -m "create data_sources table"
alembic upgrade head
uvicorn app.main:app --reload