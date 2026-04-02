"""
Feature 8 tests: land parcels and crop linkage.
"""

from datetime import date
from uuid import uuid4

from app.models.user import User
from app.security.auth import create_access_token
from tests.conftest import unwrap


def _create_user(db, role: str = 'farmer') -> User:
    user = User(
        id=uuid4(),
        full_name=f'Test {role.title()}',
        phone=f'+91{uuid4().int % 10**10:010d}',
        email=f'{role}-{uuid4().hex[:8]}@test.com',
        password_hash='hashed_test_password',
        role=role,
        region='Punjab',
        preferred_language='en',
        accessibility_settings={},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers_for(user: User) -> dict:
    token = create_access_token({'sub': str(user.id), 'role': user.role})
    return {'Authorization': f'Bearer {token}'}


def test_land_parcel_create_and_list(client, db):
    farmer = _create_user(db, role='farmer')
    headers = _headers_for(farmer)

    create_resp = client.post(
        '/api/v1/land-parcels/',
        json={
            'parcel_name': 'North Plot',
            'region': 'Punjab',
            'sub_region': 'Ludhiana',
            'land_area': 2.5,
            'land_area_unit': 'acres',
            'soil_type': {'primary': 'alluvial', 'ph': 6.8, 'organic_matter': 'medium'},
            'gps_coordinates': {
                'lat': 30.9000,
                'lng': 75.8573,
                'boundary_polygon': [
                    [30.9000, 75.8573],
                    [30.9007, 75.8573],
                    [30.9007, 75.8580],
                    [30.9000, 75.8580],
                ],
            },
            'irrigation_source': 'canal',
        },
        headers=headers,
    )

    assert create_resp.status_code == 201, create_resp.text
    created = unwrap(create_resp)
    assert created['parcel_name'] == 'North Plot'
    assert created['farmer_id'] == str(farmer.id)

    list_resp = client.get('/api/v1/land-parcels/', headers=headers)
    assert list_resp.status_code == 200, list_resp.text
    items = unwrap(list_resp)
    assert len(items) == 1
    assert items[0]['id'] == created['id']


def test_land_parcel_endpoint_blocks_provider_role(client, db):
    provider = _create_user(db, role='provider')
    headers = _headers_for(provider)

    resp = client.get('/api/v1/land-parcels/', headers=headers)
    assert resp.status_code == 403


def test_crop_create_persists_land_parcel_id(client, db):
    farmer = _create_user(db, role='farmer')
    headers = _headers_for(farmer)

    parcel_resp = client.post(
        '/api/v1/land-parcels/',
        json={
            'parcel_name': 'Linked Plot',
            'region': 'Punjab',
            'land_area': 3.0,
            'land_area_unit': 'acres',
            'gps_coordinates': {'lat': 30.9, 'lng': 75.85},
            'irrigation_source': 'drip',
        },
        headers=headers,
    )
    assert parcel_resp.status_code == 201, parcel_resp.text
    parcel_id = unwrap(parcel_resp)['id']

    crop_resp = client.post(
        '/api/v1/crops/',
        json={
            'crop_type': 'wheat',
            'variety': 'HD-2967',
            'sowing_date': date.today().isoformat(),
            'region': 'Punjab',
            'land_area': 3.0,
            'land_parcel_id': parcel_id,
        },
        headers=headers,
    )
    assert crop_resp.status_code == 201, crop_resp.text
    crop = unwrap(crop_resp)
    assert crop['land_parcel_id'] == parcel_id

    get_resp = client.get(f"/api/v1/crops/{crop['id']}", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    loaded = unwrap(get_resp)
    assert loaded['land_parcel_id'] == parcel_id


def test_land_parcel_restore_flow(client, db):
    farmer = _create_user(db, role='farmer')
    headers = _headers_for(farmer)

    create_resp = client.post(
        '/api/v1/land-parcels/',
        json={
            'parcel_name': 'Restore Plot',
            'region': 'Punjab',
            'land_area': 1.2,
            'land_area_unit': 'acres',
            'gps_coordinates': {'lat': 30.9, 'lng': 75.85},
            'irrigation_source': 'drip',
        },
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    parcel_id = unwrap(create_resp)['id']

    delete_resp = client.delete(f'/api/v1/land-parcels/{parcel_id}', headers=headers)
    assert delete_resp.status_code == 204, delete_resp.text

    list_resp = client.get('/api/v1/land-parcels/', headers=headers)
    assert list_resp.status_code == 200, list_resp.text
    assert all(item['id'] != parcel_id for item in unwrap(list_resp))

    list_deleted_resp = client.get('/api/v1/land-parcels/?include_deleted=true', headers=headers)
    assert list_deleted_resp.status_code == 200, list_deleted_resp.text
    deleted_items = unwrap(list_deleted_resp)
    matching_deleted = [item for item in deleted_items if item['id'] == parcel_id]
    assert len(matching_deleted) == 1
    assert matching_deleted[0]['is_deleted'] is True

    restore_resp = client.post(f'/api/v1/land-parcels/{parcel_id}/restore', headers=headers)
    assert restore_resp.status_code == 204, restore_resp.text

    list_after_restore = client.get('/api/v1/land-parcels/', headers=headers)
    assert list_after_restore.status_code == 200, list_after_restore.text
    assert any(item['id'] == parcel_id for item in unwrap(list_after_restore))

    list_with_deleted_after_restore = client.get('/api/v1/land-parcels/?include_deleted=true', headers=headers)
    assert list_with_deleted_after_restore.status_code == 200, list_with_deleted_after_restore.text
    matching_restored = [
        item for item in unwrap(list_with_deleted_after_restore) if item['id'] == parcel_id
    ]
    assert len(matching_restored) == 1
    assert matching_restored[0]['is_deleted'] is False


def test_crop_create_rejects_other_farmers_parcel_id(client, db):
    farmer_a = _create_user(db, role='farmer')
    farmer_b = _create_user(db, role='farmer')
    headers_a = _headers_for(farmer_a)
    headers_b = _headers_for(farmer_b)

    parcel_resp = client.post(
        '/api/v1/land-parcels/',
        json={
            'parcel_name': 'Farmer B Parcel',
            'region': 'Punjab',
            'land_area': 2.1,
            'land_area_unit': 'acres',
            'gps_coordinates': {'lat': 30.9, 'lng': 75.85},
            'irrigation_source': 'canal',
        },
        headers=headers_b,
    )
    assert parcel_resp.status_code == 201, parcel_resp.text
    other_parcel_id = unwrap(parcel_resp)['id']

    crop_resp = client.post(
        '/api/v1/crops/',
        json={
            'crop_type': 'wheat',
            'variety': 'HD-2967',
            'sowing_date': date.today().isoformat(),
            'region': 'Punjab',
            'land_area': 1.8,
            'land_parcel_id': other_parcel_id,
        },
        headers=headers_a,
    )
    assert crop_resp.status_code == 400
    body = crop_resp.json()
    error_msg = body.get('error', body.get('detail', ''))
    assert 'Invalid land_parcel_id' in error_msg or 'land_parcel_id' in str(body)
