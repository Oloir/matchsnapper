"""
Load fixture data into the database.

Usage (from backend/):
    uv run python fixtures/load_fixtures.py
    uv run python fixtures/load_fixtures.py --check   # also print match quality
"""
import asyncio
import json
import sys
from pathlib import Path

import bcrypt
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure app package is importable when run from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.models import User, Tag, SnapshotItem  # noqa: registers models

FIXTURES_DIR = Path(__file__).parent
WEIGHT_MAP = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
WEIGHT_LABELS = {v: k for k, v in WEIGHT_MAP.items()}


# ── helpers ───────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def _load_tags(session: AsyncSession) -> dict[str, object]:
    """Insert tags (skip existing). Returns name→Tag mapping."""
    raw = json.loads((FIXTURES_DIR / "tags.json").read_text())
    existing_rows = (await session.execute(select(Tag))).scalars().all()
    existing = {t.name: t for t in existing_rows}

    for item in raw:
        if item["name"] not in existing:
            tag = Tag(name=item["name"], category=item.get("category"))
            session.add(tag)

    await session.flush()

    all_tags = (await session.execute(select(Tag))).scalars().all()
    return {t.name: t for t in all_tags}


async def _load_users(session: AsyncSession, tag_map: dict) -> list[User]:
    """Insert users + snapshots (skip existing emails)."""
    raw = json.loads((FIXTURES_DIR / "users.json").read_text())
    existing_emails = set(
        (await session.execute(select(User.email))).scalars().all()
    )

    created: list[User] = []
    for u in raw:
        if u["email"] in existing_emails:
            print(f"  skip (exists): {u['username']}")
            continue

        user = User(
            email=u["email"],
            username=u["username"],
            hashed_password=_hash(u["password"]),
            bio=u.get("bio"),
        )
        session.add(user)
        await session.flush()  # get user.id

        for item in u.get("snapshot", []):
            tag_name = item["tag"]
            tag = tag_map.get(tag_name)
            if tag is None:
                print(f"  WARNING: tag '{tag_name}' not found, skipping")
                continue
            weight = WEIGHT_MAP[item["weight"]]
            stmt = (
                pg_insert(SnapshotItem)
                .values(user_id=user.id, tag_id=tag.id, weight=weight)
                .on_conflict_do_nothing()
            )
            await session.execute(stmt)

        created.append(user)
        print(f"  created: {user.username}")

    return created


# ── quality check ─────────────────────────────────────────────────────────────

def _cosine(a: dict, b: dict) -> float:
    import numpy as np
    keys = set(a) | set(b)
    va = np.array([a.get(k, 0) for k in keys], dtype=float)
    vb = np.array([b.get(k, 0) for k in keys], dtype=float)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


async def _check_quality(session: AsyncSession) -> None:
    users = (await session.execute(select(User))).scalars().all()
    items = (await session.execute(select(SnapshotItem))).scalars().all()
    tags = (await session.execute(select(Tag))).scalars().all()

    tag_names = {t.id: t.name for t in tags}
    snapshots: dict[object, dict] = {}
    for it in items:
        snapshots.setdefault(it.user_id, {})[it.tag_id] = it.weight

    print("\n=== Match Quality Check ===")
    sample_users = [u for u in users if u.id in snapshots][:5]
    for user in sample_users:
        vec_a = snapshots[user.id]
        scores = []
        for other in users:
            if other.id == user.id:
                continue
            vec_b = snapshots.get(other.id, {})
            score = _cosine(vec_a, vec_b)
            common = [tag_names[k] for k in vec_a if k in vec_b]
            scores.append((score, other.username, common))
        scores.sort(reverse=True)
        print(f"\nTop matches for @{user.username}:")
        for score, name, common in scores[:5]:
            tags_str = ", ".join(common) if common else "—"
            print(f"  {score:.2f}  @{name:<15}  common: {tags_str}")


# ── main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    check_quality = "--check" in sys.argv

    engine = create_async_engine(settings.database_url, echo=False)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as session:
        async with session.begin():
            print("Loading tags…")
            tag_map = await _load_tags(session)
            print(f"  {len(tag_map)} tags in DB")

            print("Loading users…")
            await _load_users(session, tag_map)

        if check_quality:
            await _check_quality(session)

    await engine.dispose()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
