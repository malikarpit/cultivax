from uuid import uuid4

from tests.conftest import unwrap


def test_api_v1_health_alias(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = unwrap(resp)
    assert "status" in data


def test_operations_endpoint_requires_auth(client):
    resp = client.get(f"/api/v1/operations/{uuid4()}")
    assert resp.status_code in (401, 403)


def test_service_request_complete_post_alias_requires_provider(client, auth_headers):
    resp = client.post(
        f"/api/v1/service-requests/{uuid4()}/complete",
        headers=auth_headers,
    )
    assert resp.status_code in (403, 404)


def test_media_request_upload_endpoint_exists(client, auth_headers):
    resp = client.post(
        "/api/v1/media/request-upload",
        headers=auth_headers,
        json={"crop_instance_id": str(uuid4()), "file_type": "image"},
    )
    assert resp.status_code in (400, 404)


def test_media_confirm_upload_endpoint_exists(client, auth_headers):
    resp = client.post(
        "/api/v1/media/confirm-upload",
        headers=auth_headers,
        json={"media_id": str(uuid4())},
    )
    assert resp.status_code == 404
