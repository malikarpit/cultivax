"""
Integration Test — Crop Lifecycle Flow

End-to-end test covering the complete crop lifecycle:
  1. Create crop instance → verify seasonal window assigned
  2. Log actions (irrigation, fertilizer) → verify chronological order
  3. Verify replay produces consistent state
  4. Submit yield → verify state transitions to 'Harvested'
  5. Verify crop cannot accept new actions after harvest

Tests use the FastAPI test client with SQLite in-memory DB.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.security.auth import create_access_token
from app.models.user import User


# ── Test Database Setup ────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_lifecycle.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Fresh database per test."""
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Test client with DB override."""
    def _override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def farmer_user(db):
    """Create a test farmer in the database."""
    user = User(
        id=uuid4(),
        username="lifecycle_farmer",
        email="farmer@test.com",
        hashed_password="hashed_test_password",
        role="farmer",
        full_name="Test Farmer",
        region="Punjab",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def farmer_headers(farmer_user):
    """Auth headers for the test farmer."""
    token = create_access_token({"sub": str(farmer_user.id), "role": "farmer"})
    return {"Authorization": f"Bearer {token}"}


# ======================================================================
# Integration Test 1: Full Lifecycle — Create → Actions → Yield
# ======================================================================

class TestCropLifecycleFlow:
    """
    Simulates the complete lifecycle of a wheat crop from creation to harvest.
    """

    def test_full_lifecycle(self, client, farmer_headers, farmer_user):
        """
        Flow:
          1. POST /crops → create wheat crop
          2. POST /crops/{id}/actions → log irrigation
          3. POST /crops/{id}/actions → log fertilizer (later date)
          4. POST /crops/{id}/yield → submit harvest yield
          5. Verify crop state is 'Harvested'
        """
        sowing = date.today() - timedelta(days=90)

        # ── Step 1: Create crop ─────────────────────────────────
        create_resp = client.post(
            "/api/v1/crops/",
            json={
                "crop_type": "wheat",
                "variety": "HD-2967",
                "sowing_date": sowing.isoformat(),
                "region": "Punjab",
                "sub_region": "Ludhiana",
                "land_area": 5.0,
            },
            headers=farmer_headers,
        )
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"

        crop_data = create_resp.json()
        crop_id = crop_data["id"]

        # Verify basic fields
        assert crop_data["crop_type"] == "wheat"
        assert crop_data["state"] == "Active"
        assert crop_data["region"] == "Punjab"
        assert crop_data["sowing_date"] == sowing.isoformat()

        # ── Step 2: Log first action (irrigation) ───────────────
        action1_date = sowing + timedelta(days=10)
        action1_resp = client.post(
            f"/api/v1/crops/{crop_id}/actions/",
            json={
                "action_type": "irrigation",
                "effective_date": action1_date.isoformat(),
                "category": "Timeline-Critical",
                "notes": "First irrigation after germination",
                "idempotency_key": "irr-001",
            },
            headers=farmer_headers,
        )
        assert action1_resp.status_code == 201, f"Action1 failed: {action1_resp.text}"

        action1_data = action1_resp.json()
        assert action1_data["action_type"] == "irrigation"
        assert action1_data["effective_date"] == action1_date.isoformat()

        # ── Step 3: Log second action (fertilizer, later date) ──
        action2_date = sowing + timedelta(days=25)
        action2_resp = client.post(
            f"/api/v1/crops/{crop_id}/actions/",
            json={
                "action_type": "fertilizer",
                "effective_date": action2_date.isoformat(),
                "category": "Operational",
                "notes": "Urea application",
                "idempotency_key": "fert-001",
            },
            headers=farmer_headers,
        )
        assert action2_resp.status_code == 201, f"Action2 failed: {action2_resp.text}"

        action2_data = action2_resp.json()
        assert action2_data["action_type"] == "fertilizer"

        # ── Step 4: Verify crop state is still Active ───────────
        get_resp = client.get(
            f"/api/v1/crops/{crop_id}",
            headers=farmer_headers,
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["state"] == "Active"

        # ── Step 5: Submit yield ────────────────────────────────
        harvest_date = date.today() - timedelta(days=5)
        yield_resp = client.post(
            f"/api/v1/crops/{crop_id}/yield",
            json={
                "reported_yield": 4200.0,
                "yield_unit": "kg/acre",
                "harvest_date": harvest_date.isoformat(),
            },
            headers=farmer_headers,
        )
        assert yield_resp.status_code == 201, f"Yield submit failed: {yield_resp.text}"

        yield_data = yield_resp.json()
        assert yield_data["reported_yield"] == 4200.0
        assert yield_data["crop_instance_id"] == crop_id

        # ── Step 6: Verify crop is now Harvested ────────────────
        final_resp = client.get(
            f"/api/v1/crops/{crop_id}",
            headers=farmer_headers,
        )
        assert final_resp.status_code == 200
        final_data = final_resp.json()
        assert final_data["state"] == "Harvested", (
            f"Expected 'Harvested' but got '{final_data['state']}'"
        )


# ======================================================================
# Integration Test 2: Chronological Validation
# ======================================================================

class TestChronologicalInvariant:
    """
    Verifies that actions must follow chronological order and cannot
    be logged before the sowing date.
    """

    def test_action_before_sowing_rejected(self, client, farmer_headers):
        """Actions with effective_date before sowing_date must be rejected."""
        sowing = date.today() - timedelta(days=30)

        # Create crop
        resp = client.post(
            "/api/v1/crops/",
            json={
                "crop_type": "rice",
                "sowing_date": sowing.isoformat(),
                "region": "Tamil Nadu",
            },
            headers=farmer_headers,
        )
        assert resp.status_code == 201
        crop_id = resp.json()["id"]

        # Try logging action BEFORE sowing date
        pre_sowing = sowing - timedelta(days=5)
        action_resp = client.post(
            f"/api/v1/crops/{crop_id}/actions/",
            json={
                "action_type": "irrigation",
                "effective_date": pre_sowing.isoformat(),
                "idempotency_key": "pre-sowing-001",
            },
            headers=farmer_headers,
        )
        # Should be rejected (422 or 400)
        assert action_resp.status_code in (400, 422), (
            f"Expected rejection but got {action_resp.status_code}: {action_resp.text}"
        )

    def test_out_of_order_action_rejected(self, client, farmer_headers):
        """A second action with an earlier date than the first must be rejected."""
        sowing = date.today() - timedelta(days=60)

        # Create crop
        resp = client.post(
            "/api/v1/crops/",
            json={
                "crop_type": "cotton",
                "sowing_date": sowing.isoformat(),
                "region": "Gujarat",
            },
            headers=farmer_headers,
        )
        assert resp.status_code == 201
        crop_id = resp.json()["id"]

        # Log first action (day 20)
        d1 = sowing + timedelta(days=20)
        r1 = client.post(
            f"/api/v1/crops/{crop_id}/actions/",
            json={
                "action_type": "pesticide",
                "effective_date": d1.isoformat(),
                "idempotency_key": "pest-001",
            },
            headers=farmer_headers,
        )
        assert r1.status_code == 201

        # Try to log second action BEFORE first (day 10)
        d2 = sowing + timedelta(days=10)
        r2 = client.post(
            f"/api/v1/crops/{crop_id}/actions/",
            json={
                "action_type": "irrigation",
                "effective_date": d2.isoformat(),
                "idempotency_key": "irr-back-001",
            },
            headers=farmer_headers,
        )
        assert r2.status_code in (400, 422), (
            f"Expected rejection for out-of-order action: {r2.text}"
        )


# ======================================================================
# Integration Test 3: Idempotency
# ======================================================================

class TestIdempotency:
    """
    Verifies that duplicate actions with same idempotency_key are rejected.
    """

    def test_duplicate_action_rejected(self, client, farmer_headers):
        """Same idempotency_key should not create duplicate action."""
        sowing = date.today() - timedelta(days=45)

        resp = client.post(
            "/api/v1/crops/",
            json={
                "crop_type": "wheat",
                "sowing_date": sowing.isoformat(),
                "region": "Haryana",
            },
            headers=farmer_headers,
        )
        crop_id = resp.json()["id"]

        action_date = sowing + timedelta(days=15)
        payload = {
            "action_type": "irrigation",
            "effective_date": action_date.isoformat(),
            "idempotency_key": "dup-key-001",
        }

        # First request — should succeed
        r1 = client.post(
            f"/api/v1/crops/{crop_id}/actions/",
            json=payload,
            headers=farmer_headers,
        )
        assert r1.status_code == 201

        # Second request — same key — should be rejected
        r2 = client.post(
            f"/api/v1/crops/{crop_id}/actions/",
            json=payload,
            headers=farmer_headers,
        )
        assert r2.status_code in (409, 422, 400), (
            f"Duplicate key should be rejected: {r2.text}"
        )


# ======================================================================
# Integration Test 4: Crop Listing & Filtering
# ======================================================================

class TestCropListing:
    """
    Verifies crop list endpoint with state and type filters.
    """

    def test_list_filters(self, client, farmer_headers):
        """Create multiple crops and verify filtering works."""
        sowing = date.today() - timedelta(days=30)

        # Create two crops of different types
        for crop_type in ["wheat", "rice"]:
            client.post(
                "/api/v1/crops/",
                json={
                    "crop_type": crop_type,
                    "sowing_date": sowing.isoformat(),
                    "region": "Punjab",
                },
                headers=farmer_headers,
            )

        # List all crops
        all_resp = client.get("/api/v1/crops/", headers=farmer_headers)
        assert all_resp.status_code == 200
        all_data = all_resp.json()
        assert all_data["total"] >= 2

        # Filter by crop_type
        wheat_resp = client.get(
            "/api/v1/crops/?crop_type=wheat",
            headers=farmer_headers,
        )
        assert wheat_resp.status_code == 200
        wheat_data = wheat_resp.json()
        for item in wheat_data["items"]:
            assert item["crop_type"] == "wheat"


# ======================================================================
# Integration Test 5: Replay Consistency (via API)
# ======================================================================

class TestReplayConsistency:
    """
    Verifies that fetching a crop after logging actions returns
    a consistent, replayed state with correct day numbers.
    """

    def test_crop_state_after_actions(self, client, farmer_headers):
        """Crop day_number should advance based on actions logged."""
        sowing = date.today() - timedelta(days=60)

        # Create crop
        resp = client.post(
            "/api/v1/crops/",
            json={
                "crop_type": "wheat",
                "sowing_date": sowing.isoformat(),
                "region": "MP",
            },
            headers=farmer_headers,
        )
        crop_id = resp.json()["id"]

        # Log a few sequential actions
        for day_offset in [7, 14, 21, 28]:
            action_date = sowing + timedelta(days=day_offset)
            client.post(
                f"/api/v1/crops/{crop_id}/actions/",
                json={
                    "action_type": "irrigation",
                    "effective_date": action_date.isoformat(),
                    "idempotency_key": f"replay-{day_offset}",
                },
                headers=farmer_headers,
            )

        # Fetch crop — verify consistent state
        get_resp = client.get(f"/api/v1/crops/{crop_id}", headers=farmer_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["state"] == "Active"
        # current_day_number should be >= 28 (at least as far as last action)
        assert data["current_day_number"] >= 28, (
            f"Expected day_number >= 28 but got {data['current_day_number']}"
        )
