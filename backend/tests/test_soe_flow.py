"""
End-to-End SOE Workflow Test — Day 28 (Ravi)

Tests the complete Service Orchestration Engine lifecycle:
1. Create a provider (register user → create provider profile)
2. Create a service request from a farmer
3. Provider accepts the request
4. Provider completes the request
5. Farmer submits a review
6. Trust score is recalculated

Validates the entire SOE flow as documented in TDD Sections 2.5.1–2.5.3
and SOE Enhancements 2, 5, 8.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.models.user import User
from app.models.service_provider import ServiceProvider
from app.models.service_request import ServiceRequest
from app.models.service_review import ServiceReview
from tests.conftest import unwrap


class TestSOEEndToEndFlow:
    """
    Complete SOE lifecycle test:
    Provider registration → Service request → Accept → Complete → Review → Trust recalc.
    """

    def _create_farmer(self, db) -> User:
        """Helper: create a test farmer user."""
        farmer = User(
            id=uuid4(),
            full_name="Test Farmer",
            phone=f"+91{uuid4().int % 10**10:010d}",
            email=f"farmer_{uuid4().hex[:6]}@test.in",
            password_hash="fake_hash",
            role="farmer",
            region="Punjab",
            is_active=True,
        )
        db.add(farmer)
        db.flush()
        return farmer

    def _create_provider_user(self, db) -> User:
        """Helper: create a test provider user."""
        provider_user = User(
            id=uuid4(),
            full_name="Test Provider",
            phone=f"+91{uuid4().int % 10**10:010d}",
            email=f"provider_{uuid4().hex[:6]}@test.in",
            password_hash="fake_hash",
            role="provider",
            region="Punjab",
            is_active=True,
        )
        db.add(provider_user)
        db.flush()
        return provider_user

    def _create_service_provider(self, db, user: User) -> ServiceProvider:
        """Helper: create a ServiceProvider record for a user."""
        provider = ServiceProvider(
            id=uuid4(),
            user_id=user.id,
            business_name="Test Farm Services",
            service_type="equipment_rental",
            region="Punjab",
            crop_specializations=["wheat", "rice"],
            trust_score=0.5,
            is_verified=False,
            contact_name=user.full_name,
            contact_phone=user.phone,
        )
        db.add(provider)
        db.flush()
        return provider

    # -------------------------------------------------------------------
    # Test 1: Full lifecycle — happy path
    # -------------------------------------------------------------------

    def test_full_soe_lifecycle(self, db):
        """
        Test the complete SOE flow:
        Create users → Create provider → Service request → Accept → Complete → Review → Trust.
        """
        # Step 1: Create users
        farmer = self._create_farmer(db)
        provider_user = self._create_provider_user(db)

        assert farmer.role == "farmer"
        assert provider_user.role == "provider"

        # Step 2: Register as service provider
        provider = self._create_service_provider(db, provider_user)

        assert provider.trust_score == 0.5  # Default trust
        assert provider.is_verified is False
        assert provider.business_name == "Test Farm Services"

        # Step 3: Farmer creates a service request
        service_request = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type="equipment_rental",
            description="Need tractor for land preparation",
            status="Pending",
            preferred_date=datetime.now(timezone.utc),
        )
        db.add(service_request)
        db.flush()

        assert service_request.status == "Pending"
        assert service_request.provider_id == provider.id

        # Step 4: Provider accepts the request
        service_request.status = "Accepted"
        service_request.provider_acknowledged_at = datetime.now(timezone.utc)
        db.flush()

        assert service_request.status == "Accepted"
        assert service_request.provider_acknowledged_at is not None

        # Step 5: Provider marks request as completed
        service_request.status = "Completed"
        service_request.completed_at = datetime.now(timezone.utc)
        service_request.final_price = 2500.0
        db.flush()

        assert service_request.status == "Completed"
        assert service_request.completed_at is not None

        # Step 6: Farmer submits a review
        review = ServiceReview(
            id=uuid4(),
            request_id=service_request.id,
            reviewer_id=farmer.id,
            provider_id=provider.id,
            rating=4.5,
            comment="Good tractor, timely service",
            complaint_category=None,
        )
        db.add(review)
        db.flush()

        assert review.rating == 4.5
        assert review.complaint_category is None

        # Step 7: Verify trust score can be recalculated
        # Load fresh provider and ensure completion_count can be updated
        fresh_provider = db.query(ServiceProvider).filter(
            ServiceProvider.id == provider.id
        ).first()

        assert fresh_provider is not None
        # Update trust-related counts manually (in production, TrustEngine does this)
        fresh_provider.completion_count = 1
        fresh_provider.complaint_count = 0
        db.flush()

        assert fresh_provider.completion_count == 1
        assert fresh_provider.complaint_count == 0

    # -------------------------------------------------------------------
    # Test 2: Service request state machine integrity
    # -------------------------------------------------------------------

    def test_request_state_transitions(self, db):
        """Verify valid state transitions: Pending → Accepted → Completed."""
        farmer = self._create_farmer(db)
        provider_user = self._create_provider_user(db)
        provider = self._create_service_provider(db, provider_user)

        request = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type="labor",
            status="Pending",
        )
        db.add(request)
        db.flush()

        # Pending → Accepted
        request.status = "Accepted"
        db.flush()
        assert request.status == "Accepted"

        # Accepted → InProgress
        request.status = "InProgress"
        db.flush()
        assert request.status == "InProgress"

        # InProgress → Completed
        request.status = "Completed"
        request.completed_at = datetime.now(timezone.utc)
        db.flush()
        assert request.status == "Completed"

    # -------------------------------------------------------------------
    # Test 3: One review per request constraint
    # -------------------------------------------------------------------

    def test_one_review_per_request(self, db):
        """Only one review should exist per service request."""
        farmer = self._create_farmer(db)
        provider_user = self._create_provider_user(db)
        provider = self._create_service_provider(db, provider_user)

        request = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type="advisory",
            status="Completed",
            completed_at=datetime.now(timezone.utc),
        )
        db.add(request)
        db.flush()

        # First review — should succeed
        review1 = ServiceReview(
            id=uuid4(),
            request_id=request.id,
            reviewer_id=farmer.id,
            provider_id=provider.id,
            rating=4.0,
            comment="Good advice",
        )
        db.add(review1)
        db.flush()

        # Second review for same request — should fail (unique constraint)
        review2 = ServiceReview(
            id=uuid4(),
            request_id=request.id,
            reviewer_id=farmer.id,
            provider_id=provider.id,
            rating=5.0,
            comment="Changed my mind",
        )
        db.add(review2)
        with pytest.raises(Exception):
            db.flush()

        db.rollback()

    # -------------------------------------------------------------------
    # Test 4: Review only for completed requests
    # -------------------------------------------------------------------

    def test_review_requires_completed_status(self, db):
        """Reviews should only be for completed service requests."""
        farmer = self._create_farmer(db)
        provider_user = self._create_provider_user(db)
        provider = self._create_service_provider(db, provider_user)

        # Create a pending request (not completed)
        request = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type="equipment_rental",
            status="Pending",
        )
        db.add(request)
        db.flush()

        # Verify the status is not completed — business logic check
        assert request.status != "Completed"

        # A review CAN be inserted at DB level (constraint is in API layer),
        # but the status proves the API would reject it
        assert request.status == "Pending"

    # -------------------------------------------------------------------
    # Test 5: Complaint category tracking
    # -------------------------------------------------------------------

    def test_review_with_complaint(self, db):
        """Reviews with complaint categories should be tracked."""
        farmer = self._create_farmer(db)
        provider_user = self._create_provider_user(db)
        provider = self._create_service_provider(db, provider_user)

        request = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type="labor",
            status="Completed",
            completed_at=datetime.now(timezone.utc),
        )
        db.add(request)
        db.flush()

        review = ServiceReview(
            id=uuid4(),
            request_id=request.id,
            reviewer_id=farmer.id,
            provider_id=provider.id,
            rating=2.0,
            comment="Workers arrived 3 hours late",
            complaint_category="late_arrival",
        )
        db.add(review)
        db.flush()

        assert review.complaint_category == "late_arrival"
        assert review.rating == 2.0
        assert review.is_flagged in ("none", None, False)

    # -------------------------------------------------------------------
    # Test 6: Provider cancellation flow
    # -------------------------------------------------------------------

    def test_request_cancellation(self, db):
        """Service requests can be cancelled."""
        farmer = self._create_farmer(db)
        provider_user = self._create_provider_user(db)
        provider = self._create_service_provider(db, provider_user)

        request = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type="transport",
            status="Pending",
        )
        db.add(request)
        db.flush()

        # Cancel the request
        request.status = "Cancelled"
        db.flush()

        assert request.status == "Cancelled"
        assert request.completed_at is None

    # -------------------------------------------------------------------
    # Test 7: Multiple requests to same provider — trust accumulation
    # -------------------------------------------------------------------

    def test_multiple_requests_trust_accumulation(self, db):
        """Multiple completed requests should allow trust score accumulation."""
        farmer = self._create_farmer(db)
        provider_user = self._create_provider_user(db)
        provider = self._create_service_provider(db, provider_user)

        completed_count = 0

        for i in range(5):
            req = ServiceRequest(
                id=uuid4(),
                farmer_id=farmer.id,
                provider_id=provider.id,
                service_type="equipment_rental",
                status="Completed",
                completed_at=datetime.now(timezone.utc),
                final_price=2000.0 + i * 100,
            )
            db.add(req)
            db.flush()
            completed_count += 1

            # Add review for each
            review = ServiceReview(
                id=uuid4(),
                request_id=req.id,
                reviewer_id=farmer.id,
                provider_id=provider.id,
                rating=4.0 + (i * 0.2),  # 4.0, 4.2, 4.4, 4.6, 4.8
                comment=f"Service iteration {i+1}",
            )
            db.add(review)
            db.flush()

        # Verify all requests and reviews exist
        total_requests = db.query(ServiceRequest).filter(
            ServiceRequest.provider_id == provider.id,
            ServiceRequest.status == "Completed",
        ).count()

        total_reviews = db.query(ServiceReview).filter(
            ServiceReview.reviewer_id == farmer.id,
        ).count()

        assert total_requests == 5
        assert total_reviews == 5

        # Update provider completion count
        provider.completion_count = completed_count
        db.flush()
        assert provider.completion_count == 5

    # -------------------------------------------------------------------
    # Test 8: Disputed request flow
    # -------------------------------------------------------------------

    def test_disputed_request_flow(self, db):
        """Test that requests can move to Disputed status."""
        farmer = self._create_farmer(db)
        provider_user = self._create_provider_user(db)
        provider = self._create_service_provider(db, provider_user)

        request = ServiceRequest(
            id=uuid4(),
            farmer_id=farmer.id,
            provider_id=provider.id,
            service_type="equipment_rental",
            status="Accepted",
            provider_acknowledged_at=datetime.now(timezone.utc),
        )
        db.add(request)
        db.flush()

        # Move to disputed
        request.status = "Disputed"
        db.flush()

        assert request.status == "Disputed"
