from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from app.models.crop_instance import CropInstance
from app.models.regional_cluster import RegionalCluster
from app.models.user import User
from app.security.auth import create_access_token
from app.services.event_dispatcher.db_dispatcher import DBEventDispatcher
from app.services.event_dispatcher.event_types import MLEvents
from tests.conftest import unwrap


def _create_user(db, idx: int = 1) -> User:
    user = User(
        id=uuid4(),
        full_name=f"Cluster Farmer {idx}",
        phone=f"+91{(9200000000 + idx):010d}",
        email=f"cluster-farmer-{idx}-{uuid4().hex[:6]}@test.com",
        password_hash="hashed_test_password",
        role="farmer",
        region="Punjab",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers_for(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def _create_ready_crop(
    db,
    farmer_id: UUID,
    *,
    crop_type: str = "wheat",
    region: str = "Punjab",
    season: str = "Rabi",
    stage_offset_days: int = 0,
) -> CropInstance:
    crop = CropInstance(
        id=uuid4(),
        farmer_id=farmer_id,
        crop_type=crop_type,
        sowing_date=date.today() - timedelta(days=100),
        region=region,
        seasonal_window_category=season,
        state="ReadyToHarvest",
        stage_offset_days=stage_offset_days,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


def test_new_yield_submission_updates_regional_cluster_prospectively(client, db):
    farmer = _create_user(db, idx=1)
    headers = _headers_for(farmer)
    crop = _create_ready_crop(db, farmer.id, stage_offset_days=4)

    resp = client.post(
        f"/api/v1/crops/{crop.id}/yield",
        json={"reported_yield": 8.0, "yield_unit": "kg/acre"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    DBEventDispatcher(db).process_pending(batch_size=50)

    cluster = db.query(RegionalCluster).filter(
        RegionalCluster.crop_type == "wheat",
        RegionalCluster.region == "Punjab",
        RegionalCluster.season == "Rabi",
        RegionalCluster.is_deleted == False,
    ).first()
    assert cluster is not None
    assert cluster.sample_size == 1
    assert cluster.avg_delay == pytest.approx(4.0, abs=0.0001)
    assert cluster.avg_yield == pytest.approx(8.0, abs=0.0001)
    assert cluster.last_updated_from_count == 1


def test_non_prospective_events_do_not_rewrite_clusters(client, db):
    cluster = RegionalCluster(
        id=uuid4(),
        crop_type="wheat",
        region="Punjab",
        season="Rabi",
        avg_delay=2.0,
        avg_yield=6.0,
        sample_size=2,
        last_updated_from_count=2,
    )
    db.add(cluster)
    db.commit()

    dispatcher = DBEventDispatcher(db)
    dispatcher.publish(
        event_type=MLEvents.CLUSTER_UPDATED,
        entity_type="YieldRecord",
        entity_id=uuid4(),
        payload={
            "crop_type": "wheat",
            "region": "Punjab",
            "season": "Rabi",
            "delay_days": 99,
            "yield_value": 99,
            "prospective": False,
        },
    )
    dispatcher.process_pending(batch_size=50)

    db.refresh(cluster)
    assert cluster.sample_size == 2
    assert cluster.avg_delay == pytest.approx(2.0, abs=0.0001)
    assert cluster.avg_yield == pytest.approx(6.0, abs=0.0001)

    farmer = _create_user(db, idx=2)
    headers = _headers_for(farmer)
    crop = _create_ready_crop(db, farmer.id, stage_offset_days=4)

    submit = client.post(
        f"/api/v1/crops/{crop.id}/yield",
        json={"reported_yield": 8.0, "yield_unit": "kg/acre"},
        headers=headers,
    )
    assert submit.status_code == 201, submit.text
    unwrap(submit)

    dispatcher.process_pending(batch_size=50)

    db.refresh(cluster)
    assert cluster.sample_size == 3
    assert cluster.avg_delay == pytest.approx((2.0 * 2 + 4.0) / 3.0, abs=0.0001)
    assert cluster.avg_yield == pytest.approx((6.0 * 2 + 8.0) / 3.0, abs=0.0001)
    assert cluster.last_updated_from_count == 3
