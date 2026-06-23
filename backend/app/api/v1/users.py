from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.schemas.user import AvatarResponse, UserMe, UserPublic, UserUpdate
from app.services.auth_service import get_current_user
from app.services.storage_service import storage_service

router = APIRouter()

_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@router.get("/me", response_model=UserMe)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserMe)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if "bio" in body.model_fields_set:
        current_user.bio = body.bio
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=AvatarResponse)
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if avatar.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported type: {avatar.content_type}",
        )
    data = await avatar.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 5 MB)",
        )
    url = await storage_service.upload_avatar(current_user.id, data)
    current_user.avatar_url = url
    session.add(current_user)
    await session.commit()
    return AvatarResponse(avatar_url=url)


@router.delete("/me/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.avatar_url:
        await storage_service.delete_avatar(current_user.id)
        current_user.avatar_url = None
        session.add(current_user)
        await session.commit()


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
