"""
ML Model Registry API

Endpoints for managing ML model versions.
GET  /api/v1/ml/models
POST /api/v1/ml/models  (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List, Any
from pydantic import BaseModel
from app.models.admin_audit import AdminAuditLog
from app.models.ml_feedback import MLFeedback
from app.models.ml_training import MLTrainingAudit
from app.services.admin_audit import create_audit_entry

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.services.ml.model_registry import ModelRegistry

router = APIRouter(prefix="/ml", tags=["ML Models"])


class ModelCreateRequest(BaseModel):
    model_name: str
    model_type: str
    version: int
    description: Optional[str] = None
    metrics: Optional[dict] = None
    training_dataset_ref: Optional[str] = None


class ModelResponse(BaseModel):
    id: str
    model_name: str
    model_type: str
    version: int
    is_active: bool
    description: Optional[str]
    metrics: Optional[dict]
    created_at: Any

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

@router.post(
    "/models/{model_id}/activate",
    response_model=ModelResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def activate_ml_model(
    model_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a model version, natively displacing the older instance."""
    if not reason:
        raise HTTPException(status_code=400, detail="Missing required 'reason' parameter.")
        
    registry = ModelRegistry(db)
    try:
        model = registry.activate_model(model_id)
        
        # Admin Audit tracing via helper
        create_audit_entry(
            db=db,
            admin_id=current_user.id,
            action="activate_ml_model",
            entity_type="ml_model",
            entity_id=model.id,
            reason=reason,
            after_value={"version": model.version, "model_name": model.model_name}
        )
        
        return ModelResponse.model_validate(model)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/models/{model_id}/deactivate",
    response_model=ModelResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def deactivate_ml_model(
    model_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gracefully draft an active model removing it from predict paths."""
    if not reason:
        raise HTTPException(status_code=400, detail="Missing required 'reason' parameter.")
        
    registry = ModelRegistry(db)
    try:
        model = registry.deactivate_model(model_id)
        
        # Admin Audit tracing via helper
        create_audit_entry(
            db=db,
            admin_id=current_user.id,
            action="deactivate_ml_model",
            entity_type="ml_model",
            entity_id=model.id,
            reason=reason,
            after_value={"version": model.version, "model_name": model.model_name}
        )
        
        return ModelResponse.model_validate(model)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

# -- Feedback and Training --

class MLFeedbackCreate(BaseModel):
    crop_instance_id: UUID
    prediction_id: str
    feedback_type: str
    farmer_notes: Optional[str] = None
    reason: Optional[str] = None
    original_prediction: Optional[dict] = None
    original_confidence: Optional[float] = None

@router.post("/feedback", status_code=201)
async def create_ml_feedback(
    data: MLFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Farmer feedback mapped straight to Model degradation audits."""
    fb = MLFeedback(**data.model_dump())
    db.add(fb)
    db.commit()
    return {"status": "success", "id": str(fb.id)}

@router.get("/feedback", dependencies=[Depends(require_role(["admin"]))])
async def list_ml_feedback(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Read ML drift constraints via historical feedback."""
    return db.query(MLFeedback).order_by(MLFeedback.created_at.desc()).limit(limit).all()

class MLTrainingAuditCreate(BaseModel):
    model_id: UUID
    dataset_size: int
    training_duration_seconds: Optional[float] = None
    accuracy: Optional[float] = None
    loss: Optional[float] = None
    dataset_metadata: Optional[dict] = None

@router.post("/training-audits", status_code=201, dependencies=[Depends(require_role(["admin"]))])
async def create_ml_training_audit(
    data: MLTrainingAuditCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Audit pipeline storing training outputs directly mapping accuracy jumps."""
    ta = MLTrainingAudit(**data.model_dump(), triggered_by=current_user.id)
    db.add(ta)
    db.commit()
    return {"status": "success", "id": str(ta.id)}

@router.get("/training-audits", dependencies=[Depends(require_role(["admin"]))])
async def list_ml_training_audits(
    model_id: Optional[UUID] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trace exact accuracy scores mapped against database models."""
    q = db.query(MLTrainingAudit)
    if model_id:
        q = q.filter(MLTrainingAudit.model_id == model_id)
    return q.order_by(MLTrainingAudit.created_at.desc()).limit(limit).all()
