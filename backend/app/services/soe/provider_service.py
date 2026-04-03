"""
Provider Service

Business logic for service provider CRUD.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import Optional, List, Dict, Any

from app.models.service_provider import ServiceProvider
from app.models.user import User
from app.schemas.service_provider import ProviderCreate, ProviderUpdate
from fastapi import HTTPException, status


class ProviderService:
    def __init__(self, db: Session):
        self.db = db

    def create_provider(self, user: User, data: ProviderCreate) -> ServiceProvider:
        """Register a user as a service provider."""

        # Check if already registered
        existing = self.db.query(ServiceProvider).filter(
            ServiceProvider.user_id == user.id,
            ServiceProvider.is_deleted == False,
        ).first()

        if existing:
            raise ValueError("User is already registered as a service provider")
            
        # Role transition to Provider
        if user.role != "provider":
            user.role = "provider"
            self.db.add(user)

        provider = ServiceProvider(
            user_id=user.id,
            business_name=data.business_name,
            service_type=data.service_type,
            region=data.region,
            sub_region=data.sub_region,
            service_radius_km=data.service_radius_km,
            crop_specializations=data.crop_specializations,
            description=data.description,
        )
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def list_providers(
        self,
        region: Optional[str] = None,
        crop_type: Optional[str] = None,
        service_type: Optional[str] = None,
        is_verified: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> List[ServiceProvider]:
        """List providers with optional filtering."""

        query = self.db.query(ServiceProvider).filter(
            ServiceProvider.is_deleted == False,
            ServiceProvider.is_suspended == False,
        )

        if region:
            query = query.filter(ServiceProvider.region == region)
        if service_type:
            query = query.filter(ServiceProvider.service_type == service_type)
        if is_verified is not None:
            query = query.filter(ServiceProvider.is_verified == is_verified)
        if crop_type:
            # Filter by crop_specializations JSONB contains
            query = query.filter(
                ServiceProvider.crop_specializations.contains([crop_type])
            )

        return query.offset((page - 1) * per_page).limit(per_page).all()

    def search_providers_ranked(
        self,
        region: Optional[str] = None,
        crop_type: Optional[str] = None,
        service_type: Optional[str] = None,
        search_text: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """Ranked provider search using Exposure Fairness constraints."""
        from app.services.soe.exposure_engine import ExposureFairnessEngine
        
        exposure_engine = ExposureFairnessEngine(self.db)
        
        results = exposure_engine.compute_rankings(
            region=region,
            service_type=service_type,
            crop_type=crop_type,
            search_text=search_text,
            limit=per_page,
            page=page
        )
        
        # Log impressions passively
        if results.get("items"):
            exposure_engine.log_impressions(results["items"], region or "Global", page)
            
        return results

    def get_provider(self, provider_id: UUID) -> Optional[ServiceProvider]:
        """Get a single provider by ID."""
        return self.db.query(ServiceProvider).filter(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_deleted == False,
        ).first()

    def update_provider(self, provider_id: UUID, user: User, data: ProviderUpdate) -> ServiceProvider:
        """Update provider profile attributes."""
        provider = self.get_provider(provider_id)
        if not provider:
            raise ValueError("Provider profile not found")
        
        # Ownership check
        if provider.user_id != user.id and user.role != "admin":
            raise ValueError("Unauthorized to update this profile")
            
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(provider, key, value)
            
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def verify_provider(self, provider_id: UUID, admin_user: User, is_verified: bool) -> ServiceProvider:
        """Verify or unverify a provider profile."""
        if admin_user.role != "admin":
            raise ValueError("Only an admin can verify providers")
            
        provider = self.get_provider(provider_id)
        if not provider:
            raise ValueError("Provider profile not found")
            
        provider.is_verified = is_verified
        self.db.commit()
        self.db.refresh(provider)
        return provider
