# CLAUDE.md

## Project Overview
A platform for users to search for movies, create personal movie lists, and mark movies as watched
or planned to watch. It can also combine multiple users' preferences to recommend a movie to watch
together.

Concretely: users search TMDB for a title, save it to a watch status (`watchlist`, `watching`,
`completed`, `dropped`), record TV progress, and add a personal rating and review. A group
recommendation endpoint takes several users and returns titles their watchlists have in common.

This means the data model is **multi-user**: media metadata is shared, while status, progress,
rating, and review are per-user.

Spec: `MovieNightPlanner-design-document-filled.md`. NOTE — that document is currently written for
a single-user tracker and lists multi-user recommendation in its Won't tier. It must be updated to
match this overview; until then, this file is authoritative on scope.

Still out of scope for M1/M2: AI/LLM-generated recommendations (the group recommendation is a
deterministic overlap query, not a model call), friends/comments/social feeds, and TMDB account
login.

Current Stage: Phase 1 - Design & Contract Setup

## Architecture
- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **External API**: TMDB API (The Movie Database)

### Project Structure
```text
MovieNightPlanner/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   └── services/       # Abstract service layers & contracts
│
├── mcp-server/         # TMDB MCP server (Phase 2)
├── frontend/           # HTML/CSS/JS UI (Phase 3)
├── tests/
│   └── fixtures/       # Mock JSON data for offline development
├── .env.example
├── requirements.txt
├── README.md
├── DESIGN.md
└── CLAUDE.md
```

## Team Roles & Development Boundaries

The rule for `app/routers/`: **whoever owns the data behind a route owns the route.** Local
database routes go to Owner A; the TMDB-backed route goes to Owner B.

- **Owner A (Database/CRUD)**: Responsible for `app/models/`, `app/schemas/`, SQLite data
  constraints, `app/database.py`, and the local-data routers —
  `app/routers/users.py`, `app/routers/media.py`, `app/routers/recommendations.py`,
  `app/routers/stats.py`. Also owns `app/services/media_service.py` and
  `app/services/recommendation_service.py`.
- **Owner B (Catalogue/MCP)**: Responsible for `mcp-server/`, the `app/services/catalogue_service.py`
  abstract layer and its mock/live implementations, external TMDB client connections, and
  `app/routers/search.py` (the only router that talks to TMDB rather than SQLite).
- **Owner C (Frontend/Testing)**: Responsible for `frontend/` UI and all test suites under `tests/`,
  including `tests/fixtures/`.

Shared files that need a heads-up in the group chat before editing, because everyone touches them:
`app/main.py`, `requirements.txt`, `CLAUDE.md`, and the design document.

## Coding Conventions
- **Naming**: Use `snake_case` for function and variable names, `PascalCase` for database models/classes.
- **Data Layout**: Always use Pydantic models (under schemas) for API input validation and explicit JSON responses.
- **Branching Policy**: Each developer must code inside their unique `feature/name-dev` branch to isolate context window changes.

## Common Commands & Run Guide
### Environment Setup
- Activate Virtual Environment: `.venv\Scripts\activate` (Windows)
- Install Dependencies: `pip install -r requirements.txt`

### Execution & Testing
- Start FastAPI Server: `uvicorn app.main:app --reload`
- Inspect LLM Agent Context: `/context`
- Check Model Token Consumption Meter: `/cost`
