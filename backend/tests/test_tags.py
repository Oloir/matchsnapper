import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REGISTER_URL = "/api/v1/auth/register"
TAGS_URL = "/api/v1/tags"


async def _auth(client: AsyncClient, email: str, username: str) -> dict:
    resp = await client.post(REGISTER_URL, json={
        "email": email, "username": username, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ── POST /tags ────────────────────────────────────────────────────────────────

async def test_create_tag(client: AsyncClient):
    auth = await _auth(client, "tag_create@test.com", "tag_creator")
    resp = await client.post(TAGS_URL, json={"name": "Python", "category": "технологии"}, headers=auth)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "python"   # validator lowercases
    assert data["category"] == "технологии"
    assert "id" in data


async def test_create_tag_duplicate(client: AsyncClient):
    auth = await _auth(client, "dup_tag@test.com", "dup_tag_user")
    await client.post(TAGS_URL, json={"name": "Unique Tag"}, headers=auth)
    resp = await client.post(TAGS_URL, json={"name": "unique tag"}, headers=auth)
    assert resp.status_code == 409


async def test_create_tag_unauthenticated(client: AsyncClient):
    resp = await client.post(TAGS_URL, json={"name": "no auth tag"})
    assert resp.status_code in (401, 403)


async def test_create_tag_no_category(client: AsyncClient):
    auth = await _auth(client, "nocat@test.com", "nocat_user")
    resp = await client.post(TAGS_URL, json={"name": "nocategory tag"}, headers=auth)
    assert resp.status_code == 201
    assert resp.json()["category"] is None


# ── GET /tags ─────────────────────────────────────────────────────────────────

async def test_list_tags_empty(client: AsyncClient):
    resp = await client.get(TAGS_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "pages" in data


async def test_list_tags_search(client: AsyncClient):
    auth = await _auth(client, "search_tag@test.com", "search_tag_user")
    await client.post(TAGS_URL, json={"name": "searchable unique xyz"}, headers=auth)

    resp = await client.get(TAGS_URL, params={"q": "xyz"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("xyz" in item["name"] for item in items)


async def test_list_tags_category_filter(client: AsyncClient):
    auth = await _auth(client, "cat_filter@test.com", "cat_filter_user")
    await client.post(TAGS_URL, json={"name": "cat filter sport tag", "category": "спорт_test"}, headers=auth)

    resp = await client.get(TAGS_URL, params={"category": "спорт_test"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert all(item["category"] == "спорт_test" for item in items)


async def test_list_tags_pagination(client: AsyncClient):
    resp = await client.get(TAGS_URL, params={"page": 1, "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["limit"] == 5
    assert len(data["items"]) <= 5
