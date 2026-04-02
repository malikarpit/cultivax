import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.orm import Session

@pytest.mark.asyncio
async def test_discard_dead_letter_not_found(async_client: AsyncClient, admin_headers: dict):
    """DELETE /dead-letters/{id} returns 404 if not found."""
    response = await async_client.delete(
        f"/api/v1/admin/dead-letters/{uuid4()}",
        headers=admin_headers
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_discard_dead_letter_wrong_state(async_client: AsyncClient, admin_headers: dict, db: Session):
    """DELETE /dead-letters/{id} returns 400 if state is not DeadLetter."""
    from app.models.event_log import EventLog
    event = EventLog(
        id=uuid4(),
        event_type="test",
        entity_type="test",
        entity_id=str(uuid4()),
        partition_key=str(uuid4()),
        payload={"a": 1},
        status="Created",
        event_hash="fakehash1"
    )
    db.add(event)
    db.commit()

    response = await async_client.delete(
        f"/api/v1/admin/dead-letters/{event.id}",
        headers=admin_headers
    )
    assert response.status_code == 400
    assert "state" in str(response.json())

@pytest.mark.asyncio
async def test_discard_dead_letter_success(async_client: AsyncClient, admin_headers: dict, db: Session):
    """DELETE /dead-letters/{id} successfully soft deletes it."""
    from app.models.event_log import EventLog
    event = EventLog(
        id=uuid4(),
        event_type="test",
        entity_type="test",
        entity_id=str(uuid4()),
        partition_key=str(uuid4()),
        payload={"a": 1},
        status="DeadLetter",
        failure_reason="Max retries exceeded",
        event_hash="fakehash2"
    )
    db.add(event)
    db.commit()

    response = await async_client.delete(
        f"/api/v1/admin/dead-letters/{event.id}",
        headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json().get("data", {}).get("status") == "success" or response.json().get("status") == "success"
    
    db.refresh(event)
    assert event.is_deleted is True
    assert "Discarded by admin" in event.failure_reason
