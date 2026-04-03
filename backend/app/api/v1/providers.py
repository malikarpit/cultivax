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
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.service_provider import ServiceProvider
from app.schemas.service_provider import ProviderCreate, ProviderResponse, ProviderUpdate, PaginatedRankedResponse
from app.services.soe.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.post(
    "/",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["provider"]))],
)
async def create_provider(
    data: ProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register current user as a service provider. Provider role only."""
    # Duplicate check — one profile per user
    existing = db.query(ServiceProvider).filter(
        ServiceProvider.user_id == current_user.id,
        ServiceProvider.is_deleted == False,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Provider profile already exists",
        )

    service = ProviderService(db)
    try:
        provider = service.create_provider(current_user, data)
        return ProviderResponse.model_validate(provider)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/onboard",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Become a Provider. Accessible to any logged in user.",
)
async def onboard_provider(
    data: ProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Onboarding endpoint. Upgrades logged-in user to provider role."""
    service = ProviderService(db)
    try:
        provider = service.create_provider(current_user, data)
        return ProviderResponse.model_validate(provider)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: UUID,
    data: ProviderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific provider profile. Must be owner."""
    service = ProviderService(db)
    try:
        provider = service.update_provider(provider_id, current_user, data)
        return ProviderResponse.model_validate(provider)
    except ValueError as e:
        if "Unauthorized" in str(e):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{provider_id}/verify", response_model=ProviderResponse, dependencies=[Depends(require_role(["admin"]))])
async def verify_provider(
    provider_id: UUID,
    is_verified: bool = Query(..., description="Set verification status to true or false"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user),
):
    """(Admin) Verify or Unverify a provider."""
    service = ProviderService(db)
    try:
        provider = service.verify_provider(provider_id, admin_user, is_verified)
        return ProviderResponse.model_validate(provider)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/search", response_model=PaginatedRankedResponse)
async def search_providers(
    region: Optional[str] = None,
    crop_type: Optional[str] = None,
    service_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Firmly Ranked and Exposure-capped search returning metadata logic payloads."""
    service = ProviderService(db)
    results = service.search_providers_ranked(
        region=region,
        crop_type=crop_type,
        service_type=service_type,
        search_text=search,
        page=page,
        per_page=per_page
    )
    
    # Rebuild items manually using dict to construct Response model.
    inflated_items = []
    for item in results["items"]:
        raw = item["raw_model"]
        flat_obj = {
            "id": raw.id,
            "user_id": raw.user_id,
            "business_name": raw.business_name,
            "service_type": raw.service_type,
            "region": raw.region,
            "sub_region": raw.sub_region,
            "service_radius_km": raw.service_radius_km,
            "crop_specializations": raw.crop_specializations,
            "trust_score": item["trust_score"],
            "is_verified": raw.is_verified,
            "is_suspended": raw.is_suspended,
            "description": raw.description,
            "created_at": raw.created_at,
            "ranking_score": item["ranking_score"],
            "ranking_meta": {
                "random_factor": item["random_factor"],
                "exposure_decay": item["exposure_decay"]
            }
        }
        
        # Pull optional properties if available
        if item.get("exposure_boosted"):
            flat_obj["fairness_boosted"] = True
            flat_obj["ranking_flags"] = ["FAIRNESS_BOOST"]
            
        inflated_items.append(flat_obj)
        
    return {
        "items": inflated_items,
        "total": results["total"],
        "page": results["page"],
        "limit": results["limit"]
    }

@router.get(
    "/me",
    response_model=ProviderResponse,
    summary="Get the current user's provider profile",
)
async def get_my_provider_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the ServiceProvider profile for the currently authenticated user.

    Used by the frontend to resolve the ServiceProvider.id (different from user.id)
    needed for equipment and service management routes.

    Returns 404 if the current user has no provider profile.
    """
    provider = db.query(ServiceProvider).filter(
        ServiceProvider.user_id == current_user.id,
        ServiceProvider.is_deleted == False,
    ).first()
    if not provider:
        raise HTTPException(
            status_code=404,
            detail="No provider profile found for your account. Create one first.",
        )
    return ProviderResponse.model_validate(provider)


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
