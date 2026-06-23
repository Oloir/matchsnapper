from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.snapshot import SnapshotItem
from app.models.tag import Tag
from app.schemas.snapshot import (
    WEIGHT_LABELS,
    WEIGHT_VALUES,
    SnapshotItemIn,
    SnapshotItemOut,
    SnapshotOut,
)


async def get_snapshot(session: AsyncSession, user_id: UUID) -> SnapshotOut:
    rows = await session.execute(
        select(SnapshotItem, Tag)
        .join(Tag, SnapshotItem.tag_id == Tag.id)
        .where(SnapshotItem.user_id == user_id)
        .order_by(SnapshotItem.weight.desc(), Tag.name)
    )
    items = [
        SnapshotItemOut(
            tag_id=si.tag_id,
            tag_name=tag.name,
            weight=WEIGHT_VALUES[si.weight],
        )
        for si, tag in rows.all()
    ]
    return SnapshotOut(items=items)


async def replace_snapshot(
    session: AsyncSession, user_id: UUID, items_in: list[SnapshotItemIn]
) -> SnapshotOut:
    if items_in:
        tag_ids = [item.tag_id for item in items_in]
        result = await session.execute(select(Tag.id).where(Tag.id.in_(tag_ids)))
        found = {row[0] for row in result.all()}
        missing = set(tag_ids) - found
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tags not found: {[str(t) for t in missing]}",
            )

    await session.execute(delete(SnapshotItem).where(SnapshotItem.user_id == user_id))

    for item in items_in:
        session.add(SnapshotItem(
            user_id=user_id,
            tag_id=item.tag_id,
            weight=WEIGHT_LABELS[item.weight],
        ))

    await session.commit()
    return await get_snapshot(session, user_id)


async def upsert_item(
    session: AsyncSession, user_id: UUID, item_in: SnapshotItemIn
) -> SnapshotOut:
    tag = await session.get(Tag, item_in.tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    weight_int = WEIGHT_LABELS[item_in.weight]
    stmt = (
        insert(SnapshotItem)
        .values(user_id=user_id, tag_id=item_in.tag_id, weight=weight_int)
        .on_conflict_do_update(
            index_elements=["user_id", "tag_id"],
            set_={"weight": weight_int},
        )
    )
    await session.execute(stmt)
    await session.commit()
    return await get_snapshot(session, user_id)


async def delete_item(
    session: AsyncSession, user_id: UUID, tag_id: UUID
) -> None:
    result = await session.execute(
        delete(SnapshotItem)
        .where(SnapshotItem.user_id == user_id, SnapshotItem.tag_id == tag_id)
        .returning(SnapshotItem.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not in snapshot")
