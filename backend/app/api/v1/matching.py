from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.schemas.matching import MatchList, SimilarityResponse
from app.services.auth_service import get_current_user
from app.services.matching_service import compute_matches, compute_similarity

router = APIRouter()


@router.get("", response_model=MatchList)
async def list_matches(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await compute_matches(session, current_user.id, page, limit)


@router.get("/{user_id}", response_model=SimilarityResponse)
async def get_similarity(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot compare with yourself")

    other = await session.get(User, user_id)
    if not other or not other.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await compute_similarity(session, current_user.id, user_id)
