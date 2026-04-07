"""
Test Configuration — PostgreSQL-Backed

Uses a dedicated PostgreSQL test database for realistic testing that matches
the production environment. All tables are created fresh per session and
cleaned between tests via DELETE for isolation.

Design choice: PostgreSQL (not SQLite) avoids:
- JSONB/UUID type compilation hacks
- Startup event errors from dual-engine mismatch
- Behavioural differences between SQLite and PostgreSQL
"""

import os
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

# Override DATABASE_URL BEFORE importing app (so startup events use test DB)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://cultivax_user:cultivax_pass@localhost:5432/cultivax_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["TESTING"] = "1"  # Disable rate limiting & other test-unfriendly middleware

from app.main import app
from app.database import Base, get_db, engine as app_engine
from app.config import settings as app_settings
from app.security.auth import create_access_token
from app.models.user import User

# Ensure all new models are registered in Base.metadata before create_all()
from app.models.official_scheme import OfficialScheme  # noqa: F401
from app.models.scheme_redirect_log import SchemeRedirectLog  # noqa: F401
from app.models.dispute_case import DisputeCase  # noqa: F401
from app.models.sms_delivery_log import SmsDeliveryLog  # noqa: F401
from app.models.ml_inference_audit import MLInferenceAudit  # noqa: F401
from app.models.user_consent import UserConsent  # noqa: F401

# Create test engine using the same URL the app now uses
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ── Helper: Response Envelope Unwrapper ────────────────────────────

def unwrap(response):
    """
    Unwrap the API response envelope.
    
    Our API uses {success, data, meta} envelope. Tests should call:
        data = unwrap(resp)  
    to get the raw payload, regardless of whether the response is enveloped.
    
    For error responses, returns the full envelope (with 'success', 'error', 'details').
    """
    body = response.json()
    if isinstance(body, dict):
        # Already enveloped with 'data' key
        if "data" in body and "success" in body:
            return body["data"]
        # Error envelope
        if "success" in body and not body.get("success", True):
            return body
    return body


# ── Database Fixtures ──────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables once at the start of the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db(setup_test_database):
    """
    Provide a database session for each test.
    Uses DELETE for cleanup after each test.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up all tables between tests for isolation
        cleanup = TestingSessionLocal()
        try:
            for table in reversed(Base.metadata.sorted_tables):
                cleanup.execute(table.delete())
            cleanup.commit()
        finally:
            cleanup.close()


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── User Factory ───────────────────────────────────────────────────

def _create_test_user(db, role="farmer", suffix=None):
    """Create a real user in the test database and return it."""
    suffix = suffix or uuid4().hex[:8]
    user = User(
        id=uuid4(),
        email=f"{role}_{suffix}@test.com",
        phone=f"+91{uuid4().int % 10**10:010d}",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$test_hash",
        role=role,
        full_name=f"Test {role.title()}",
        region="Punjab",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Auth Fixtures (all backed by real DB users) ────────────────────

@pytest.fixture
def farmer_user(db):
    """Create a real farmer user in the database."""
    return _create_test_user(db, "farmer")


@pytest.fixture
def admin_user(db):
    """Create a real admin user in the database."""
    return _create_test_user(db, "admin")


@pytest.fixture
def provider_user(db):
    """Create a real provider user in the database."""
    return _create_test_user(db, "provider")


@pytest.fixture
def auth_headers(farmer_user):
    """Auth headers for a real farmer user in the database."""
    token = create_access_token({"sub": str(farmer_user.id), "role": "farmer"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user):
    """Auth headers for a real admin user in the database."""
    token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def provider_headers(provider_user):
    """Auth headers for a real service provider user in the database."""
    token = create_access_token({"sub": str(provider_user.id), "role": "provider"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def farmer_user_id(farmer_user):
    """Return the farmer user ID for tests that need to track user identity."""
    return str(farmer_user.id)


@pytest.fixture
def auth_headers_with_id(farmer_user):
    """Auth headers with a known user ID for ownership testing."""
    token = create_access_token({"sub": str(farmer_user.id), "role": "farmer"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def farmer_token(farmer_user):
    """Generate a JWT token string for the test farmer user."""
    return create_access_token({"sub": str(farmer_user.id), "role": "farmer"})


# ── App Settings ───────────────────────────────────────────────────

@pytest.fixture
def settings():
    """Provide app settings for tests that need configuration access."""
    return app_settings


# ── Async Fixtures ─────────────────────────────────────────────────

@pytest_asyncio.fixture
async def async_client(db):
    """Async HTTP client for tests using httpx.AsyncClient."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
