"""
Test Configuration

Shared fixtures for all tests: test database, test client, and authentication helpers.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.main import app
from app.database import Base, get_db
from app.security.auth import create_access_token

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


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


@pytest.fixture
def auth_headers():
    """Generate authentication headers for testing."""
    token = create_access_token({"sub": str(uuid4()), "role": "farmer"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    """Generate admin authentication headers."""
    token = create_access_token({"sub": str(uuid4()), "role": "admin"})
    return {"Authorization": f"Bearer {token}"}
