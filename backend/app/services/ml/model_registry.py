"""
ML Model Registry Service

Manages ML model version lifecycle: registration, activation,
deactivation, and querying.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

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
        model_type: str,
        version: str,
        model_name: Optional[str] = None,
        artifact_path: Optional[str] = None,
        description: Optional[str] = None,
        metrics: Optional[dict] = None,
        training_dataset_ref: Optional[str] = None,
        registered_by: Optional[UUID] = None,
    ) -> MLModel:
        """Register a new ML model version."""
        resolved_model_name = model_name or model_type

        # Build duplicate check filters only with fields available on the model.
        duplicate_filters = [
            MLModel.model_name == resolved_model_name,
            MLModel.version == version,
        ]
        if hasattr(MLModel, "is_deleted"):
            duplicate_filters.append(MLModel.is_deleted == False)

        # Check for duplicate version
        existing = self.db.query(MLModel).filter(*duplicate_filters).first()

        if existing:
            raise ValueError(
                f"Model '{resolved_model_name}' version '{version}' already exists"
            )

        model_kwargs = {
            "model_name": resolved_model_name,
            "model_type": model_type,
            "version": version,
        }

        if hasattr(MLModel, "file_path"):
            model_kwargs["file_path"] = artifact_path
        if hasattr(MLModel, "training_metadata"):
            model_kwargs["training_metadata"] = metrics or {}
        if hasattr(MLModel, "accuracy") and metrics and "accuracy" in metrics:
            model_kwargs["accuracy"] = metrics["accuracy"]
        if hasattr(MLModel, "status"):
            model_kwargs["status"] = "draft"
        if hasattr(MLModel, "description"):
            model_kwargs["description"] = description
        if hasattr(MLModel, "evaluation_metrics"):
            model_kwargs["evaluation_metrics"] = metrics or {}
        if hasattr(MLModel, "training_dataset_reference"):
            model_kwargs["training_dataset_reference"] = training_dataset_ref
        if hasattr(MLModel, "is_active"):
            model_kwargs["is_active"] = False
        if hasattr(MLModel, "registered_by"):
            model_kwargs["registered_by"] = registered_by

        model = MLModel(**model_kwargs)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Registered ML model: {resolved_model_name} v{version}")
        return model

    def activate_model(self, model_id: UUID) -> MLModel:
        """
        Activate a model version. Deactivates other versions of same name.
        """
        model_filters = [MLModel.id == model_id]
        if hasattr(MLModel, "is_deleted"):
            model_filters.append(MLModel.is_deleted == False)

        model = self.db.query(MLModel).filter(*model_filters).first()

        if not model:
            raise LookupError(f"Model {model_id} not found")

        # Deactivate other versions of same model
        deactivation_filters = [
            MLModel.model_name == model.model_name,
            MLModel.id != model_id,
        ]
        if hasattr(MLModel, "is_active"):
            deactivation_filters.append(MLModel.is_active == True)
        elif hasattr(MLModel, "status"):
            deactivation_filters.append(MLModel.status == "active")

        updates = (
            {"is_active": False}
            if hasattr(MLModel, "is_active")
            else {"status": "draft"}
        )
        self.db.query(MLModel).filter(*deactivation_filters).update(updates)

        if hasattr(model, "is_active"):
            model.is_active = True
        if hasattr(model, "status"):
            model.status = "active"
        if hasattr(model, "activated_at"):
            model.activated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Activated model: {model.model_name} v{model.version}")
        return model

    def deactivate_model(self, model_id: UUID) -> MLModel:
        """Deactivate a model version."""
        model_filters = [MLModel.id == model_id]
        if hasattr(MLModel, "is_deleted"):
            model_filters.append(MLModel.is_deleted == False)

        model = self.db.query(MLModel).filter(*model_filters).first()

        if not model:
            raise LookupError(f"Model {model_id} not found")

        if hasattr(model, "is_active"):
            model.is_active = False
        if hasattr(model, "status"):
            model.status = "draft"
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Deactivated model: {model.model_name} v{model.version}")
        return model

    def get_active_model(self, model_name: str) -> Optional[MLModel]:
        """Get the currently active version of a model."""
        active_filters = [MLModel.model_name == model_name]
        if hasattr(MLModel, "is_active"):
            active_filters.append(MLModel.is_active == True)
        elif hasattr(MLModel, "status"):
            active_filters.append(MLModel.status == "active")
        if hasattr(MLModel, "is_deleted"):
            active_filters.append(MLModel.is_deleted == False)

        return self.db.query(MLModel).filter(*active_filters).first()

    def list_models(
        self,
        model_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[MLModel]:
        """List registered models with optional filtering."""
        query = self.db.query(MLModel)
        if hasattr(MLModel, "is_deleted"):
            query = query.filter(MLModel.is_deleted == False)

        if model_type:
            query = query.filter(MLModel.model_type == model_type)
        if active_only:
            if hasattr(MLModel, "is_active"):
                query = query.filter(MLModel.is_active == True)
            elif hasattr(MLModel, "status"):
                query = query.filter(MLModel.status == "active")

        return query.order_by(MLModel.created_at.desc()).all()
