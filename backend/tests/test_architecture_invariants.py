"""Architecture invariants for event-only CTIS mutation safety."""

from datetime import date
import inspect

import pytest

from app.config import settings
from app.models.crop_instance import CropInstance
from app.services.event_dispatcher.mutation_guard import allow_ctis_mutation


def _create_crop(db, farmer_id):
    crop = CropInstance(
        farmer_id=farmer_id,
        crop_type="wheat",
        sowing_date=date(2026, 1, 1),
        region="Punjab",
        state="Created",
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


def test_soe_modules_do_not_import_ctis_state_mutators():
    import app.services.soe.request_service as request_service

    src = inspect.getsource(request_service)
    assert "crop.state =" not in src
    assert "crop.stage =" not in src


def test_direct_crop_state_write_blocked_when_guard_enabled(db, farmer_user, monkeypatch):
    monkeypatch.setattr(settings, "CTIS_MUTATION_GUARD_ENABLED", True)
    crop = _create_crop(db, farmer_user.id)

    crop.state = "Active"
    with pytest.raises(RuntimeError, match="Direct CTIS mutation blocked"):
        db.commit()
    db.rollback()


def test_guard_allows_handler_context_mutation(db, farmer_user, monkeypatch):
    monkeypatch.setattr(settings, "CTIS_MUTATION_GUARD_ENABLED", True)
    crop = _create_crop(db, farmer_user.id)

    with allow_ctis_mutation():
        crop.state = "Active"
        db.commit()

    db.refresh(crop)
    assert crop.state == "Active"