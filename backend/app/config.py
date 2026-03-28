"""
CultivaX Application Configuration

Loads settings from environment variables with sensible defaults.
Uses Pydantic Settings for type-safe configuration.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "CultivaX"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database — local development default
    DATABASE_URL: str = "postgresql://cultivax_user:cultivax_pass@localhost:5432/cultivax_db"

    # Cloud SQL — used when deployed to Cloud Run
    CLOUD_SQL_CONNECTION_NAME: str = ""   # e.g. "project:region:instance"
    CLOUD_SQL_DB_NAME: str = "cultivax_db"
    CLOUD_SQL_DB_USER: str = "cultivax_user"
    CLOUD_SQL_DB_PASSWORD: str = ""
    CLOUD_SQL_UNIX_SOCKET: str = "/cloudsql"  # Cloud Run auto-mounts here

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting (per minute)
    RATE_LIMIT_FARMER: int = 60
    RATE_LIMIT_PROVIDER: int = 100
    RATE_LIMIT_ADMIN: int = 200
    RATE_LIMIT_DEFAULT: int = 30

    # Cloud Storage (Day 28)
    GCS_BUCKET_NAME: str = ""  # Set to enable GCS uploads, empty = local fallback
    GCS_SIGNED_URL_EXPIRY_MINUTES: int = 60
    MEDIA_UPLOAD_DIR: str = "uploads/media"  # Local fallback directory

    # Security
    PROD_DB_HOST_ALLOWLIST: str = ""  # Comma-separated prod DB hosts

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def effective_database_url(self) -> str:
        """
        Build the correct database URL based on environment.

        - If CLOUD_SQL_CONNECTION_NAME is set, construct a unix socket URL
          for Cloud Run (e.g. postgresql://user:pass@/db?host=/cloudsql/conn).
        - Otherwise, fall back to DATABASE_URL (for local dev / docker-compose).
        """
        if self.CLOUD_SQL_CONNECTION_NAME:
            socket_path = f"{self.CLOUD_SQL_UNIX_SOCKET}/{self.CLOUD_SQL_CONNECTION_NAME}"
            return (
                f"postgresql://{self.CLOUD_SQL_DB_USER}:{self.CLOUD_SQL_DB_PASSWORD}"
                f"@/{self.CLOUD_SQL_DB_NAME}?host={socket_path}"
            )
        return self.DATABASE_URL

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def prod_db_hosts(self) -> List[str]:
        if not self.PROD_DB_HOST_ALLOWLIST:
            return []
        return [h.strip() for h in self.PROD_DB_HOST_ALLOWLIST.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
