"""Application entry point: creates tables and registers routers."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db

# Importing the models package registers User, Media, and UserMedia on Base so
# create_all() sees all three tables.
from app import models  # noqa: F401
from app.routers import media, recommendations, search, users

# Read .env before anything reads os.environ.
load_dotenv()

# Create the SQLite database file and all tables on startup.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Movie Night Planner",
    description=(
        "Track movies and TV shows, and find what a group of users all want to "
        "watch. Data from TMDB. This product uses the TMDB API but is not "
        "endorsed or certified by TMDB."
    ),
)

# Comma-separated list of allowed frontend origins, e.g.
# CORS_ORIGINS=https://movienightplanner.example,https://www.movienightplanner.example
# Never use "*" in production: the design document requires known origins only.
DEFAULT_DEV_ORIGINS = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_DEV_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(media.router)
app.include_router(recommendations.router)
app.include_router(search.router)


@app.get("/api")
def api_root():
    return {"message": "Movie Night Planner API", "docs": "/docs"}


@app.get("/health")
def health(response: Response, db: Session = Depends(get_db)):
    """Report application and database status."""
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        # Deliberately not returning the exception text: the design document
        # forbids exposing database paths or stack traces to users.
        database = "unavailable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
    }


# Serve the frontend from the app itself, so `uvicorn app.main:app --reload` is the
# only command needed and the browser talks to the API same-origin.
#
# Mounted LAST on purpose: routes are matched in registration order, so /users,
# /media, /search, /recommendations, /docs, and /health all win over this mount.
# html=True makes "/" serve frontend/index.html.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
