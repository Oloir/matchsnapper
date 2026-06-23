from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.schemas.snapshot import SnapshotItemIn, SnapshotOut
from app.services.auth_service import get_current_user
from app.services.snapshot_service import (
    delete_item,
    get_snapshot,
    replace_snapshot,
    upsert_item,
)

router = APIRouter()


@router.get("/me", response_model=SnapshotOut)
async def get_my_snapshot(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await get_snapshot(session, current_user.id)


@router.put("/me", response_model=SnapshotOut)
async def put_my_snapshot(
    items: list[SnapshotItemIn],
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await replace_snapshot(session, current_user.id, items)


@router.patch("/me/items", response_model=SnapshotOut)
async def patch_my_snapshot_item(
    item: SnapshotItemIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await upsert_item(session, current_user.id, item)


@router.delete("/me/items/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_snapshot_item(
    tag_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await delete_item(session, current_user.id, tag_id)
