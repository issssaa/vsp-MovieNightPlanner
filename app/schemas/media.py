"""Pydantic schemas and enums for shared catalogue metadata."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MediaType(str, Enum):
    MOVIE = "movie"
    TV = "tv"


class Source(str, Enum):
    TMDB = "tmdb"
    MANUAL = "manual"


class MediaRead(BaseModel):
    """One catalogue title, as returned inside a user's entry."""

    id: int
    tmdb_id: Optional[int] = None
    media_type: MediaType
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    release_year: Optional[int] = None
    total_seasons: Optional[int] = None
    total_episodes: Optional[int] = None
    source: Source

    model_config = ConfigDict(from_attributes=True)
