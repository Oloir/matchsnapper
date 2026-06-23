import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REGISTER_URL = "/api/v1/auth/register"


async def _auth(client: AsyncClient, email: str, username: str) -> dict:
    resp = await client.post(REGISTER_URL, json={
        "email": email, "username": username, "password": "password123",
    })
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _me_id(client: AsyncClient, auth: dict) -> str:
    return (await client.get("/api/v1/users/me", headers=auth)).json()["id"]


# ── POST /users/{id}/view ─────────────────────────────────────────────────────

async def test_mark_viewed(client: AsyncClient):
    auth_a = await _auth(client, "view_a@test.com", "view_a_user")
    auth_b = await _auth(client, "view_b@test.com", "view_b_user")
    b_id = await _me_id(client, auth_b)

    resp = await client.post(f"/api/v1/users/{b_id}/view", headers=auth_a)
    assert resp.status_code == 201
    data = resp.json()
    assert data["viewed_id"] == b_id
    assert data["is_viewed"] is True


async def test_mark_viewed_idempotent(client: AsyncClient):
    auth_a = await _auth(client, "view_idem_a@test.com", "view_idem_a")
    auth_b = await _auth(client, "view_idem_b@test.com", "view_idem_b")
    b_id = await _me_id(client, auth_b)

    await client.post(f"/api/v1/users/{b_id}/view", headers=auth_a)
    resp = await client.post(f"/api/v1/users/{b_id}/view", headers=auth_a)
    assert resp.status_code == 201  # ON CONFLICT DO NOTHING — idempotent


async def test_mark_viewed_self_rejected(client: AsyncClient):
    auth = await _auth(client, "view_self@test.com", "view_self_user")
    my_id = await _me_id(client, auth)
    resp = await client.post(f"/api/v1/users/{my_id}/view", headers=auth)
    assert resp.status_code == 400


async def test_mark_viewed_reflected_in_matching(client: AsyncClient):
    auth_a = await _auth(client, "view_match_a@test.com", "view_match_a")
    auth_b = await _auth(client, "view_match_b@test.com", "view_match_b")
    b_id = await _me_id(client, auth_b)

    await client.post(f"/api/v1/users/{b_id}/view", headers=auth_a)
    resp = await client.get("/api/v1/matching", headers=auth_a)
    b_result = next((r for r in resp.json()["results"] if r["user"]["id"] == b_id), None)
    assert b_result is not None
    assert b_result["is_viewed"] is True


# ── DELETE /users/{id}/view ───────────────────────────────────────────────────

async def test_unmark_viewed(client: AsyncClient):
    auth_a = await _auth(client, "unview_a@test.com", "unview_a_user")
    auth_b = await _auth(client, "unview_b@test.com", "unview_b_user")
    b_id = await _me_id(client, auth_b)

    await client.post(f"/api/v1/users/{b_id}/view", headers=auth_a)
    resp = await client.delete(f"/api/v1/users/{b_id}/view", headers=auth_a)
    assert resp.status_code == 204

    match = await client.get("/api/v1/matching", headers=auth_a)
    b_result = next((r for r in match.json()["results"] if r["user"]["id"] == b_id), None)
    if b_result:
        assert b_result["is_viewed"] is False


async def test_unmark_viewed_nonexistent_is_ok(client: AsyncClient):
    auth_a = await _auth(client, "unview_ne_a@test.com", "unview_ne_a")
    auth_b = await _auth(client, "unview_ne_b@test.com", "unview_ne_b")
    b_id = await _me_id(client, auth_b)

    resp = await client.delete(f"/api/v1/users/{b_id}/view", headers=auth_a)
    assert resp.status_code == 204  # idempotent delete


# ── POST /users/{id}/contact ──────────────────────────────────────────────────

async def test_send_contact(client: AsyncClient):
    auth_a = await _auth(client, "contact_a@test.com", "contact_a_user")
    auth_b = await _auth(client, "contact_b@test.com", "contact_b_user")
    b_id = await _me_id(client, auth_b)

    resp = await client.post(f"/api/v1/users/{b_id}/contact", headers=auth_a)
    assert resp.status_code == 201
    data = resp.json()
    assert data["to_user_id"] == b_id
    assert data["status"] == "pending"


async def test_send_contact_duplicate(client: AsyncClient):
    auth_a = await _auth(client, "contact_dup_a@test.com", "contact_dup_a")
    auth_b = await _auth(client, "contact_dup_b@test.com", "contact_dup_b")
    b_id = await _me_id(client, auth_b)

    await client.post(f"/api/v1/users/{b_id}/contact", headers=auth_a)
    resp = await client.post(f"/api/v1/users/{b_id}/contact", headers=auth_a)
    assert resp.status_code == 409


async def test_send_contact_self_rejected(client: AsyncClient):
    auth = await _auth(client, "contact_self@test.com", "contact_self_user")
    my_id = await _me_id(client, auth)
    resp = await client.post(f"/api/v1/users/{my_id}/contact", headers=auth)
    assert resp.status_code == 400


async def test_send_contact_unknown_user(client: AsyncClient):
    auth = await _auth(client, "contact_unk@test.com", "contact_unk_user")
    resp = await client.post("/api/v1/users/00000000-0000-0000-0000-000000000000/contact", headers=auth)
    assert resp.status_code == 404
