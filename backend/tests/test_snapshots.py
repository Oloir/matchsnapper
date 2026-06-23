import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REGISTER_URL = "/api/v1/auth/register"
TAGS_URL = "/api/v1/tags"
SNAPSHOT_URL = "/api/v1/snapshots/me"
ITEMS_URL = "/api/v1/snapshots/me/items"


async def _auth(client: AsyncClient, email: str, username: str) -> dict:
    resp = await client.post(REGISTER_URL, json={
        "email": email, "username": username, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _create_tag(client: AsyncClient, auth: dict, name: str, category: str | None = None) -> str:
    resp = await client.post(TAGS_URL, json={"name": name, "category": category}, headers=auth)
    assert resp.status_code == 201
    return resp.json()["id"]


# ── GET /snapshots/me ─────────────────────────────────────────────────────────

async def test_get_empty_snapshot(client: AsyncClient):
    auth = await _auth(client, "snap_empty@test.com", "snap_empty_user")
    resp = await client.get(SNAPSHOT_URL, headers=auth)
    assert resp.status_code == 200
    assert resp.json() == {"items": []}


# ── PUT /snapshots/me ─────────────────────────────────────────────────────────

async def test_put_snapshot(client: AsyncClient):
    auth = await _auth(client, "snap_put@test.com", "snap_put_user")
    tag_id = await _create_tag(client, auth, "snap put tag football")

    resp = await client.put(SNAPSHOT_URL, json=[{"tag_id": tag_id, "weight": "S"}], headers=auth)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["tag_id"] == tag_id
    assert items[0]["weight"] == "S"


async def test_put_snapshot_replaces_fully(client: AsyncClient):
    auth = await _auth(client, "snap_replace@test.com", "snap_replace_user")
    tag1 = await _create_tag(client, auth, "replace tag 1")
    tag2 = await _create_tag(client, auth, "replace tag 2")

    await client.put(SNAPSHOT_URL, json=[
        {"tag_id": tag1, "weight": "S"},
        {"tag_id": tag2, "weight": "A"},
    ], headers=auth)

    resp = await client.put(SNAPSHOT_URL, json=[{"tag_id": tag2, "weight": "B"}], headers=auth)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["tag_id"] == tag2
    assert items[0]["weight"] == "B"


async def test_put_snapshot_clear(client: AsyncClient):
    auth = await _auth(client, "snap_clear@test.com", "snap_clear_user")
    tag_id = await _create_tag(client, auth, "snap clear tag")
    await client.put(SNAPSHOT_URL, json=[{"tag_id": tag_id, "weight": "A"}], headers=auth)

    resp = await client.put(SNAPSHOT_URL, json=[], headers=auth)
    assert resp.status_code == 200
    assert resp.json()["items"] == []


async def test_put_snapshot_unknown_tag(client: AsyncClient):
    auth = await _auth(client, "snap_badtag@test.com", "snap_badtag_user")
    resp = await client.put(SNAPSHOT_URL, json=[
        {"tag_id": "00000000-0000-0000-0000-000000000000", "weight": "S"}
    ], headers=auth)
    assert resp.status_code == 404


# ── PATCH /snapshots/me/items ─────────────────────────────────────────────────

async def test_patch_item_add(client: AsyncClient):
    auth = await _auth(client, "snap_patch@test.com", "snap_patch_user")
    tag_id = await _create_tag(client, auth, "snap patch tag")

    resp = await client.patch(ITEMS_URL, json={"tag_id": tag_id, "weight": "C"}, headers=auth)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["tag_id"] == tag_id and i["weight"] == "C" for i in items)


async def test_patch_item_update_weight(client: AsyncClient):
    auth = await _auth(client, "snap_upd@test.com", "snap_upd_user")
    tag_id = await _create_tag(client, auth, "snap update weight tag")

    await client.patch(ITEMS_URL, json={"tag_id": tag_id, "weight": "D"}, headers=auth)
    resp = await client.patch(ITEMS_URL, json={"tag_id": tag_id, "weight": "S"}, headers=auth)

    items = resp.json()["items"]
    match = next(i for i in items if i["tag_id"] == tag_id)
    assert match["weight"] == "S"


async def test_patch_item_unknown_tag(client: AsyncClient):
    auth = await _auth(client, "snap_unk@test.com", "snap_unk_user")
    resp = await client.patch(ITEMS_URL, json={
        "tag_id": "00000000-0000-0000-0000-000000000000", "weight": "A"
    }, headers=auth)
    assert resp.status_code == 404


# ── DELETE /snapshots/me/items/{tag_id} ───────────────────────────────────────

async def test_delete_item(client: AsyncClient):
    auth = await _auth(client, "snap_del@test.com", "snap_del_user")
    tag_id = await _create_tag(client, auth, "snap del tag")

    await client.patch(ITEMS_URL, json={"tag_id": tag_id, "weight": "B"}, headers=auth)
    resp = await client.delete(f"{ITEMS_URL}/{tag_id}", headers=auth)
    assert resp.status_code == 204

    snapshot = await client.get(SNAPSHOT_URL, headers=auth)
    assert not any(i["tag_id"] == tag_id for i in snapshot.json()["items"])


async def test_delete_item_not_in_snapshot(client: AsyncClient):
    auth = await _auth(client, "snap_del_miss@test.com", "snap_del_miss_user")
    tag_id = await _create_tag(client, auth, "snap del missing tag")

    resp = await client.delete(f"{ITEMS_URL}/{tag_id}", headers=auth)
    assert resp.status_code == 404


# ── weight ordering ───────────────────────────────────────────────────────────

async def test_snapshot_ordered_by_weight_desc(client: AsyncClient):
    auth = await _auth(client, "snap_order@test.com", "snap_order_user")
    tag_s = await _create_tag(client, auth, "snap order s tag")
    tag_d = await _create_tag(client, auth, "snap order d tag")

    await client.put(SNAPSHOT_URL, json=[
        {"tag_id": tag_d, "weight": "D"},
        {"tag_id": tag_s, "weight": "S"},
    ], headers=auth)

    resp = await client.get(SNAPSHOT_URL, headers=auth)
    items = resp.json()["items"]
    assert items[0]["weight"] == "S"
    assert items[-1]["weight"] == "D"
