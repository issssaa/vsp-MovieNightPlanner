"""CRUD endpoints for movies."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.movie import Movie
from app.schemas.movie import MovieCreate, MovieRead, MovieUpdate

router = APIRouter(prefix="/movies", tags=["movies"])


@router.post("", response_model=MovieRead, status_code=status.HTTP_201_CREATED)
def create_movie(payload: MovieCreate, db: Session = Depends(get_db)):
    # Reject duplicate tmdb_id with 409 Conflict.
    existing = db.query(Movie).filter(Movie.tmdb_id == payload.tmdb_id).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Movie with tmdb_id {payload.tmdb_id} already exists",
        )

    movie = Movie(**payload.model_dump())
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


@router.get("", response_model=List[MovieRead])
def list_movies(db: Session = Depends(get_db)):
    return db.query(Movie).all()


@router.get("/{movie_id}", response_model=MovieRead)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
        )
    return movie


@router.patch("/{movie_id}", response_model=MovieRead)
def update_movie(movie_id: int, payload: MovieUpdate, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
        )

    # Only update fields the client actually sent.
    updates = payload.model_dump(exclude_unset=True)

    # If tmdb_id is being changed, make sure it stays unique.
    new_tmdb_id = updates.get("tmdb_id")
    if new_tmdb_id is not None and new_tmdb_id != movie.tmdb_id:
        clash = db.query(Movie).filter(Movie.tmdb_id == new_tmdb_id).first()
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Movie with tmdb_id {new_tmdb_id} already exists",
            )

    for field, value in updates.items():
        setattr(movie, field, value)

    db.commit()
    db.refresh(movie)
    return movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
        )
    db.delete(movie)
    db.commit()
    return None
