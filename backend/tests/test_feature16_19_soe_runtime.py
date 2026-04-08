from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.service_provider import ServiceProvider
from app.models.service_request import ServiceRequest
from app.models.service_request_event import ServiceRequestEvent
from app.models.user import User
from app.security.auth import create_access_token
from app.services.soe.exposure_engine import ExposureFairnessEngine


def _create_farmer(db, idx: int) -> User:
    user = User(
        id=uuid4(),
        full_name=f"Farmer {idx}",
        phone=f"+91{(9000000000 + idx):010d}",
        email=f"farmer-{idx}-{uuid4().hex[:6]}@test.in",
        password_hash="hash",
        role="farmer",
        region="Punjab",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_provider(db) -> ServiceProvider:
    provider_user = User(
        id=uuid4(),
        full_name="Provider User",
        phone=f"+91{uuid4().int % 10**10:010d}",
        email=f"provider-{uuid4().hex[:6]}@test.in",
        password_hash="hash",
        role="provider",
        region="Punjab",
        is_active=True,
    )
    db.add(provider_user)
    db.commit()
    db.refresh(provider_user)

    provider = ServiceProvider(
        id=uuid4(),
        user_id=provider_user.id,
        business_name="Punjab Services",
        service_type="advisory",
        region="Punjab",
        crop_specializations=["wheat"],
        trust_score=0.5,
        is_verified=True,
        contact_name="Provider",
        contact_phone=provider_user.phone,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def _create_completed_request(db, farmer: User, provider: ServiceProvider) -> ServiceRequest:
    req = ServiceRequest(
        id=uuid4(),
        farmer_id=farmer.id,
        provider_id=provider.id,
        service_type="advisory",
        status="Completed",
        preferred_date=datetime.now(timezone.utc) - timedelta(days=2),
        completed_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def _headers_for(user: User) -> dict:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def test_review_submission_triggers_trust_fraud_escalation_runtime(client, db):
    provider = _create_provider(db)
    farmers = [_create_farmer(db, i) for i in range(1, 4)]
    requests = [_create_completed_request(db, farmer, provider) for farmer in farmers]

    resp = client.post(
        "/api/v1/reviews/",
        json={
            "request_id": str(requests[0].id),
            "rating": 2.0,
            "comment": "Service was delayed",
            "complaint_category": "late_arrival",
        },
        headers=_headers_for(farmers[0]),
    )
    assert resp.status_code == 201, resp.text

    db.refresh(provider)
    assert provider.completion_count == 3
    assert provider.complaint_count >= 1

    events = db.query(ServiceRequestEvent).filter(
        ServiceRequestEvent.request_id == requests[0].id
    ).all()
    event_types = {e.event_type for e in events}
    assert "Reviewed" in event_types
    assert "review_risk_evaluated" in event_types

    eval_event = next(e for e in events if e.event_type == "review_risk_evaluated")
    assert "fraud=" in (eval_event.notes or "")
    assert "escalation=" in (eval_event.notes or "")


def test_complaint_heavy_provider_gets_suspended(client, db):
    provider = _create_provider(db)
    farmers = [_create_farmer(db, i) for i in range(10, 14)]
    requests = [_create_completed_request(db, farmer, provider) for farmer in farmers]

    for idx, req in enumerate(requests):
        resp = client.post(
            "/api/v1/reviews/",
            json={
                "request_id": str(req.id),
                "rating": 1.0,
                "comment": f"Complaint {idx}",
                "complaint_category": "quality_issue",
            },
            headers=_headers_for(farmers[idx]),
        )
        assert resp.status_code == 201, resp.text

    db.refresh(provider)
    assert provider.is_suspended is True
    assert provider.suspension_reason is not None


def test_exposure_distribution_under_rolling_window(db, monkeypatch):
    monkeypatch.setattr("app.services.soe.exposure_engine.random.uniform", lambda a, b: 0.5)

    providers = []
    for idx, trust in enumerate([0.92, 0.90, 0.88, 0.70, 0.68, 0.66], start=1):
        user = User(
            id=uuid4(),
            full_name=f"Fairness Provider User {idx}",
            phone=f"+91{(9100000000 + idx):010d}",
            email=f"fairness-provider-{idx}-{uuid4().hex[:4]}@test.in",
            password_hash="hash",
            role="provider",
            region="Punjab",
            is_active=True,
        )
        db.add(user)
        db.flush()

        provider = ServiceProvider(
            id=uuid4(),
            user_id=user.id,
            business_name=f"Fairness Provider {idx}",
            service_type="advisory",
            region="Punjab",
            crop_specializations=["wheat"],
            trust_score=trust,
            is_verified=True,
            contact_name=f"Provider {idx}",
            contact_phone=user.phone,
        )
        db.add(provider)
        providers.append(provider)

    db.commit()

    engine = ExposureFairnessEngine(db)
    ranked = engine.compute_rankings(region="Punjab", limit=20)

    assert len(ranked["items"]) >= 6
    top3_sum = sum(item["ranking_score"] for item in ranked["items"][:3])
    total_sum = sum(item["ranking_score"] for item in ranked["items"])
    assert (top3_sum / max(total_sum, 1e-9)) <= 0.70


def test_trust_score_decays_with_inactivity(db):
    from app.services.soe.trust_engine import TrustScoreEngine
    
    provider = _create_provider(db)
    farmer = _create_farmer(db, 99)
    
    # 1. Create 3 requests that completed 6 months ago to meet MIN_REQUESTS_FOR_TRUST
    for i in range(3):
        req = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type="advisory",
            status="Completed",
            preferred_date=datetime.now(timezone.utc) - timedelta(days=190),
            completed_at=datetime.now(timezone.utc) - timedelta(days=180),
            updated_at=datetime.now(timezone.utc) - timedelta(days=180),
        )
        db.add(req)
    db.commit()
    
    engine = TrustScoreEngine(db)
    result = engine.compute_trust_score(provider.id)
    
    # It should have decayed (~6 months implies 0.98^6 = ~0.88 multiplier)
    assert result["months_inactive"] >= 5.5
    assert result["trust_score"] < 0.90  # Initial score would be bounded, but decayed
    
    # 2. Add a recent action, effectively resetting decay
    req2 = ServiceRequest(
        id=uuid4(),
        farmer_id=farmer.id,
        provider_id=provider.id,
        service_type="advisory",
        status="Completed",
        preferred_date=datetime.now(timezone.utc) - timedelta(days=2),
        completed_at=datetime.now(timezone.utc) - timedelta(days=1),
        updated_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(req2)
    db.commit()
    db.refresh(req2)
    
    result2 = engine.compute_trust_score(provider.id)
    assert result2["months_inactive"] < 1.0
    assert result2["trust_score"] > result["trust_score"]
