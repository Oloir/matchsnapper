from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserUpdate(BaseModel):
    bio: str | None = None


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    avatar_url: str | None = None
    bio: str | None = None


class UserMe(UserPublic):
    email: str
    is_active: bool
    created_at: datetime


class AvatarResponse(BaseModel):
    avatar_url: str
