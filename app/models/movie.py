"""SQLAlchemy ORM model for a Movie."""

from sqlalchemy import Column, Date, Integer, String, Text

from app.database import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    overview = Column(Text, nullable=True)
    release_date = Column(Date, nullable=True)
    genres = Column(String, nullable=True)
    poster_path = Column(String, nullable=True)
