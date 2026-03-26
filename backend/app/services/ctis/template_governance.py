"""
Rule Template Governance Service — 26 march: Phase 7A

Handles the governance lifecycle of crop rule templates:
  draft → validated → active → deprecated

Includes:
  - Structural validation (chronological stages, risk params, windows)
  - Dual-admin approval workflow
  - Template deprecation
"""

import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session  # type: ignore

from app.models.crop_rule_template import CropRuleTemplate  # type: ignore

logger = logging.getLogger(__name__)

# Valid status transitions
VALID_TRANSITIONS = {
    "draft": ["validated"],
    "validated": ["active", "draft"],  # Can be sent back to draft
    "active": ["deprecated"],
    "deprecated": [],  # Terminal state
}

# Required stage fields
REQUIRED_STAGE_FIELDS = {"name", "duration_days"}

# Required risk parameter fields
REQUIRED_RISK_FIELDS = {"stress_threshold", "max_drift_days"}


class TemplateGovernanceService:
    """
    Manages the governance lifecycle of crop rule templates.

    Workflow:
      1. Admin creates template (status=draft)
      2. Admin triggers validation → status=validated (or stays draft with errors)
      3. A SECOND admin approves → status=active
      4. Superseded templates → status=deprecated
    """

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------
    # Validation (draft → validated)
    # -------------------------------------------------------------------

    def validate_template(self, template_id: UUID) -> dict:
        """
        Validate a draft template's structure.

        Checks:
          1. Stage definitions are in chronological order
          2. Stage durations are positive integers
          3. Risk parameters have required fields with valid values
          4. Windows reference existing stages

        Returns:
            {"valid": bool, "errors": list, "status": str}
        """
        template = self._get_template(template_id)

        if template.status != "draft":
            return {
                "valid": False,
                "errors": [f"Cannot validate template in '{template.status}' status. Must be 'draft'."],
                "status": template.status,
            }

        errors = []

        # Check 1: Stage definitions
        errors.extend(self._validate_stages(template.stage_definitions or []))

        # Check 2: Risk parameters
        errors.extend(self._validate_risk_params(template.risk_parameters or {}))

        # Check 3: Window references
        stage_names = {s.get("name") for s in (template.stage_definitions or []) if isinstance(s, dict)}
        errors.extend(self._validate_windows(template.irrigation_windows or {}, stage_names, "irrigation"))
        errors.extend(self._validate_windows(template.fertilizer_windows or {}, stage_names, "fertilizer"))

        # Persist validation result
        template.validation_errors = errors

        if not errors:
            template.status = "validated"
            self.db.commit()
            logger.info(f"Template {template_id} validated successfully → status=validated")
            return {"valid": True, "errors": [], "status": "validated"}
        else:
            self.db.commit()
            logger.warning(f"Template {template_id} validation failed: {len(errors)} errors")
            return {"valid": False, "errors": errors, "status": "draft"}

    def _validate_stages(self, stages: list) -> List[str]:
        """Check chronological order and required fields."""
        errors = []

        if not stages:
            errors.append("stage_definitions is empty — at least one stage required")
            return errors

        cumulative_days = 0
        for i, stage in enumerate(stages):
            if not isinstance(stage, dict):
                errors.append(f"Stage {i}: must be a dict, got {type(stage).__name__}")
                continue

            # Required fields
            missing = REQUIRED_STAGE_FIELDS - set(stage.keys())
            if missing:
                errors.append(f"Stage {i}: missing required fields: {missing}")
                continue

            # Duration must be positive
            duration = stage.get("duration_days", 0)
            if not isinstance(duration, (int, float)) or duration <= 0:
                errors.append(f"Stage {i} ({stage.get('name', '?')}): duration_days must be positive, got {duration}")

            # Check chronological ordering (cumulative)
            start_day = stage.get("start_day", cumulative_days)
            if start_day < cumulative_days:
                errors.append(
                    f"Stage {i} ({stage.get('name', '?')}): start_day {start_day} "
                    f"overlaps with previous stage ending at day {cumulative_days}"
                )
            cumulative_days = start_day + duration

        return errors

    def _validate_risk_params(self, params: dict) -> List[str]:
        """Check risk parameters have required fields with valid values."""
        errors = []

        if not params:
            errors.append("risk_parameters is empty — required fields: " + str(REQUIRED_RISK_FIELDS))
            return errors

        missing = REQUIRED_RISK_FIELDS - set(params.keys())
        if missing:
            errors.append(f"risk_parameters missing fields: {missing}")

        # Numeric validation
        for field in ["stress_threshold", "max_drift_days"]:
            val = params.get(field)
            if val is not None and not isinstance(val, (int, float)):
                errors.append(f"risk_parameters.{field} must be numeric, got {type(val).__name__}")
            if isinstance(val, (int, float)) and val < 0:
                errors.append(f"risk_parameters.{field} must be non-negative, got {val}")

        return errors

    def _validate_windows(self, windows: dict, stage_names: set, window_type: str) -> List[str]:
        """Check window references point to valid stages."""
        errors = []
        if not windows:
            return errors

        for stage_ref in windows.keys():
            if stage_ref not in stage_names:
                errors.append(
                    f"{window_type}_windows references unknown stage '{stage_ref}'. "
                    f"Valid stages: {stage_names}"
                )
        return errors

    # -------------------------------------------------------------------
    # Dual-Admin Approval (validated → active)
    # -------------------------------------------------------------------

    def approve_template(self, template_id: UUID, approver_id: UUID) -> dict:
        """
        Second admin approves a validated template → status=active.

        Args:
            template_id: UUID of the template
            approver_id: UUID of the approving admin (must differ from creator)

        Returns:
            {"approved": bool, "error": str | None, "status": str}
        """
        template = self._get_template(template_id)

        if template.status != "validated":
            return {
                "approved": False,
                "error": f"Cannot approve template in '{template.status}' status. Must be 'validated'.",
                "status": template.status,
            }

        # Dual-approval: approver must differ from creator
        if template.created_by and template.created_by == approver_id:
            return {
                "approved": False,
                "error": "Dual-approval violation: approver cannot be the same as creator.",
                "status": template.status,
            }

        template.status = "active"
        template.approved_by = approver_id
        template.approved_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(f"Template {template_id} approved by {approver_id} → status=active")
        return {"approved": True, "error": None, "status": "active"}

    # -------------------------------------------------------------------
    # Deprecation (active → deprecated)
    # -------------------------------------------------------------------

    def deprecate_template(self, template_id: UUID) -> dict:
        """Mark an active template as deprecated."""
        template = self._get_template(template_id)

        if template.status != "active":
            return {
                "deprecated": False,
                "error": f"Cannot deprecate template in '{template.status}' status.",
                "status": template.status,
            }

        template.status = "deprecated"
        self.db.commit()

        logger.info(f"Template {template_id} deprecated")
        return {"deprecated": True, "error": None, "status": "deprecated"}

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _get_template(self, template_id: UUID) -> CropRuleTemplate:
        """Load a template or raise ValueError."""
        template = (
            self.db.query(CropRuleTemplate)
            .filter(
                CropRuleTemplate.id == template_id,
                CropRuleTemplate.is_deleted == False,
            )
            .first()
        )
        if not template:
            raise ValueError(f"CropRuleTemplate {template_id} not found")
        return template
