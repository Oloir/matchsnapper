import uuid

from sqlalchemy import ForeignKey, Index, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SnapshotItem(Base):
    __tablename__ = "snapshot_items"
    __table_args__ = (
        UniqueConstraint("user_id", "tag_id"),
        Index("idx_snapshot_user", "user_id"),
        Index("idx_snapshot_tag", "tag_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id"), nullable=False
    )
    weight: Mapped[int] = mapped_column(SmallInteger, nullable=False)
