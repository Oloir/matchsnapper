from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.interactions import ContactRequest, ProfileView
from app.models.user import User
from app.schemas.matching import ContactOut, ViewOut
from app.services.auth_service import get_current_user

router = APIRouter()


async def _require_other_user(user_id: UUID, current_user: User, session: AsyncSession) -> User:
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot target yourself")
    other = await session.get(User, user_id)
    if not other or not other.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return other


# ── Profile views ─────────────────────────────────────────────────────────────

@router.post("/{user_id}/view", response_model=ViewOut, status_code=status.HTTP_201_CREATED)
async def mark_viewed(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _require_other_user(user_id, current_user, session)

    stmt = (
        insert(ProfileView)
        .values(viewer_id=current_user.id, viewed_id=user_id)
        .on_conflict_do_nothing()
    )
    await session.execute(stmt)
    await session.commit()

    return ViewOut(viewer_id=current_user.id, viewed_id=user_id, is_viewed=True)


@router.delete("/{user_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def unmark_viewed(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _require_other_user(user_id, current_user, session)

    await session.execute(
        delete(ProfileView).where(
            ProfileView.viewer_id == current_user.id,
            ProfileView.viewed_id == user_id,
        )
    )
    await session.commit()


# ── Contact requests ──────────────────────────────────────────────────────────

@router.post("/{user_id}/contact", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def send_contact(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _require_other_user(user_id, current_user, session)

    existing = await session.execute(
        select(ContactRequest).where(
            ContactRequest.from_user_id == current_user.id,
            ContactRequest.to_user_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact request already sent")

    req = ContactRequest(from_user_id=current_user.id, to_user_id=user_id)
    session.add(req)
    await session.commit()

    return ContactOut(from_user_id=current_user.id, to_user_id=user_id, status="pending")
