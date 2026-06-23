from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class TagCreate(BaseModel):
    name: str
    category: str | None = None

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        return v.strip().lower()


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category: str | None = None


class TagList(BaseModel):
    items: list[TagOut]
    total: int
    page: int
    limit: int
    pages: int
