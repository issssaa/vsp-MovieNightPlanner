"""CRUD endpoints for one user's saved media entries.

`{id}` in every path is a `user_media.id` — the id of one user's entry, not the
id of the shared catalogue row. Deleting an entry removes it from that user's
list and leaves the shared `media` row (and every other user's entry) alone.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.media import Media
from app.models.user_media import UserMedia
from app.routers.users import get_user_or_404
from app.schemas.media import MediaType, Source
from app.schemas.user_media import (
    EntryCreate,
    EntryRead,
    EntryUpdate,
    ProgressUpdate,
    Status,
    StatusUpdate,
    reject_progress_on_movie,
)

router = APIRouter(prefix="/media", tags=["media"])

# Catalogue fields that describe the title itself, used when creating a media row.
CATALOGUE_FIELDS = (
    "title",
    "original_title",
    "overview",
    "poster_path",
    "release_year",
    "total_seasons",
    "total_episodes",
)


def get_entry_or_404(db: Session, entry_id: int) -> UserMedia:
    entry = (
        db.query(UserMedia)
        .options(joinedload(UserMedia.media))
        .filter(UserMedia.id == entry_id)
        .first()
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Entry {entry_id} not found"
        )
    return entry


def check_progress_against_media(
    media: Media, current_season: Optional[int], current_episode: Optional[int]
) -> None:
    """Enforce the TV-only progress rule that SQLite cannot express as a CHECK.

    media_type lives on `media` while the progress columns live on `user_media`,
    so this is the layer where the two meet. See Design Decision 2.
    """
    if media.media_type != MediaType.TV.value:
        try:
            reject_progress_on_movie(current_season, current_episode)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc


def find_or_create_media(db: Session, payload: EntryCreate) -> Media:
    """Reuse the shared catalogue row if it exists, otherwise create it.

    This is what makes two users saving the same title share one row, which is in
    turn what makes the group overlap query a single GROUP BY.
    """
    if payload.source is Source.TMDB:
        existing = (
            db.query(Media)
            .filter(
                Media.tmdb_id == payload.tmdb_id,
                Media.media_type == payload.media_type.value,
            )
            .first()
        )
        if existing is not None:
            # Another user already imported this title. Catalogue fields in the
            # request are ignored on purpose: the stored row is the shared truth.
            return existing

        # PHASE 2 HANDOFF: replace this with a CatalogueService lookup by tmdb_id
        # so the backend stops trusting client-supplied metadata, as required by
        # the design document. Until that exists there is no offline way to learn
        # the title, so we require the client to send it.
        if not payload.title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"tmdb_id {payload.tmdb_id} is not in the local catalogue yet, "
                    "so 'title' is required to create it. This requirement goes "
                    "away in Phase 2 once metadata is fetched from TMDB."
                ),
            )

    # Manual entries always create their own row. Two users who each add the same
    # title by hand therefore get separate rows and will NOT match in group
    # recommendations — a known M1 limitation of the offline fallback path.
    media = Media(
        tmdb_id=payload.tmdb_id,
        media_type=payload.media_type.value,
        source=payload.source.value,
        **{field: getattr(payload, field) for field in CATALOGUE_FIELDS},
    )
    db.add(media)
    db.flush()  # assign media.id without committing yet
    return media


@router.post("", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate, db: Session = Depends(get_db)):
    get_user_or_404(db, payload.user_id)

    media = find_or_create_media(db, payload)
    check_progress_against_media(media, payload.current_season, payload.current_episode)

    already_saved = (
        db.query(UserMedia)
        .filter(
            UserMedia.user_id == payload.user_id,
            UserMedia.media_id == media.id,
        )
        .first()
    )
    if already_saved is not None:
        # This user already has it. A DIFFERENT user saving the same title is
        # normal and must succeed, which is why the check includes user_id.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"User {payload.user_id} has already saved '{media.title}' "
                f"(entry {already_saved.id})"
            ),
        )

    entry = UserMedia(
        user_id=payload.user_id,
        media_id=media.id,
        status=payload.status.value,
        current_season=payload.current_season,
        current_episode=payload.current_episode,
        rating=payload.rating,
        review=payload.review,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=List[EntryRead])
def list_entries(
    user_id: int = Query(..., description="Whose list to return"),
    status_filter: Optional[Status] = Query(
        default=None, alias="status", description="Filter by watch status"
    ),
    media_type: Optional[MediaType] = Query(default=None),
    title: Optional[str] = Query(
        default=None, description="Case-insensitive substring match on title"
    ),
    db: Session = Depends(get_db),
):
    get_user_or_404(db, user_id)

    # Every personal-data query filters on user_id. Without this one line, one
    # user's list would leak into another's.
    query = (
        db.query(UserMedia)
        .join(UserMedia.media)
        .options(joinedload(UserMedia.media))
        .filter(UserMedia.user_id == user_id)
    )

    if status_filter is not None:
        query = query.filter(UserMedia.status == status_filter.value)
    if media_type is not None:
        query = query.filter(Media.media_type == media_type.value)
    if title:
        # ilike is parameterized by SQLAlchemy; the wildcards are data, not SQL.
        query = query.filter(Media.title.ilike(f"%{title}%"))

    return query.order_by(Media.title).all()


@router.get("/{entry_id}", response_model=EntryRead)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    return get_entry_or_404(db, entry_id)


@router.patch("/{entry_id}", response_model=EntryRead)
def update_entry(entry_id: int, payload: EntryUpdate, db: Session = Depends(get_db)):
    entry = get_entry_or_404(db, entry_id)
    updates = payload.model_dump(exclude_unset=True)

    # Resolve progress against what is already stored, so clearing one field and
    # setting the other is judged on the final state rather than the payload.
    resulting_season = updates.get("current_season", entry.current_season)
    resulting_episode = updates.get("current_episode", entry.current_episode)
    check_progress_against_media(entry.media, resulting_season, resulting_episode)

    for field, value in updates.items():
        setattr(entry, field, value.value if isinstance(value, Status) else value)

    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}/status", response_model=EntryRead)
def update_status(entry_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    entry = get_entry_or_404(db, entry_id)
    entry.status = payload.status.value
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}/progress", response_model=EntryRead)
def update_progress(
    entry_id: int, payload: ProgressUpdate, db: Session = Depends(get_db)
):
    entry = get_entry_or_404(db, entry_id)
    updates = payload.model_dump(exclude_unset=True)

    resulting_season = updates.get("current_season", entry.current_season)
    resulting_episode = updates.get("current_episode", entry.current_episode)
    check_progress_against_media(entry.media, resulting_season, resulting_episode)

    for field, value in updates.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = get_entry_or_404(db, entry_id)
    # Deletes only this user's entry. The shared media row stays, because other
    # users may still have it saved.
    db.delete(entry)
    db.commit()
    return None
