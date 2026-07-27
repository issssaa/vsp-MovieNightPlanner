"""SQLAlchemy ORM model for a Media title (movie or TV show).

One row per title, shared by every user who saves it. Holds only catalogue
metadata that belongs to the title itself — nothing personal. Status, progress,
rating, and review live on UserMedia. See Design Decision 2.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)

    # Null only for manually created entries (source == "manual").
    tmdb_id = Column(Integer, nullable=True, index=True)
    media_type = Column(String(5), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    original_title = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)
    poster_path = Column(String(500), nullable=True)
    release_year = Column(Integer, nullable=True)

    # TV totals are catalogue facts, so they live here. Per-user position
    # (current_season / current_episode) lives on UserMedia.
    total_seasons = Column(Integer, nullable=True)
    total_episodes = Column(Integer, nullable=True)

    source = Column(String(10), nullable=False, default="tmdb", server_default="tmdb")

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    entries = relationship(
        "UserMedia",
        back_populates="media",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("media_type IN ('movie', 'tv')", name="ck_media_media_type"),
        CheckConstraint("source IN ('tmdb', 'manual')", name="ck_media_source"),
        CheckConstraint(
            "release_year IS NULL OR (release_year BETWEEN 1870 AND 2200)",
            name="ck_media_release_year",
        ),
        # A TMDB title is stored once. SQLite treats NULLs as distinct in a unique
        # index, so any number of manual entries with tmdb_id IS NULL is allowed —
        # which is what we want.
        UniqueConstraint("tmdb_id", "media_type", name="uq_media_tmdb_id_media_type"),
    )
