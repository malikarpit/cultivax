"""
Providers API

Service Provider CRUD endpoints.
POST /api/v1/providers
GET  /api/v1/providers
GET  /api/v1/providers/{provider_id}
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.service_provider import ProviderCreate, ProviderResponse
from app.services.soe.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: ProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register current user as a service provider."""
    service = ProviderService(db)
    try:
        provider = service.create_provider(current_user, data)
        return ProviderResponse.model_validate(provider)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/", response_model=list[ProviderResponse])
async def list_providers(
    region: Optional[str] = None,
    crop_type: Optional[str] = None,
    service_type: Optional[str] = None,
    is_verified: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List service providers with filtering."""
    service = ProviderService(db)
    providers = service.list_providers(
        region=region,
        crop_type=crop_type,
        service_type=service_type,
        is_verified=is_verified,
        page=page,
        per_page=per_page,
    )
    return [ProviderResponse.model_validate(p) for p in providers]


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single provider by ID."""
    service = ProviderService(db)
    provider = service.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return ProviderResponse.model_validate(provider)
