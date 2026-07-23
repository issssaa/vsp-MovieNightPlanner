"""Database configuration: engine, session factory, and declarative base."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database stored as a file in the project root.
SQLALCHEMY_DATABASE_URL = "sqlite:///./movies.db"

# `check_same_thread=False` is required for SQLite when used with FastAPI,
# because a single connection may be shared across threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Session factory; each request gets its own session via `get_db`.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all ORM models inherit from.
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
