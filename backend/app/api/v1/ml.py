"""
ML Model Registry API

Endpoints for managing ML model versions.
GET  /api/v1/ml/models
POST /api/v1/ml/models  (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.services.ml.model_registry import ModelRegistry

router = APIRouter(prefix="/ml", tags=["ML Models"])


class ModelCreateRequest(BaseModel):
    model_name: str
    model_type: str
    version: str
    description: Optional[str] = None
    metrics: Optional[dict] = None
    training_dataset_ref: Optional[str] = None


class ModelResponse(BaseModel):
    id: str
    model_name: str
    model_type: str
    version: str
    is_active: bool
    description: Optional[str]
    metrics: Optional[dict]
    created_at: str

    class Config:
        from_attributes = True


@router.get("/models", response_model=list[ModelResponse])
async def list_models(
    model_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List registered ML models."""
    registry = ModelRegistry(db)
    models = registry.list_models(model_type=model_type, active_only=active_only)
    return [ModelResponse.model_validate(m) for m in models]


@router.post(
    "/models",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["admin"]))],
)
async def register_model(
    data: ModelCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new ML model version (admin only)."""
    registry = ModelRegistry(db)
    try:
        model = registry.register_model(
            model_name=data.model_name,
            model_type=data.model_type,
            version=data.version,
            description=data.description,
            metrics=data.metrics,
            training_dataset_ref=data.training_dataset_ref,
            registered_by=current_user.id,
        )
        return ModelResponse.model_validate(model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
