from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    DATABASE_URL: str = (
        "postgresql://postgres:postgres@localhost:5432/data_analysis_agent"
    )
    AI_API_KEY: str = ""
    AI_MODEL: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    UPLOAD_DIR: str = "uploads"
    EXPORT_DIR: str = "exports"
    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SESSION_TTL_SECONDS: int = 3600
    SCHEDULER_INTERVAL_SECONDS: int = 300
    AUTH_COOKIE_NAME: str = "daa_access_token"
    COOKIE_SECURE: bool = False

    @property
    def cors_origins(self) -> list[str]:
        """Return configured CORS origins as a clean list of URLs."""
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    model_config = {"env_file": ".env"}


settings = Settings()
