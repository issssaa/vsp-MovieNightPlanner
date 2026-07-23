"""Pydantic schemas for Movie request/response validation."""

from datetime import date
from typing import Optional

from pydantic import BaseModel


class MovieBase(BaseModel):
    """Fields shared by create and update operations."""

    title: str
    overview: Optional[str] = None
    release_date: Optional[date] = None
    genres: Optional[str] = None
    poster_path: Optional[str] = None


class MovieCreate(MovieBase):
    """Payload for creating a movie; tmdb_id is required on creation."""

    tmdb_id: int


class MovieUpdate(BaseModel):
    """Payload for PATCH; every field is optional so partial updates work."""

    tmdb_id: Optional[int] = None
    title: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[date] = None
    genres: Optional[str] = None
    poster_path: Optional[str] = None


class MovieRead(MovieBase):
    """Response model returned to clients."""

    id: int
    tmdb_id: int

    # Allow building the schema directly from an ORM object.
    model_config = {"from_attributes": True}
