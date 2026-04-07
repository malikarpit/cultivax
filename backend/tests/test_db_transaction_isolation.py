from datetime import date

import pytest
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from app.database import engine
from app.models.crop_instance import CropInstance


def _create_crop(db, farmer_user, *, land_area: float = 1.0) -> CropInstance:
    crop = CropInstance(
        farmer_id=farmer_user.id,
        crop_type="wheat",
        sowing_date=date(2026, 1, 1),
        region="Punjab",
        land_area=land_area,
        state="Created",
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


def test_rollback_discards_uncommitted_updates(db, farmer_user):
    crop = _create_crop(db, farmer_user, land_area=1.5)

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    tx = Session()
    try:
        row = tx.query(CropInstance).filter(CropInstance.id == crop.id).with_for_update().one()
        row.land_area = 9.0
        tx.flush()
        tx.rollback()
    finally:
        tx.close()

    db.expire_all()
    persisted = db.query(CropInstance).filter(CropInstance.id == crop.id).one()
    assert persisted.land_area == pytest.approx(1.5)


def test_nowait_lock_blocks_conflicting_writer(db, farmer_user):
    crop = _create_crop(db, farmer_user, land_area=2.0)

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    s1 = Session()
    s2 = Session()
    try:
        locked = s1.query(CropInstance).filter(CropInstance.id == crop.id).with_for_update().one()
        locked.land_area = 3.0
        s1.flush()

        with pytest.raises(DBAPIError):
            s2.query(CropInstance).filter(CropInstance.id == crop.id).with_for_update(nowait=True).one()
        s2.rollback()

        s1.commit()
    finally:
        s1.close()
        s2.close()

    db.expire_all()
    persisted = db.query(CropInstance).filter(CropInstance.id == crop.id).one()
    assert persisted.land_area == pytest.approx(3.0)
