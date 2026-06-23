import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagList, TagOut
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("", response_model=TagList)
async def list_tags(
    q: str | None = Query(None, description="Search by name (case-insensitive)"),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    base = select(Tag)
    if q:
        base = base.where(Tag.name.ilike(f"%{q.strip().lower()}%"))
    if category:
        base = base.where(Tag.category == category)

    total_result = await session.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar_one()

    rows = await session.execute(
        base.order_by(Tag.name).offset((page - 1) * limit).limit(limit)
    )
    items = [TagOut.model_validate(tag) for tag in rows.scalars().all()]

    return TagList(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(
    body: TagCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(select(Tag).where(Tag.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists")

    tag = Tag(name=body.name, category=body.category, created_by=current_user.id)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return TagOut.model_validate(tag)
