"""
Rules API

CRUD for crop rule templates (admin only).
GET  /api/v1/rules
POST /api/v1/rules
PUT  /api/v1/rules/{rule_id}

MSDD 1.4 — rule_version_applied tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.crop_rule_template import CropRuleTemplate

router = APIRouter(prefix="/rules", tags=["Crop Rules"])


class RuleCreateRequest(BaseModel):
    crop_type: str
    variety: Optional[str] = None
    region: Optional[str] = None
    version_id: str = "1.0"
    effective_from_date: date
    stage_definitions: list
    risk_parameters: dict
    irrigation_windows: Optional[dict] = None
    fertilizer_windows: Optional[dict] = None
    harvest_windows: Optional[dict] = None
    drift_limits: Optional[dict] = None
    description: Optional[str] = None


class RuleResponse(BaseModel):
    id: str
    crop_type: str
    variety: Optional[str]
    region: Optional[str]
    version_id: str
    effective_from_date: date
    is_active: str
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=list[RuleResponse])
async def list_rules(
    crop_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List crop rule templates."""
    query = db.query(CropRuleTemplate).filter(CropRuleTemplate.is_deleted == False)
    if crop_type:
        query = query.filter(CropRuleTemplate.crop_type == crop_type)
    if active_only:
        query = query.filter(CropRuleTemplate.is_active == "active")
    rules = query.order_by(CropRuleTemplate.created_at.desc()).all()
    return [RuleResponse.model_validate(r) for r in rules]


@router.post(
    "/",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["admin"]))],
)
async def create_rule(
    data: RuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new crop rule template (admin only)."""
    rule = CropRuleTemplate(
        crop_type=data.crop_type,
        variety=data.variety,
        region=data.region,
        version_id=data.version_id,
        effective_from_date=data.effective_from_date,
        stage_definitions=data.stage_definitions,
        risk_parameters=data.risk_parameters,
        irrigation_windows=data.irrigation_windows or {},
        fertilizer_windows=data.fertilizer_windows or {},
        harvest_windows=data.harvest_windows or {},
        drift_limits=data.drift_limits or {},
        description=data.description,
        created_by=current_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.put(
    "/{rule_id}",
    response_model=RuleResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def update_rule(
    rule_id: UUID,
    data: RuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a crop rule template (admin only). Creates new version."""
    existing = db.query(CropRuleTemplate).filter(
        CropRuleTemplate.id == rule_id,
        CropRuleTemplate.is_deleted == False,
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Rule template not found")

    # Deprecate old version
    existing.is_active = "deprecated"

    # Create new version
    new_rule = CropRuleTemplate(
        crop_type=data.crop_type,
        variety=data.variety,
        region=data.region,
        version_id=data.version_id,
        effective_from_date=data.effective_from_date,
        stage_definitions=data.stage_definitions,
        risk_parameters=data.risk_parameters,
        irrigation_windows=data.irrigation_windows or {},
        fertilizer_windows=data.fertilizer_windows or {},
        harvest_windows=data.harvest_windows or {},
        drift_limits=data.drift_limits or {},
        description=data.description,
        created_by=current_user.id,
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return RuleResponse.model_validate(new_rule)
