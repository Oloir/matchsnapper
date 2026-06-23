from uuid import UUID

from pydantic import BaseModel, field_validator

WEIGHT_LABELS = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
WEIGHT_VALUES = {v: k for k, v in WEIGHT_LABELS.items()}


class SnapshotItemIn(BaseModel):
    tag_id: UUID
    weight: str  # "S" | "A" | "B" | "C" | "D"

    @field_validator("weight")
    @classmethod
    def weight_valid(cls, v: str) -> str:
        v = v.upper()
        if v not in WEIGHT_LABELS:
            raise ValueError(f"weight must be one of {list(WEIGHT_LABELS)}")
        return v


class SnapshotItemOut(BaseModel):
    tag_id: UUID
    tag_name: str
    weight: str  # letter label


class SnapshotOut(BaseModel):
    items: list[SnapshotItemOut]
