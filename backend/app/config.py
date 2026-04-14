"""
CultivaX Application Configuration

Loads settings from environment variables with sensible defaults.
Uses Pydantic Settings for type-safe configuration.
"""

import logging
from typing import List, Optional

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "CultivaX"
    APP_ENV: str = "development"
    DEBUG: bool = True
    CTIS_MUTATION_GUARD_ENABLED: bool = False

    # Database — local development default
    DATABASE_URL: str = (
        "postgresql://cultivax_user:cultivax_pass@localhost:5432/cultivax_db"
    )

    # Cloud SQL — used when deployed to Cloud Run
    CLOUD_SQL_CONNECTION_NAME: str = ""  # e.g. "project:region:instance"
    CLOUD_SQL_DB_NAME: str = "cultivax_db"
    CLOUD_SQL_DB_USER: str = "cultivax_user"
    CLOUD_SQL_DB_PASSWORD: str = ""
    CLOUD_SQL_UNIX_SOCKET: str = "/cloudsql"  # Cloud Run auto-mounts here

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting (requests per minute, per user/IP)
    RATE_LIMIT_FARMER: int = 100
    RATE_LIMIT_PROVIDER: int = 100
    RATE_LIMIT_ADMIN: int = 200
    RATE_LIMIT_DEFAULT: int = 100
    # Stricter per-path limits for auth endpoints (anti-brute-force)
    RATE_LIMIT_AUTH_SENSITIVE: int = 100  # /auth/login, /auth/request-otp

    # Redis for distributed rate limiting + idempotency
    REDIS_URL: str = ""  # e.g., redis://localhost:6379/0

    # Admin API Key
    ADMIN_API_KEY: str = ""  # Set to secure key in production
    ADMIN_API_KEYS_JSON: str = (
        ""  # JSON array/object keyring with key_id/hash/active/time-window
    )
    ADMIN_REQUIRE_API_SIGNATURE: bool = (
        False  # Require X-Signature/X-Timestamp on admin mutations
    )

    # Cloud Storage (Day 28)
    GCS_BUCKET_NAME: str = ""  # Set to enable GCS uploads, empty = local fallback
    GCS_SIGNED_URL_EXPIRY_MINUTES: int = 60
    MEDIA_UPLOAD_DIR: str = "uploads/media"  # Local fallback directory

    # Security
    PROD_DB_HOST_ALLOWLIST: str = ""  # Comma-separated prod DB hosts

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # WhatsApp
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""

    # SMS / Twilio
    SMS_PROVIDER: str = "stub" # "stub" or "twilio"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Idempotency — which POST/PUT/PATCH paths require an Idempotency-Key header
    # (MSDD FX-0010 — mandatory idempotency on high-stakes mutations)
    # Stored as comma-separated string (env var) then parsed as a list property.
    IDEMPOTENCY_REQUIRED_PATHS_RAW: str = (
        "/api/v1/service-requests,"
        "/api/v1/reviews,"
        "/api/v1/offline-sync,"
        "/api/v1/yield,"
        "/api/v1/crops/{crop_id}/sync-batch"
    )

    @property
    def effective_database_url(self) -> str:
        """
        Build the correct database URL based on environment.

        - If CLOUD_SQL_CONNECTION_NAME is set, construct a unix socket URL
          for Cloud Run (e.g. postgresql://user:pass@/db?host=/cloudsql/conn).
        - Otherwise, fall back to DATABASE_URL (for local dev / docker-compose).
        """
        if self.CLOUD_SQL_CONNECTION_NAME:
            socket_path = (
                f"{self.CLOUD_SQL_UNIX_SOCKET}/{self.CLOUD_SQL_CONNECTION_NAME}"
            )
            return (
                f"postgresql://{self.CLOUD_SQL_DB_USER}:{self.CLOUD_SQL_DB_PASSWORD}"
                f"@/{self.CLOUD_SQL_DB_NAME}?host={socket_path}"
            )
        return self.DATABASE_URL

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def prod_db_hosts(self) -> List[str]:
        if not self.PROD_DB_HOST_ALLOWLIST:
            return []
        return [h.strip() for h in self.PROD_DB_HOST_ALLOWLIST.split(",")]

    @property
    def idempotency_required_paths(self) -> List[str]:
        """Parse IDEMPOTENCY_REQUIRED_PATHS_RAW into a list."""
        return [
            p.strip()
            for p in self.IDEMPOTENCY_REQUIRED_PATHS_RAW.split(",")
            if p.strip()
        ]

    def warn_production_gaps(self) -> None:
        """
        Log warnings for missing production-critical configuration.
        Called at application startup.
        """
        if self.APP_ENV == "production":
            if not self.REDIS_URL:
                logger.warning(
                    "REDIS_URL not set in production. Rate limiting and idempotency "
                    "will fall back to in-memory (not cluster-safe). Set REDIS_URL."
                )
            if not self.ADMIN_API_KEY and not self.ADMIN_API_KEYS_JSON:
                logger.critical(
                    "No admin API key material configured in production "
                    "(ADMIN_API_KEY/ADMIN_API_KEYS_JSON). Admin endpoints will return 503."
                )
            if self.ADMIN_API_KEY and not self.ADMIN_API_KEY.startswith("sha256:"):
                logger.critical(
                    "ADMIN_API_KEY is plaintext in production. Use sha256:<hash> "
                    "or configure ADMIN_API_KEYS_JSON keyring."
                )
            if self.SECRET_KEY == "your-secret-key-change-in-production":
                logger.critical(
                    "SECRET_KEY is set to the default development value in production. "
                    "All JWT tokens are insecure. Set a strong random SECRET_KEY."
                )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
