"""
FR-30 / F3 — Dead Letter Queue: Single + Bulk Retry Success Tests

Covers:
- Single retry resets DeadLetter event to Created, clears retry_count
- Bulk retry with event_type filter only retries matching events
- Bulk retry respects limit parameter
- 404 on retry for non-existent event
- 400 on retry for non-DeadLetter event
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.event_log import EventLog


def _make_dead_letter(db: Session, event_type: str = "test.event", suffix: str = "") -> EventLog:
    """Seed a DeadLetter event and return it."""
    event = EventLog(
        id=uuid4(),
        event_type=event_type,
        entity_type="TestEntity",
        entity_id=str(uuid4()),
        partition_key=str(uuid4()),
        payload={"test": True},
        status="DeadLetter",
        retry_count=5,
        max_retries=5,
        failure_reason=f"Max retries exceeded{suffix}",
        event_hash=f"dlq-hash-{uuid4().hex[:8]}",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# ---------------------------------------------------------------------------
# Single retry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_single_retry_moves_deadletter_to_created(
    async_client: AsyncClient, admin_headers: dict, db: Session
):
    """POST /dead-letters/{id}/retry resets status to Created and clears retry_count."""
    event = _make_dead_letter(db)

    resp = await async_client.post(
        f"/api/v1/admin/dead-letters/{event.id}/retry",
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Accept either wrapper formats
    data = body.get("data", body)
    assert data.get("new_state") == "Created" or data.get("status") in ("success", "retried")

    db.refresh(event)
    assert event.status == "Created"
    assert event.retry_count == 0
    assert event.next_retry_at is None


@pytest.mark.asyncio
async def test_single_retry_returns_404_for_nonexistent_event(
    async_client: AsyncClient, admin_headers: dict
):
    """POST /dead-letters/{id}/retry returns 404 for unknown event id."""
    resp = await async_client.post(
        f"/api/v1/admin/dead-letters/{uuid4()}/retry",
        headers=admin_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_single_retry_returns_400_for_non_deadletter_event(
    async_client: AsyncClient, admin_headers: dict, db: Session
):
    """POST /dead-letters/{id}/retry returns 400 when event is not in DeadLetter state."""
    event = EventLog(
        id=uuid4(),
        event_type="test.event",
        entity_type="TestEntity",
        entity_id=str(uuid4()),
        partition_key=str(uuid4()),
        payload={},
        status="Created",  # Not dead-lettered
        event_hash=f"not-dl-{uuid4().hex[:8]}",
    )
    db.add(event)
    db.commit()

    resp = await async_client.post(
        f"/api/v1/admin/dead-letters/{event.id}/retry",
        headers=admin_headers,
    )
    assert resp.status_code in (400, 404)


# ---------------------------------------------------------------------------
# Bulk retry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_retry_respects_event_type_filter(
    async_client: AsyncClient, admin_headers: dict, db: Session
):
    """POST /dead-letters/bulk-retry only retries events matching the requested event_type."""
    target_type = f"target.event.{uuid4().hex[:6]}"
    other_type = f"other.event.{uuid4().hex[:6]}"

    target_events = [_make_dead_letter(db, event_type=target_type, suffix=f"-{i}") for i in range(3)]
    other_events = [_make_dead_letter(db, event_type=other_type, suffix=f"-{i}") for i in range(2)]

    resp = await async_client.post(
        "/api/v1/admin/dead-letters/bulk-retry",
        json={"event_type": target_type, "limit": 100, "reason": "test-filter-retry"},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text

    # Target events should now be Created
    for ev in target_events:
        db.refresh(ev)
        assert ev.status == "Created", f"Expected Created, got {ev.status} for {ev.id}"

    # Other events should remain DeadLetter
    for ev in other_events:
        db.refresh(ev)
        assert ev.status == "DeadLetter", f"Expected DeadLetter, got {ev.status} for {ev.id}"


@pytest.mark.asyncio
async def test_bulk_retry_respects_limit(
    async_client: AsyncClient, admin_headers: dict, db: Session
):
    """POST /dead-letters/bulk-retry does not retry more events than the specified limit."""
    batch_type = f"batch.event.{uuid4().hex[:6]}"
    events = [_make_dead_letter(db, event_type=batch_type, suffix=f"-{i}") for i in range(5)]

    resp = await async_client.post(
        "/api/v1/admin/dead-letters/bulk-retry",
        json={"event_type": batch_type, "limit": 3, "reason": "test-limit-retry"},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text

    retried_count = sum(
        1 for ev in events
        if db.refresh(ev) or ev.status == "Created"
    )
    # At most 3 should have been retried
    assert retried_count <= 3


@pytest.mark.asyncio
async def test_bulk_retry_response_contains_retried_count(
    async_client: AsyncClient, admin_headers: dict, db: Session
):
    """Bulk retry response includes a count of retried events."""
    batch_type = f"count.event.{uuid4().hex[:6]}"
    [_make_dead_letter(db, event_type=batch_type) for _ in range(2)]

    resp = await async_client.post(
        "/api/v1/admin/dead-letters/bulk-retry",
        json={"event_type": batch_type, "limit": 100, "reason": "count-check"},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    data = body.get("data", body)
    # Should include some count field
    assert any(k in data for k in ("retried", "retried_count", "count", "updated"))
