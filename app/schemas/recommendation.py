"""Pydantic schemas for the group recommendation response.

See Design Decision 6: this is a deterministic watchlist-overlap result, not a
model prediction. Every field is traceable to rows the users actually saved.
"""

from typing import List, Optional

from pydantic import BaseModel

from app.schemas.media import MediaType


class RecommendationItem(BaseModel):
    media_id: int
    tmdb_id: Optional[int] = None
    title: str
    media_type: MediaType
    release_year: Optional[int] = None
    poster_path: Optional[str] = None
    # Echoes the requested users. By construction every returned title is on all
    # of their watchlists, which is the explanation shown in the UI.
    on_watchlist_of: List[int]
    # Null when nobody in the group has rated it yet.
    group_avg_rating: Optional[float] = None


class RecommendationResponse(BaseModel):
    user_ids: List[int]
    count: int
    results: List[RecommendationItem]
    # Populated only when count == 0, so the UI never has to invent a message.
    message: Optional[str] = None
