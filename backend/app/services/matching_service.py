import math
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interactions import ProfileView
from app.models.snapshot import SnapshotItem
from app.models.tag import Tag
from app.models.user import User
from app.schemas.matching import CommonTag, MatchList, MatchResult, MatchUser, SimilarityResponse
from app.schemas.snapshot import WEIGHT_VALUES


def _cosine(a: dict, b: dict) -> float:
    tags = set(a) | set(b)
    if not tags:
        return 0.0
    va = np.array([a.get(t, 0) for t in tags], dtype=np.float64)
    vb = np.array([b.get(t, 0) for t in tags], dtype=np.float64)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def _common_tags(
    mine: dict, theirs: dict, tag_names: dict[UUID, str]
) -> list[CommonTag]:
    return [
        CommonTag(
            tag=tag_names.get(tid, ""),
            weight_mine=WEIGHT_VALUES[mine[tid]],
            weight_theirs=WEIGHT_VALUES[theirs[tid]],
        )
        for tid in set(mine) & set(theirs)
    ]


async def _load_snapshot(session: AsyncSession, user_id: UUID) -> dict[UUID, int]:
    rows = await session.execute(
        select(SnapshotItem.tag_id, SnapshotItem.weight)
        .where(SnapshotItem.user_id == user_id)
    )
    return {row.tag_id: row.weight for row in rows.all()}


async def compute_matches(
    session: AsyncSession,
    user_id: UUID,
    page: int,
    limit: int,
) -> MatchList:
    my_snap = await _load_snapshot(session, user_id)

    # All other active users
    users_rows = await session.execute(
        select(User).where(User.is_active == True, User.id != user_id)
    )
    other_users: dict[UUID, User] = {u.id: u for u in users_rows.scalars()}

    if not other_users:
        return MatchList(results=[], total=0, page=page, limit=limit, pages=1)

    # Their snapshots
    snap_rows = await session.execute(
        select(SnapshotItem.user_id, SnapshotItem.tag_id, SnapshotItem.weight)
        .where(SnapshotItem.user_id.in_(other_users.keys()))
    )
    other_snaps: dict[UUID, dict[UUID, int]] = {}
    for row in snap_rows.all():
        other_snaps.setdefault(row.user_id, {})[row.tag_id] = row.weight

    # Tag names for common_tags computation
    all_ids = set(my_snap) | {tid for s in other_snaps.values() for tid in s}
    tag_names: dict[UUID, str] = {}
    if all_ids:
        tag_rows = await session.execute(select(Tag.id, Tag.name).where(Tag.id.in_(all_ids)))
        tag_names = {r.id: r.name for r in tag_rows.all()}

    # Viewed set
    viewed_rows = await session.execute(
        select(ProfileView.viewed_id).where(ProfileView.viewer_id == user_id)
    )
    viewed_ids: set[UUID] = {r.viewed_id for r in viewed_rows.all()}

    # Compute scores
    scored = []
    for uid, user in other_users.items():
        their_snap = other_snaps.get(uid, {})
        score = _cosine(my_snap, their_snap)
        is_viewed = uid in viewed_ids
        scored.append((score, is_viewed, uid, user, their_snap))

    # Sort: unviewed first (DESC score), then viewed (DESC score)
    scored.sort(key=lambda x: (x[1], -x[0]))

    total = len(scored)
    page_items = scored[(page - 1) * limit : page * limit]

    results = [
        MatchResult(
            user=MatchUser(id=u.id, username=u.username, avatar_url=u.avatar_url, bio=u.bio),
            score=round(score, 6),
            is_viewed=is_viewed,
            common_tags=_common_tags(my_snap, their_snap, tag_names),
        )
        for score, is_viewed, _, u, their_snap in page_items
    ]

    return MatchList(
        results=results,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )


async def compute_similarity(
    session: AsyncSession,
    user_id: UUID,
    other_id: UUID,
) -> SimilarityResponse:
    my_snap = await _load_snapshot(session, user_id)
    their_snap = await _load_snapshot(session, other_id)

    all_ids = set(my_snap) | set(their_snap)
    tag_names: dict[UUID, str] = {}
    if all_ids:
        tag_rows = await session.execute(select(Tag.id, Tag.name).where(Tag.id.in_(all_ids)))
        tag_names = {r.id: r.name for r in tag_rows.all()}

    return SimilarityResponse(
        user_id=other_id,
        score=round(_cosine(my_snap, their_snap), 6),
        common_tags=_common_tags(my_snap, their_snap, tag_names),
    )
