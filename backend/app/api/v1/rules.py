"""
Rules API

CRUD for crop rule templates (admin only).
GET  /api/v1/rules  (paginated)
POST /api/v1/rules
PUT  /api/v1/rules/{rule_id}
POST /api/v1/rules/{rule_id}/validate
POST /api/v1/rules/{rule_id}/approve
POST /api/v1/rules/{rule_id}/deprecate

MSDD 1.4 — rule_version_applied tracking
"""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.admin_audit import AdminAuditLog
from app.models.crop_rule_template import CropRuleTemplate
from app.models.user import User
from app.services.admin_audit import create_audit_entry
from app.services.ctis.template_governance import TemplateGovernanceService

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
    id: UUID
    crop_type: str
    variety: Optional[str]
    region: Optional[str]
    version_id: str
    effective_from_date: date
    status: str
    validation_errors: Optional[list] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    description: Optional[str]
    created_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


@router.get(
    "/",
    dependencies=[Depends(require_role(["admin"]))],
)
async def list_rules(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    crop_type: Optional[str] = None,
    region: Optional[str] = None,
    rule_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List crop rule templates paginated. Admin only."""
    query = db.query(CropRuleTemplate).filter(CropRuleTemplate.is_deleted == False)
    if crop_type:
        query = query.filter(CropRuleTemplate.crop_type == crop_type)
    if region:
        query = query.filter(CropRuleTemplate.region == region)
    if rule_status:
        query = query.filter(CropRuleTemplate.status == rule_status)

    total = query.count()
    rules = (
        query.order_by(CropRuleTemplate.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [RuleResponse.model_validate(r) for r in rules],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


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
    """Create a new crop rule template (draft state). Admin only."""
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
        status="draft",
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.post(
    "/{rule_id}/validate",
    response_model=RuleResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def validate_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate a draft rule template semantics. Moves to validated if success."""
    svc = TemplateGovernanceService(db)
    try:
        svc.validate_template(rule_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule = db.query(CropRuleTemplate).filter(CropRuleTemplate.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.post(
    "/{rule_id}/approve",
    response_model=RuleResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def approve_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a validated rule template. Replaces active."""
    svc = TemplateGovernanceService(db)
    try:
        approve_result = svc.approve_template(rule_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Rule not found")

    if not approve_result.get("approved"):
        error = str(approve_result.get("error") or "Approval failed")
        if "Dual-approval" in error:
            raise HTTPException(status_code=403, detail=error)
        raise HTTPException(status_code=400, detail=error)

    rule = db.query(CropRuleTemplate).filter(CropRuleTemplate.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Deprecate any previously active template in the same scope.
    active_in_scope = (
        db.query(CropRuleTemplate)
        .filter(
            CropRuleTemplate.crop_type == rule.crop_type,
            CropRuleTemplate.region == rule.region,
            CropRuleTemplate.variety == rule.variety,
            CropRuleTemplate.status == "active",
            CropRuleTemplate.id != rule_id,
        )
        .all()
    )

    for old_active in active_in_scope:
        old_active.status = "deprecated"

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="rule_approved",
        entity_type="crop_rule_template",
        entity_id=rule_id,
        after_value={"crop_type": rule.crop_type},
    )

    db.commit()
    db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.post(
    "/{rule_id}/deprecate",
    response_model=RuleResponse,
    dependencies=[Depends(require_role(["admin"]))],
)
async def deprecate_rule(
    rule_id: UUID,
    reason: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deprecate an active or validated template."""
    svc = TemplateGovernanceService(db)
    try:
        result = svc.deprecate_template(rule_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Rule not found")

    if not result.get("deprecated"):
        raise HTTPException(
            status_code=400, detail=result.get("error") or "Deprecation failed"
        )

    rule = db.query(CropRuleTemplate).filter(CropRuleTemplate.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    create_audit_entry(
        db=db,
        admin_id=current_user.id,
        action="rule_deprecated",
        entity_type="crop_rule_template",
        entity_id=rule_id,
        reason=reason,
    )

    db.commit()
    db.refresh(rule)
    return RuleResponse.model_validate(rule)
