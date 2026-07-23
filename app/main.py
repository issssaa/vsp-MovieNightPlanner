"""Application entry point: creates tables and registers routers."""

from fastapi import FastAPI

from app.database import Base, engine
from app.models import movie as movie_model  # noqa: F401  (ensures model is registered)
from app.routers import movies

# Create the SQLite database file and all tables on startup.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Night Planner")

app.include_router(movies.router)


@app.get("/")
def root():
    return {"message": "Movie Night Planner API"}
