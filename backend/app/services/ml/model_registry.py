"""
ML Model Registry Service

Manages ML model version lifecycle: registration, activation,
deactivation, and querying.
"""

from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone
import logging

from app.models.ml_model import MLModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    ML model version management service.

    Supports:
    - Registering new model versions
    - Activating/deactivating versions
    - Querying active models by type
    """

    def __init__(self, db: Session):
        self.db = db

    def register_model(
        self,
        model_name: str,
        model_type: str,
        version: str,
        description: Optional[str] = None,
        metrics: Optional[dict] = None,
        training_dataset_ref: Optional[str] = None,
        registered_by: Optional[UUID] = None,
    ) -> MLModel:
        """Register a new ML model version."""
        # Check for duplicate version
        existing = self.db.query(MLModel).filter(
            MLModel.model_name == model_name,
            MLModel.version == version,
            MLModel.is_deleted == False,
        ).first()

        if existing:
            raise ValueError(
                f"Model '{model_name}' version '{version}' already exists"
            )

        model = MLModel(
            model_name=model_name,
            model_type=model_type,
            version=version,
            description=description,
            evaluation_metrics=metrics or {},
            training_dataset_reference=training_dataset_ref,
            is_active=False,  # Must be explicitly activated
            registered_by=registered_by,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Registered ML model: {model_name} v{version}")
        return model

    def activate_model(self, model_id: UUID) -> MLModel:
        """
        Activate a model version. Deactivates other versions of same name.
        """
        model = self.db.query(MLModel).filter(
            MLModel.id == model_id,
            MLModel.is_deleted == False,
        ).first()

        if not model:
            raise LookupError(f"Model {model_id} not found")

        # Deactivate other versions of same model
        self.db.query(MLModel).filter(
            MLModel.model_name == model.model_name,
            MLModel.id != model_id,
            MLModel.is_active == True,
        ).update({"is_active": False})

        model.is_active = True
        model.activated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Activated model: {model.model_name} v{model.version}")
        return model

    def deactivate_model(self, model_id: UUID) -> MLModel:
        """Deactivate a model version."""
        model = self.db.query(MLModel).filter(
            MLModel.id == model_id,
            MLModel.is_deleted == False,
        ).first()

        if not model:
            raise LookupError(f"Model {model_id} not found")

        model.is_active = False
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Deactivated model: {model.model_name} v{model.version}")
        return model

    def get_active_model(self, model_name: str) -> Optional[MLModel]:
        """Get the currently active version of a model."""
        return self.db.query(MLModel).filter(
            MLModel.model_name == model_name,
            MLModel.is_active == True,
            MLModel.is_deleted == False,
        ).first()

    def list_models(
        self,
        model_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[MLModel]:
        """List registered models with optional filtering."""
        query = self.db.query(MLModel).filter(MLModel.is_deleted == False)

        if model_type:
            query = query.filter(MLModel.model_type == model_type)
        if active_only:
            query = query.filter(MLModel.is_active == True)

        return query.order_by(MLModel.created_at.desc()).all()
