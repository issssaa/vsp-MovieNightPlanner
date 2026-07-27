"""Pydantic schemas for a user's saved entry (status, progress, rating, review)."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.media import MediaRead, MediaType, Source

REVIEW_MAX_LENGTH = 2000


class Status(str, Enum):
    WATCHLIST = "watchlist"
    WATCHING = "watching"
    COMPLETED = "completed"
    DROPPED = "dropped"


class EntryCreate(BaseModel):
    """Save a title to one user's list.

    Catalogue fields are only used when the shared `media` row does not exist yet.
    If another user already saved this title, the existing row is reused and any
    catalogue fields sent here are ignored.

    PHASE 2 HANDOFF: once `CatalogueService` exists, the backend will fetch title,
    overview, poster, and year from TMDB using `tmdb_id`, and the client will stop
    sending them. Until then a new TMDB title needs at least a `title`, because
    there is no other way to learn it offline.
    """

    user_id: int
    media_type: MediaType
    source: Source = Source.TMDB
    status: Status = Status.WATCHLIST

    tmdb_id: Optional[int] = Field(default=None, ge=1)

    # Catalogue metadata for creating the shared media row.
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    original_title: Optional[str] = Field(default=None, max_length=500)
    overview: Optional[str] = None
    poster_path: Optional[str] = Field(default=None, max_length=500)
    release_year: Optional[int] = Field(default=None, ge=1870, le=2200)
    total_seasons: Optional[int] = Field(default=None, ge=0)
    total_episodes: Optional[int] = Field(default=None, ge=0)

    # Personal fields.
    current_season: Optional[int] = Field(default=None, ge=0)
    current_episode: Optional[int] = Field(default=None, ge=0)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    review: Optional[str] = Field(default=None, max_length=REVIEW_MAX_LENGTH)

    @model_validator(mode="after")
    def check_source_and_progress(self) -> "EntryCreate":
        if self.source is Source.MANUAL:
            if self.tmdb_id is not None:
                raise ValueError("A manual entry must not carry a tmdb_id.")
            if not self.title:
                raise ValueError("A manual entry requires a title.")
        else:
            if self.tmdb_id is None:
                raise ValueError(
                    "tmdb_id is required unless source is 'manual'. "
                    "Use source='manual' to add a title by hand."
                )

        # media_type is known here, so the TV-only rule can be enforced up front.
        if self.media_type is not MediaType.TV:
            reject_progress_on_movie(self.current_season, self.current_episode)
            if self.total_seasons is not None or self.total_episodes is not None:
                raise ValueError(
                    "total_seasons and total_episodes only apply to TV shows."
                )
        return self


class EntryUpdate(BaseModel):
    """Partial update of the personal fields. Sending no fields is rejected.

    The TV-only rule for progress cannot be checked here, because media_type lives
    on the joined `media` row. The router re-checks it against the database.
    """

    status: Optional[Status] = None
    current_season: Optional[int] = Field(default=None, ge=0)
    current_episode: Optional[int] = Field(default=None, ge=0)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    review: Optional[str] = Field(default=None, max_length=REVIEW_MAX_LENGTH)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "EntryUpdate":
        if not self.model_fields_set:
            raise ValueError("Send at least one field to update.")
        return self


class StatusUpdate(BaseModel):
    """Update only the watch status."""

    status: Status


class ProgressUpdate(BaseModel):
    """Update TV position. At least one of the two fields is required."""

    current_season: Optional[int] = Field(default=None, ge=0)
    current_episode: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "ProgressUpdate":
        if self.current_season is None and self.current_episode is None:
            raise ValueError("Send current_season, current_episode, or both.")
        return self


class EntryRead(BaseModel):
    """One saved entry, with its shared catalogue metadata nested."""

    id: int
    user_id: int
    status: Status
    current_season: Optional[int] = None
    current_episode: Optional[int] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    media: MediaRead

    model_config = ConfigDict(from_attributes=True)


def reject_progress_on_movie(
    current_season: Optional[int], current_episode: Optional[int]
) -> None:
    """Raise if TV progress fields were supplied for a movie.

    Shared by EntryCreate (where media_type is in the payload) and by the media
    router (where it has to be read from the joined media row). Keeping it in one
    place means the rule cannot drift between the two call sites.
    """
    if current_season is not None or current_episode is not None:
        raise ValueError(
            "current_season and current_episode only apply to TV shows, not movies."
        )
