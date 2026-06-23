from uuid import UUID

from pydantic import BaseModel


class CommonTag(BaseModel):
    tag: str
    weight_mine: str
    weight_theirs: str


class MatchUser(BaseModel):
    id: UUID
    username: str
    avatar_url: str | None = None
    bio: str | None = None


class MatchResult(BaseModel):
    user: MatchUser
    score: float
    is_viewed: bool
    common_tags: list[CommonTag]


class MatchList(BaseModel):
    results: list[MatchResult]
    total: int
    page: int
    limit: int
    pages: int


class SimilarityResponse(BaseModel):
    user_id: UUID
    score: float
    common_tags: list[CommonTag]


class ViewOut(BaseModel):
    viewer_id: UUID
    viewed_id: UUID
    is_viewed: bool


class ContactOut(BaseModel):
    from_user_id: UUID
    to_user_id: UUID
    status: str
