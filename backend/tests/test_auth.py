"""
Authentication Module Tests

Tests for user registration, login, and JWT validation.
"""

import pytest
from fastapi.testclient import TestClient


class TestRegistration:
    """Tests for user registration endpoint."""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json={
            "full_name": "Test Farmer",
            "phone": "+919876543210",
            "password": "securepass123",
            "role": "farmer",
            "region": "Punjab",
        })
        assert response.status_code in (200, 201)
        data = response.json()
        assert "access_token" in data or "id" in data

    def test_register_duplicate_phone(self, client: TestClient):
        """Test registration with duplicate phone number fails."""
        user_data = {
            "full_name": "Test Farmer",
            "phone": "+919876543211",
            "password": "securepass123",
            "role": "farmer",
            "region": "Punjab",
        }
        client.post("/api/v1/auth/register", json=user_data)
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code in (400, 409, 422)

    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        response = client.post("/api/v1/auth/register", json={
            "full_name": "Test",
        })
        assert response.status_code == 422


class TestLogin:
    """Tests for login endpoint."""

    def test_login_success(self, client: TestClient):
        """Test successful login."""
        # Register first
        client.post("/api/v1/auth/register", json={
            "full_name": "Login Test",
            "phone": "+919876543212",
            "password": "testpass123",
            "role": "farmer",
            "region": "Punjab",
        })
        # Login
        response = client.post("/api/v1/auth/login", json={
            "phone": "+919876543212",
            "password": "testpass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password."""
        client.post("/api/v1/auth/register", json={
            "full_name": "Login Wrong",
            "phone": "+919876543213",
            "password": "correctpass",
            "role": "farmer",
            "region": "Punjab",
        })
        response = client.post("/api/v1/auth/login", json={
            "phone": "+919876543213",
            "password": "wrongpass",
        })
        assert response.status_code in (400, 401)

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        response = client.post("/api/v1/auth/login", json={
            "phone": "+919999999999",
            "password": "anypass",
        })
        assert response.status_code in (400, 401, 404)


class TestJWT:
    """Tests for JWT validation."""

    def test_protected_route_no_token(self, client: TestClient):
        """Test accessing protected route without JWT fails."""
        response = client.get("/api/v1/crops/")
        assert response.status_code in (401, 403)

    def test_protected_route_invalid_token(self, client: TestClient):
        """Test accessing protected route with invalid JWT fails."""
        response = client.get(
            "/api/v1/crops/",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code in (401, 403)
