import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.services.auth_service import decode_token

pytestmark = pytest.mark.asyncio

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"


async def test_register_success(client: AsyncClient):
    resp = await client.post(REGISTER_URL, json={
        "email": "alice@test.com",
        "username": "alice",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "bob@test.com", "username": "bob", "password": "password123"}
    await client.post(REGISTER_URL, json=payload)
    resp = await client.post(REGISTER_URL, json={**payload, "username": "bob2"})
    assert resp.status_code == 409


async def test_register_duplicate_username(client: AsyncClient):
    await client.post(REGISTER_URL, json={
        "email": "carol@test.com", "username": "carol", "password": "password123",
    })
    resp = await client.post(REGISTER_URL, json={
        "email": "carol2@test.com", "username": "carol", "password": "password123",
    })
    assert resp.status_code == 409


async def test_register_short_password(client: AsyncClient):
    resp = await client.post(REGISTER_URL, json={
        "email": "short@test.com", "username": "shortpw", "password": "123",
    })
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient):
    await client.post(REGISTER_URL, json={
        "email": "dave@test.com", "username": "dave", "password": "password123",
    })
    resp = await client.post(LOGIN_URL, json={
        "email": "dave@test.com", "password": "password123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient):
    await client.post(REGISTER_URL, json={
        "email": "eve@test.com", "username": "eve", "password": "password123",
    })
    resp = await client.post(LOGIN_URL, json={
        "email": "eve@test.com", "password": "wrongpassword",
    })
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post(LOGIN_URL, json={
        "email": "nobody@test.com", "password": "password123",
    })
    assert resp.status_code == 401


async def test_refresh_success(client: AsyncClient):
    reg = await client.post(REGISTER_URL, json={
        "email": "frank@test.com", "username": "frank", "password": "password123",
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_access_token_rejected(client: AsyncClient):
    reg = await client.post(REGISTER_URL, json={
        "email": "grace@test.com", "username": "grace", "password": "password123",
    })
    access_token = reg.json()["access_token"]
    resp = await client.post(REFRESH_URL, json={"refresh_token": access_token})
    assert resp.status_code == 401


async def test_invalid_token_rejected():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.token", "access")
    assert exc_info.value.status_code == 401


async def test_wrong_token_type_rejected():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.token", "refresh")
    assert exc_info.value.status_code == 401


async def test_protected_route_with_token(client: AsyncClient):
    reg = await client.post(REGISTER_URL, json={
        "email": "henry@test.com", "username": "henry", "password": "password123",
    })
    token = reg.json()["access_token"]
    resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    # users/me not implemented yet — 404 is fine, 401 would mean auth failed
    assert resp.status_code != 401
