"""Group recommendation: what do these users all want to watch?

Design Decision 6 — a deterministic overlap over saved watchlists. No model, no
external service. Every returned title is one that every listed user actually put
on their watchlist, which is why the result is explainable and testable.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.media import Media
from app.models.user_media import UserMedia
from app.routers.users import get_user_or_404
from app.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.schemas.user_media import Status

router = APIRouter(tags=["recommendations"])


def parse_user_ids(raw: str) -> List[int]:
    """Turn `?user_ids=1,2,2,3` into [1, 2, 3], rejecting anything unusable.

    Duplicates are collapsed before counting, otherwise passing the same id twice
    would make every title in that one user's watchlist look like a group match.
    """
    seen: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = int(part)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"'{part}' is not a valid user id. Use e.g. ?user_ids=1,2",
            ) from None
        if value not in seen:
            seen.append(value)

    if len(seen) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Group recommendation needs at least two distinct user ids. "
                "Use e.g. ?user_ids=1,2"
            ),
        )
    return seen


@router.get("/recommendations", response_model=RecommendationResponse)
def recommend_for_group(
    user_ids: str = Query(
        ...,
        description="Comma-separated user ids, at least two, e.g. 1,2",
        examples=["1,2"],
    ),
    db: Session = Depends(get_db),
):
    ids = parse_user_ids(user_ids)

    # Fail loudly on an unknown id rather than quietly recommending for a smaller
    # group than the user asked about.
    for user_id in ids:
        get_user_or_404(db, user_id)

    average_rating = func.avg(UserMedia.rating).label("group_avg_rating")

    rows = (
        db.query(
            Media.id,
            Media.tmdb_id,
            Media.title,
            Media.media_type,
            Media.release_year,
            Media.poster_path,
            average_rating,
        )
        .join(UserMedia, UserMedia.media_id == Media.id)
        # in_() binds each id as a parameter — never string-formatted into SQL.
        .filter(
            UserMedia.user_id.in_(ids),
            UserMedia.status == Status.WATCHLIST.value,
        )
        .group_by(Media.id)
        # The whole feature is this line: keep only titles that every listed user
        # has on their watchlist.
        .having(func.count(func.distinct(UserMedia.user_id)) == len(ids))
        # Unrated titles sort last. Expressed as a boolean rather than NULLS LAST
        # so it does not depend on the bundled SQLite version.
        .order_by((average_rating.is_(None)).asc(), average_rating.desc(), Media.title)
        .all()
    )

    results = [
        RecommendationItem(
            media_id=row.id,
            tmdb_id=row.tmdb_id,
            title=row.title,
            media_type=row.media_type,
            release_year=row.release_year,
            poster_path=row.poster_path,
            on_watchlist_of=ids,
            group_avg_rating=(
                round(float(row.group_avg_rating), 2)
                if row.group_avg_rating is not None
                else None
            ),
        )
        for row in rows
    ]

    return RecommendationResponse(
        user_ids=ids,
        count=len(results),
        results=results,
        message=(
            None
            if results
            else (
                "These users have no watchlist titles in common. Add more titles, "
                "or try a smaller group."
            )
        ),
    )
