import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REGISTER_URL = "/api/v1/auth/register"
TAGS_URL = "/api/v1/tags"
SNAPSHOT_URL = "/api/v1/snapshots/me"
ITEMS_URL = "/api/v1/snapshots/me/items"
MATCHING_URL = "/api/v1/matching"


async def _auth(client: AsyncClient, email: str, username: str) -> dict:
    resp = await client.post(REGISTER_URL, json={
        "email": email, "username": username, "password": "password123",
    })
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _me_id(client: AsyncClient, auth: dict) -> str:
    resp = await client.get("/api/v1/users/me", headers=auth)
    return resp.json()["id"]


async def _make_tag(client: AsyncClient, auth: dict, name: str) -> str:
    resp = await client.post(TAGS_URL, json={"name": name}, headers=auth)
    assert resp.status_code == 201
    return resp.json()["id"]


async def _set_snapshot(client: AsyncClient, auth: dict, items: list[dict]) -> None:
    resp = await client.put(SNAPSHOT_URL, json=items, headers=auth)
    assert resp.status_code == 200


# ── GET /matching ─────────────────────────────────────────────────────────────

async def test_matching_returns_list(client: AsyncClient):
    auth = await _auth(client, "match_list@test.com", "match_list_user")
    resp = await client.get(MATCHING_URL, headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data


async def test_matching_excludes_self(client: AsyncClient):
    auth = await _auth(client, "match_self@test.com", "match_self_user")
    my_id = await _me_id(client, auth)
    resp = await client.get(MATCHING_URL, headers=auth)
    result_ids = [r["user"]["id"] for r in resp.json()["results"]]
    assert my_id not in result_ids


async def test_matching_score_range(client: AsyncClient):
    auth = await _auth(client, "match_score@test.com", "match_score_user")
    resp = await client.get(MATCHING_URL, headers=auth)
    for r in resp.json()["results"]:
        assert 0.0 <= r["score"] <= 1.0


async def test_matching_unviewed_before_viewed(client: AsyncClient):
    auth_a = await _auth(client, "match_ord_a@test.com", "match_ord_a")
    auth_b = await _auth(client, "match_ord_b@test.com", "match_ord_b")
    auth_c = await _auth(client, "match_ord_c@test.com", "match_ord_c")

    tag = await _make_tag(client, auth_a, "match order tag unique")
    await _set_snapshot(client, auth_a, [{"tag_id": tag, "weight": "S"}])
    await _set_snapshot(client, auth_b, [{"tag_id": tag, "weight": "S"}])
    await _set_snapshot(client, auth_c, [{"tag_id": tag, "weight": "S"}])

    b_id = await _me_id(client, auth_b)
    await client.post(f"/api/v1/users/{b_id}/view", headers=auth_a)

    resp = await client.get(MATCHING_URL, headers=auth_a)
    results = resp.json()["results"]

    # find b and c in results
    b_result = next((r for r in results if r["user"]["id"] == b_id), None)
    assert b_result is not None
    assert b_result["is_viewed"] is True

    # All unviewed should come before any viewed
    unviewed_indices = [i for i, r in enumerate(results) if not r["is_viewed"]]
    viewed_indices = [i for i, r in enumerate(results) if r["is_viewed"]]
    if unviewed_indices and viewed_indices:
        assert max(unviewed_indices) < min(viewed_indices)


async def test_matching_with_common_tags(client: AsyncClient):
    auth_a = await _auth(client, "match_common_a@test.com", "match_common_a")
    auth_b = await _auth(client, "match_common_b@test.com", "match_common_b")

    tag = await _make_tag(client, auth_a, "match common tag unique xyz")
    await _set_snapshot(client, auth_a, [{"tag_id": tag, "weight": "S"}])
    await _set_snapshot(client, auth_b, [{"tag_id": tag, "weight": "A"}])

    b_id = await _me_id(client, auth_b)
    resp = await client.get(MATCHING_URL, headers=auth_a)
    b_result = next((r for r in resp.json()["results"] if r["user"]["id"] == b_id), None)

    assert b_result is not None
    assert b_result["score"] > 0
    assert len(b_result["common_tags"]) >= 1
    ct = b_result["common_tags"][0]
    assert ct["weight_mine"] == "S"
    assert ct["weight_theirs"] == "A"


async def test_matching_pagination(client: AsyncClient):
    auth = await _auth(client, "match_page@test.com", "match_page_user")
    resp = await client.get(MATCHING_URL, params={"page": 1, "limit": 2}, headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 2
    assert len(data["results"]) <= 2


# ── GET /matching/{user_id} ───────────────────────────────────────────────────

async def test_similarity_with_user(client: AsyncClient):
    auth_a = await _auth(client, "sim_a@test.com", "sim_a_user")
    auth_b = await _auth(client, "sim_b@test.com", "sim_b_user")

    tag = await _make_tag(client, auth_a, "sim tag unique abc")
    await _set_snapshot(client, auth_a, [{"tag_id": tag, "weight": "S"}])
    await _set_snapshot(client, auth_b, [{"tag_id": tag, "weight": "S"}])

    b_id = await _me_id(client, auth_b)
    resp = await client.get(f"{MATCHING_URL}/{b_id}", headers=auth_a)
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == pytest.approx(1.0, abs=1e-5)
    assert len(data["common_tags"]) == 1


async def test_similarity_with_self_rejected(client: AsyncClient):
    auth = await _auth(client, "sim_self@test.com", "sim_self_user")
    my_id = await _me_id(client, auth)
    resp = await client.get(f"{MATCHING_URL}/{my_id}", headers=auth)
    assert resp.status_code == 400


async def test_similarity_with_unknown_user(client: AsyncClient):
    auth = await _auth(client, "sim_unk@test.com", "sim_unk_user")
    resp = await client.get(f"{MATCHING_URL}/00000000-0000-0000-0000-000000000000", headers=auth)
    assert resp.status_code == 404


async def test_similarity_no_overlap_is_zero(client: AsyncClient):
    auth_a = await _auth(client, "sim_zero_a@test.com", "sim_zero_a")
    auth_b = await _auth(client, "sim_zero_b@test.com", "sim_zero_b")

    tag_a = await _make_tag(client, auth_a, "sim zero tag a unique")
    tag_b = await _make_tag(client, auth_b, "sim zero tag b unique")
    await _set_snapshot(client, auth_a, [{"tag_id": tag_a, "weight": "S"}])
    await _set_snapshot(client, auth_b, [{"tag_id": tag_b, "weight": "S"}])

    b_id = await _me_id(client, auth_b)
    resp = await client.get(f"{MATCHING_URL}/{b_id}", headers=auth_a)
    assert resp.json()["score"] == pytest.approx(0.0, abs=1e-5)
    assert resp.json()["common_tags"] == []
