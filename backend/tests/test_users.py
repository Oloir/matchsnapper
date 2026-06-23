import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from PIL import Image

from app.services.storage_service import storage_service

pytestmark = pytest.mark.asyncio

REGISTER_URL = "/api/v1/auth/register"
ME_URL = "/api/v1/users/me"
AVATAR_URL = "/api/v1/users/me/avatar"

FAKE_AVATAR_URL = "http://localhost:9000/matchsnapper/avatars/test.jpg"


def _make_jpeg(size: tuple[int, int] = (200, 200)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color=(100, 150, 200)).save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


async def _register(client: AsyncClient, email: str, username: str) -> dict:
    resp = await client.post(REGISTER_URL, json={
        "email": email, "username": username, "password": "password123",
    })
    assert resp.status_code == 201
    return resp.json()


# ── GET /users/me ─────────────────────────────────────────────────────────────

async def test_get_me(client: AsyncClient):
    tokens = await _register(client, "getme@test.com", "getme_user")
    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "getme@test.com"
    assert data["username"] == "getme_user"
    assert data["is_active"] is True


async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get(ME_URL)
    assert resp.status_code in (401, 403)


# ── PATCH /users/me ───────────────────────────────────────────────────────────

async def test_patch_bio(client: AsyncClient):
    tokens = await _register(client, "bio@test.com", "bio_user")
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.patch(ME_URL, json={"bio": "Hello from tests!"}, headers=auth)
    assert resp.status_code == 200
    assert resp.json()["bio"] == "Hello from tests!"


async def test_patch_bio_to_null(client: AsyncClient):
    tokens = await _register(client, "bionull@test.com", "bionull_user")
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.patch(ME_URL, json={"bio": "Initial bio"}, headers=auth)
    resp = await client.patch(ME_URL, json={"bio": None}, headers=auth)
    assert resp.status_code == 200
    assert resp.json()["bio"] is None


# ── GET /users/{id} ───────────────────────────────────────────────────────────

async def test_get_public_profile(client: AsyncClient):
    tokens = await _register(client, "pub@test.com", "pub_user")
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    user_id = (await client.get(ME_URL, headers=auth)).json()["id"]

    resp = await client.get(f"/api/v1/users/{user_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "pub_user"
    assert "email" not in data
    assert "hashed_password" not in data


async def test_get_nonexistent_user(client: AsyncClient):
    resp = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ── POST /users/me/avatar ─────────────────────────────────────────────────────

async def test_upload_avatar(client: AsyncClient):
    tokens = await _register(client, "ava@test.com", "ava_user")
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch.object(storage_service, "upload_avatar", new=AsyncMock(return_value=FAKE_AVATAR_URL)):
        resp = await client.post(
            AVATAR_URL,
            files={"avatar": ("photo.jpg", _make_jpeg(), "image/jpeg")},
            headers=auth,
        )
    assert resp.status_code == 200
    assert resp.json()["avatar_url"] == FAKE_AVATAR_URL

    me = await client.get(ME_URL, headers=auth)
    assert me.json()["avatar_url"] == FAKE_AVATAR_URL


async def test_upload_avatar_wrong_type(client: AsyncClient):
    tokens = await _register(client, "ava_bad@test.com", "ava_bad_user")
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(
        AVATAR_URL,
        files={"avatar": ("file.txt", b"not an image", "text/plain")},
        headers=auth,
    )
    assert resp.status_code == 415


# ── DELETE /users/me/avatar ───────────────────────────────────────────────────

async def test_delete_avatar(client: AsyncClient):
    tokens = await _register(client, "del_ava@test.com", "del_ava_user")
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch.object(storage_service, "upload_avatar", new=AsyncMock(return_value=FAKE_AVATAR_URL)):
        await client.post(
            AVATAR_URL,
            files={"avatar": ("photo.jpg", _make_jpeg(), "image/jpeg")},
            headers=auth,
        )

    with patch.object(storage_service, "delete_avatar", new=AsyncMock()):
        resp = await client.delete(AVATAR_URL, headers=auth)
    assert resp.status_code == 204

    me = await client.get(ME_URL, headers=auth)
    assert me.json()["avatar_url"] is None


async def test_delete_avatar_when_none(client: AsyncClient):
    tokens = await _register(client, "nodava@test.com", "nodava_user")
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.delete(AVATAR_URL, headers=auth)
    assert resp.status_code == 204
