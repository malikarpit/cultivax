"""
Common Schemas

Shared schema definitions used across all modules.
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool = True
    data: Optional[T] = None
    message: str = "OK"
    timestamp: datetime = None

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs or kwargs["timestamp"] is None:
            kwargs["timestamp"] = datetime.utcnow()
        super().__init__(**kwargs)


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = 1
    per_page: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"  # asc | desc


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with metadata."""

    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int


class ErrorDetail(BaseModel):
    """Structured error detail."""

    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = None

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs or kwargs["timestamp"] is None:
            kwargs["timestamp"] = datetime.utcnow()
        super().__init__(**kwargs)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    environment: str
