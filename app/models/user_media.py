"""SQLAlchemy ORM model for one user's relationship to one title.

Everything personal lives here: watch status, TV position, rating, review.
`UNIQUE (user_id, media_id)` expresses "a user saves a title at most once",
while two different users saving the same title is normal and must succeed.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base

STATUSES = ("watchlist", "watching", "completed", "dropped")


class UserMedia(Base):
    __tablename__ = "user_media"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_id = Column(
        Integer,
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(10), nullable=False, default="watchlist", server_default="watchlist"
    )

    # TV position. Only valid when the joined media.media_type == 'tv'. That rule
    # spans two tables, so SQLite cannot express it as a CHECK — it is enforced in
    # app/schemas/user_media.py and in the media router. See Design Decision 2.
    current_season = Column(Integer, nullable=True)
    current_episode = Column(Integer, nullable=True)

    rating = Column(Integer, nullable=True)
    review = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="entries")
    media = relationship("Media", back_populates="entries")

    __table_args__ = (
        UniqueConstraint("user_id", "media_id", name="uq_user_media_user_id_media_id"),
        CheckConstraint(
            "status IN ('watchlist', 'watching', 'completed', 'dropped')",
            name="ck_user_media_status",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 5)", name="ck_user_media_rating"
        ),
        CheckConstraint(
            "current_season IS NULL OR current_season >= 0",
            name="ck_user_media_current_season",
        ),
        CheckConstraint(
            "current_episode IS NULL OR current_episode >= 0",
            name="ck_user_media_current_episode",
        ),
    )
