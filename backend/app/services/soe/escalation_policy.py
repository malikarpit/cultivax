"""
Escalation Policy Engine — SOE Complaint Escalation

Evaluates a provider's complaint history and determines the
appropriate escalation level (Warning → Suspension → Ban).

MSDD Enhancement 3 | SOE Enhancement 3
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import func  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.service_provider import ServiceProvider  # type: ignore
from app.models.service_request import ServiceRequest  # type: ignore
from app.models.service_review import ServiceReview  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Escalation thresholds
# ---------------------------------------------------------------------------

COMPLAINT_RATIO_THRESHOLD = 0.20  # 20% complaint ratio triggers escalation
WARNING_LIMIT = 3  # ≤ 3 complaints → Warning
SUSPEND_LIMIT = 7  # ≤ 7 complaints → Temporary suspension
# > 7 complaints → Permanent suspension

# Escalation levels
LEVEL_NONE = "None"
LEVEL_WARNING = "Warning"
LEVEL_TEMP_SUSPENSION = "TemporarySuspension"
LEVEL_PERM_SUSPENSION = "PermanentSuspension"


class EscalationResult:
    """Result of an escalation policy check."""

    def __init__(
        self,
        level: str,
        complaint_count: int,
        complaint_ratio: float,
        total_reviews: int,
        message: str,
    ):
        self.level = level
        self.complaint_count = complaint_count
        self.complaint_ratio = float(round(complaint_ratio, 4))  # type: ignore
        self.total_reviews = total_reviews
        self.message = message

    def to_dict(self) -> dict:
        return {
            "escalation_level": self.level,
            "complaint_count": self.complaint_count,
            "complaint_ratio": self.complaint_ratio,
            "total_reviews": self.total_reviews,
            "message": self.message,
        }

    @property
    def requires_action(self) -> bool:
        return self.level != LEVEL_NONE


class EscalationPolicyEngine:
    """
    Evaluates a provider's complaint history and determines escalation.

    Logic (MSDD Enhancement 3):
        1. If complaint_ratio > 20%:
            - complaint_count <= 3 → Warning
            - complaint_count <= 7 → TemporarySuspension
            - complaint_count >  7 → PermanentSuspension
        2. If complaint_ratio <= 20%: No escalation
    """

    def __init__(self, db: Session):
        self.db = db

    def check_escalation(self, provider_id: UUID) -> EscalationResult:
        """
        Check the escalation status for a provider.

        Args:
            provider_id: The service provider to evaluate.

        Returns:
            EscalationResult with the determined escalation level.
        """

        # Verify provider exists
        provider = (
            self.db.query(ServiceProvider)
            .filter(
                ServiceProvider.id == provider_id,
                ServiceProvider.is_deleted == False,
            )
            .first()
        )

        if not provider:
            raise ValueError(f"ServiceProvider {provider_id} not found")

        # Count total reviews for this provider
        total_reviews = (
            self.db.query(func.count(ServiceReview.id))
            .join(ServiceRequest, ServiceReview.request_id == ServiceRequest.id)
            .filter(
                ServiceRequest.provider_id == provider_id,
                ServiceReview.is_deleted == False,
            )
            .scalar()
            or 0
        )

        # Count complaints (reviews with a complaint_category set)
        complaint_count = (
            self.db.query(func.count(ServiceReview.id))
            .join(ServiceRequest, ServiceReview.request_id == ServiceRequest.id)
            .filter(
                ServiceRequest.provider_id == provider_id,
                ServiceReview.complaint_category.isnot(None),
                ServiceReview.is_deleted == False,
            )
            .scalar()
            or 0
        )

        # Compute complaint ratio
        complaint_ratio = complaint_count / total_reviews if total_reviews > 0 else 0.0

        # Determine escalation level
        level, message = self._evaluate(complaint_count, complaint_ratio)

        result = EscalationResult(
            level=level,
            complaint_count=complaint_count,
            complaint_ratio=complaint_ratio,
            total_reviews=total_reviews,
            message=message,
        )

        if result.requires_action:
            logger.warning(
                f"Escalation for provider {provider_id}: "
                f"level={level}, complaints={complaint_count}/{total_reviews} "
                f"(ratio={complaint_ratio:.2%})"
            )
        else:
            logger.info(
                f"No escalation for provider {provider_id}: "
                f"complaints={complaint_count}/{total_reviews}"
            )

        return result

    def apply_escalation(self, provider_id: UUID) -> EscalationResult:
        """
        Check and apply escalation actions to the provider record.

        This will update the provider's suspension status if warranted.
        """
        result = self.check_escalation(provider_id)

        if not result.requires_action:
            return result

        provider = (
            self.db.query(ServiceProvider)
            .filter(ServiceProvider.id == provider_id)
            .first()
        )

        if not provider:
            return result

        if result.level == LEVEL_WARNING:
            # Log warning but don't suspend
            logger.warning(f"Provider {provider_id}: WARNING issued")

        elif result.level == LEVEL_TEMP_SUSPENSION:
            provider.is_suspended = True
            provider.suspension_reason = (
                f"Temporary suspension: {result.complaint_count} complaints "
                f"({result.complaint_ratio:.0%} complaint ratio)"
            )
            self.db.commit()
            logger.warning(f"Provider {provider_id}: TEMPORARILY SUSPENDED")

        elif result.level == LEVEL_PERM_SUSPENSION:
            provider.is_suspended = True
            provider.suspension_reason = (
                f"Permanent suspension: {result.complaint_count} complaints "
                f"({result.complaint_ratio:.0%} complaint ratio). "
                "Contact admin for appeal."
            )
            self.db.commit()
            logger.error(f"Provider {provider_id}: PERMANENTLY SUSPENDED")

        return result

    def _evaluate(
        self, complaint_count: int, complaint_ratio: float
    ) -> tuple[str, str]:
        """Determine escalation level from complaint data."""

        if complaint_ratio <= COMPLAINT_RATIO_THRESHOLD:
            return LEVEL_NONE, "Complaint ratio within acceptable limits."

        if complaint_count <= WARNING_LIMIT:
            return (
                LEVEL_WARNING,
                f"Warning: {complaint_count} complaints received. "
                "Improve service quality to avoid suspension.",
            )

        if complaint_count <= SUSPEND_LIMIT:
            return (
                LEVEL_TEMP_SUSPENSION,
                f"Temporary suspension: {complaint_count} complaints. "
                "Account suspended pending review.",
            )

        return (
            LEVEL_PERM_SUSPENSION,
            f"Permanent suspension: {complaint_count} complaints. "
            "Account permanently suspended. Contact admin for appeal.",
        )
