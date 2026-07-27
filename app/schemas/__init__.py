"""Pydantic request/response schemas, mirroring app/models/."""

from app.schemas.media import MediaRead, MediaType, Source
from app.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.schemas.user import UserCreate, UserRead
from app.schemas.user_media import (
    REVIEW_MAX_LENGTH,
    EntryCreate,
    EntryRead,
    EntryUpdate,
    ProgressUpdate,
    Status,
    StatusUpdate,
    reject_progress_on_movie,
)

__all__ = [
    "MediaRead",
    "MediaType",
    "Source",
    "UserCreate",
    "UserRead",
    "EntryCreate",
    "EntryRead",
    "EntryUpdate",
    "ProgressUpdate",
    "Status",
    "StatusUpdate",
    "REVIEW_MAX_LENGTH",
    "reject_progress_on_movie",
    "RecommendationItem",
    "RecommendationResponse",
]
