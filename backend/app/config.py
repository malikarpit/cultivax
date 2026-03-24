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

    # Database
    DATABASE_URL: str = "postgresql://cultivax_user:cultivax_pass@localhost:5432/cultivax_db"

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

    # Security
    PROD_DB_HOST_ALLOWLIST: str = ""  # Comma-separated prod DB hosts

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

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
