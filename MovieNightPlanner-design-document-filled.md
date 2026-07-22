# MovieNightPlanner Design Document

## Overview

MovieNightPlanner is a personal movie and TV tracking web application for students and casual viewers who want one place to organize what they plan to watch, are currently watching, have completed, or have dropped. Users search for a title, select the correct movie or TV show, and the application retrieves metadata from The Movie Database (TMDB), including the poster, release year, overview, and media type. Users can then save the title, update its viewing status, record TV progress, add a rating, and write a short review.

## Demo Contract

- **Intended audience:** A student who watches movies and TV shows across different streaming services and wants a simple, platform-independent way to organize their watch history.
- **One-sentence problem:** Viewers often lose track of what they want to watch, what they have completed, and where they stopped in a TV series because their records are scattered across different platforms.
- **Magic moment:** Given a title search and a selected result, the system retrieves the correct TMDB metadata, creates a complete media card, saves it to the selected watch status, and immediately displays it in the user's collection.
- **Exact demo input → expected output:**
  - **Input:** Search for `Dune`, select `Dune (2021)`, choose `Watchlist`, and click `Add`.
  - **Expected output:** A saved card appears showing `Dune`, `2021`, `Movie`, its poster, a short overview, and a `Watchlist` status label. The database stores the selected TMDB ID and media type.
- **Three screens or states you will show:**
  1. Dashboard with empty or existing Watchlist, Watching, Completed, and Dropped sections.
  2. Search results for `Dune`, showing multiple candidate titles with posters, years, and media types.
  3. The saved `Dune (2021)` detail card with its metadata, status controls, rating, and review fields.
- **If the external API is unavailable:** The user sees a friendly error message and may retry. If cached or seeded results exist, the application displays them. The user may also create a manual entry with a title, media type, year, and placeholder poster.
- **Evidence the result is trustworthy:** Each imported item stores its TMDB ID and media type and displays a visible `Data from TMDB` attribution. An automated integration test verifies that the demo input saves the 2021 movie version of *Dune*, rather than another title with the same name.

**Building it in stages.** At **M1**, MovieNightPlanner will implement the complete search → select → save → display workflow using mocked TMDB responses or seeded data. At **M2**, the mock catalogue service will be replaced by an MCP server connected to the live TMDB API without changing the frontend workflow.

## Current Context

- **What problem does this solve?** Streaming services maintain separate watchlists and histories, and they only cover content available on their own platforms. Users who watch across several services need one independent place to track titles, viewing status, TV progress, ratings, and reviews.
- **Who are the target users?** Students and casual viewers who watch both movies and TV shows and want a lightweight personal tracker without a large social network or complicated recommendation system.
- **What existing solutions exist and why are they insufficient?** Streaming-platform watchlists are limited to their own catalogues. Letterboxd is primarily movie-focused, while larger tracking platforms may include more social and discovery features than the target user needs. MovieNightPlanner focuses on a direct workflow: search, select, save, update progress, and review.

## Requirements

### Functional Requirements

- [ ] Users can search TMDB for movies and TV shows by title.
- [ ] Search results show enough information to distinguish similar titles, including poster, media type, and release or first-air year.
- [ ] Users can add a selected title to `watchlist`, `watching`, `completed`, or `dropped`.
- [ ] Users can list and filter saved media by status, media type, or title.
- [ ] Users can view the details of a saved media item.
- [ ] Users can update the watch status of a saved item.
- [ ] Users can update current season and episode progress for TV shows.
- [ ] Users can add or update a personal rating from 1 to 5.
- [ ] Users can add or update an optional written review.
- [ ] Users can delete a saved media item.
- [ ] The system prevents duplicate entries with the same TMDB ID and media type.
- [ ] Users can manually add a title when TMDB is unavailable or has no suitable result.

### Non-Functional Requirements

- **Performance:** Local CRUD requests should normally complete within 500 ms. TMDB-backed searches should normally complete within 3 seconds. The classroom version should support approximately 20 concurrent users.
- **Reliability:** TMDB timeouts, empty results, authentication failures, and rate-limit responses must produce controlled error messages instead of application crashes.
- **Security:** Validate all request bodies, keep the TMDB bearer token in an environment variable, use parameterized database operations, restrict production CORS origins, and never expose secrets or stack traces to users.
- **Privacy:** Store only information required by the tracker. The first version does not require a TMDB user login or access to private TMDB account data.
- **Accessibility:** All form fields must have labels, all major actions must be keyboard-accessible, poster images must have useful alternative text, and status must not be communicated by color alone.
- **Attribution:** The application must display TMDB attribution and the statement: `This product uses the TMDB API but is not endorsed or certified by TMDB.`

## Design Decisions

### 1. Store Local Tracking Data Separately from TMDB

**Decision:** MovieNightPlanner will store selected TMDB metadata together with the user's local status, progress, rating, and review.

**Rationale:**
- Personal tracking data remains available when TMDB is temporarily unavailable.
- The project retains its own meaningful CRUD operations.
- Storing both `tmdb_id` and `media_type` identifies a title reliably even when names are duplicated.
- The application does not require TMDB user authentication.

**Alternatives considered:**
- **Use a TMDB account watchlist directly:** Rejected because it requires user-level authentication and moves the main CRUD data outside the course project's database.
- **Store only the title and search TMDB every time:** Rejected because titles are ambiguous and every page load would depend on the external service.

### 2. Use One Shared Media Table for Movies and TV Shows

**Decision:** Movies and TV shows will share one `media_items` table, distinguished by a constrained `media_type` field.

**Rationale:**
- Most stored fields are shared.
- A single model simplifies listing, filtering, and CRUD implementation.
- TV-only progress fields can remain null for movies.

**Alternatives considered:**
- **Separate `movies` and `tv_series` tables:** Rejected because this duplicates status, rating, review, and external metadata fields.
- **Create season and episode tables in M1:** Rejected because episode-level modelling does not directly serve the demo contract and would expand the project scope unnecessarily.

### 3. Use FastAPI, SQLite, and a Lightweight Frontend

**Decision:** Use FastAPI for the backend, SQLite for local persistence, and HTML/CSS/JavaScript for the frontend.

**Rationale:**
- FastAPI provides request validation and generated API documentation.
- SQLite requires no separate database server and is sufficient for a classroom-scale application.
- A lightweight frontend keeps development effort focused on the core interaction, testing, and usability.

**Alternatives considered:**
- **PostgreSQL:** Suitable for a larger deployed system but unnecessary for the expected scale unless the course environment specifically requires it.
- **A large React frontend:** Rejected for the initial version because framework setup does not directly improve the core demo interaction.

### 4. Use TMDB Application-Level Bearer Authentication

**Decision:** The MCP server will read `TMDB_BEARER_TOKEN` from an environment variable and send it in the authorization header.

**Rationale:**
- Application-level authentication is sufficient for search and details requests.
- No TMDB session or user login is required.
- The token remains on the server and is never exposed to the browser.

**Alternatives considered:**
- **TMDB user authentication:** Rejected because request-token approval and session management are outside the core requirements.
- **API key in query parameters:** Rejected because bearer authentication avoids placing credentials in request URLs and logs.

## Technical Design

### System Architecture

```text
[Browser Frontend]
        |
        | HTTP / JSON
        v
[FastAPI Application] --------> [SQLite Database]
        |
        | MCP tool calls
        v
[MovieNightPlanner MCP Server]
        |
        | HTTPS + Bearer token
        v
[TMDB API]
```

The browser never receives the TMDB token. FastAPI handles input validation, local CRUD, duplicate checking, and user-facing errors. The MCP server handles TMDB requests, response normalization, timeouts, and external-service errors.

### Data Models

```python
media_items = """
    CREATE TABLE media_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tmdb_id INTEGER,
        media_type TEXT NOT NULL
            CHECK (media_type IN ('movie', 'tv')),
        title TEXT NOT NULL,
        original_title TEXT,
        overview TEXT,
        poster_path TEXT,
        release_year INTEGER,
        status TEXT NOT NULL DEFAULT 'watchlist'
            CHECK (status IN ('watchlist', 'watching', 'completed', 'dropped')),
        current_season INTEGER,
        current_episode INTEGER,
        total_seasons INTEGER,
        total_episodes INTEGER,
        rating INTEGER CHECK (rating BETWEEN 1 AND 5),
        review TEXT,
        source TEXT NOT NULL DEFAULT 'tmdb'
            CHECK (source IN ('tmdb', 'manual')),
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        CHECK (
            media_type = 'tv'
            OR (current_season IS NULL AND current_episode IS NULL)
        ),
        UNIQUE (tmdb_id, media_type)
    );
"""
```

Validation rules:

- `tmdb_id` may be null only for manually created items.
- Season and episode values must be zero or greater.
- Progress fields are accepted only for TV shows.
- Ratings must be integers from 1 to 5.
- Reviews are limited to 2,000 characters.
- Duplicate TMDB items return HTTP `409 Conflict`.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Return application and database status |
| GET | `/search?query={title}&media_type={movie\|tv\|all}` | Search TMDB through the MCP server |
| GET | `/media` | List saved media, with optional status, type, and title filters |
| POST | `/media` | Save a selected TMDB result or create a manual entry |
| GET | `/media/{id}` | Get one saved media item |
| PATCH | `/media/{id}` | Update status, progress, rating, or review |
| PATCH | `/media/{id}/status` | Update only the watch status |
| PATCH | `/media/{id}/progress` | Update TV season and episode progress |
| DELETE | `/media/{id}` | Delete a saved item |
| POST | `/media/{id}/refresh` | Refresh TMDB metadata while preserving personal fields |
| GET | `/stats` | Return counts by status and media type plus average rating |

Example create request:

```json
{
  "tmdb_id": 438631,
  "media_type": "movie",
  "status": "watchlist"
}
```

The backend uses the selected TMDB ID to retrieve or verify the title metadata before saving it. It does not blindly trust title, poster, or overview values supplied by the browser.

### MCP Server Design

**External API:** The Movie Database (TMDB) API v3.

**Tools to expose:**

1. `search_media(query, media_type="all", language="en-US", page=1)`  
   Searches movies, TV shows, or both. Returns normalized results containing `tmdb_id`, `media_type`, title, original title, year, poster path, and overview.

2. `get_media_details(tmdb_id, media_type, language="en-US")`  
   Retrieves the details of one movie or TV show. Returns shared metadata and, for TV shows, total seasons and total episodes.

3. `get_configuration()`  
   Retrieves and caches TMDB image configuration used to construct valid poster URLs.

**Transport:** STDIO for local development and course integration. HTTP will only be considered if deployment requires the MCP server to run separately.

Example normalized error:

```json
{
  "error": {
    "code": "TMDB_UNAVAILABLE",
    "message": "Movie data is temporarily unavailable.",
    "retryable": true
  }
}
```

### File Structure

```text
movienightplanner/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── media.py
│   │   ├── search.py
│   │   └── stats.py
│   └── services/
│       ├── media_service.py
│       └── catalogue_service.py
├── mcp-server/
│   ├── server.py
│   ├── tmdb_client.py
│   └── normalizers.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── assets/
│       └── poster-placeholder.svg
├── tests/
│   ├── fixtures/
│   │   └── tmdb_dune_search.json
│   ├── test_media_api.py
│   ├── test_search_api.py
│   ├── test_media_service.py
│   ├── test_mcp_tools.py
│   └── test_demo_contract.py
├── .env.example
├── .gitignore
├── CLAUDE.md
├── README.md
└── requirements.txt
```

## Implementation Plan

### Phase 1: Core Application (Week 1)

- [ ] Set up the repository, project structure, `.gitignore`, `.env.example`, and `CLAUDE.md`
- [ ] Implement the SQLite schema and database initialization
- [ ] Implement media CRUD operations
- [ ] Implement watch-status updates
- [ ] Implement TV progress validation
- [ ] Implement ratings and reviews
- [ ] Define a `CatalogueService` interface
- [ ] Implement a mocked catalogue service
- [ ] Complete the mocked `Dune (2021)` search → select → save → display workflow
- [ ] Build basic Watchlist, Watching, Completed, and Dropped filters
- [ ] Add duplicate and input-error handling
- [ ] Write initial demo-contract and endpoint tests

### Phase 2: MCP Integration (Week 2)

- [ ] Obtain TMDB application credentials
- [ ] Configure `TMDB_BEARER_TOKEN`
- [ ] Implement the MCP server
- [ ] Implement `search_media`
- [ ] Implement `get_media_details`
- [ ] Implement `get_configuration`
- [ ] Switch between mocked and live catalogue services through configuration
- [ ] Handle timeouts, empty results, HTTP 401, HTTP 404, and HTTP 429
- [ ] Cache TMDB image configuration and recent search results
- [ ] Test movie and TV searches with mocked HTTP responses
- [ ] Run one controlled live smoke test
- [ ] Generate and review tests with AI
- [ ] Run Semgrep and fix relevant findings

### Phase 3: Polish and Deploy (Week 3)

- [ ] Add poster cards, loading states, error states, and empty states
- [ ] Add keyboard focus states and responsive layout
- [ ] Add viewing statistics
- [ ] Add metadata refresh and placeholder posters
- [ ] Add TMDB attribution and a credits page
- [ ] Deploy the frontend and backend
- [ ] Configure production CORS and secrets
- [ ] Write setup, architecture, API, and troubleshooting documentation
- [ ] Rehearse the exact demo flow
- [ ] Prepare seeded fallback data for demo day

### Won't Tier for the Initial Version

- [ ] AI-generated recommendations
- [ ] Friends, comments, or social feeds
- [ ] Automatic Netflix, Disney+, or Prime history import
- [ ] A database record for every individual episode
- [ ] Episode-level reviews
- [ ] Live streaming-provider availability by country
- [ ] TMDB account synchronization

## Testing Strategy

### Unit Tests

- Validate allowed watch statuses
- Validate rating range
- Reject TV progress fields for movies
- Reject negative season or episode values
- Normalize movie and TV responses into the same result format
- Build valid poster URLs from image configuration and poster paths
- Preserve personal fields when refreshing TMDB metadata
- Convert TMDB timeouts and error responses into controlled application errors

### API Tests

- Create, read, update, filter, and delete media items
- Return `404` for unknown local IDs
- Return `409` for duplicate TMDB items
- Return `422` for invalid status, rating, or progress values
- Allow `tmdb_id` to be null for valid manual entries

### Integration Tests

- Test the complete demo workflow:
  1. Search for `Dune`
  2. Select the 2021 movie result
  3. Add it to `watchlist`
  4. Retrieve it from `/media`
  5. Verify title, year, media type, poster path, status, source, and TMDB ID
- Test FastAPI-to-MCP integration
- Mock TMDB HTTP calls during automated tests
- Test unavailable-API, cached-result, and manual-entry fallback paths
- Test the full CRUD workflow: create → read → update → delete

### Security Testing

- Run Semgrep on Python and frontend code
- Verify that `.env` and real tokens are excluded from Git
- Test overly long and malicious search or review input
- Confirm parameterized ORM/database operations
- Confirm that production CORS does not allow arbitrary origins
- Confirm that errors do not expose tokens, request headers, stack traces, or database paths

## Security Considerations

- [ ] Validate all input and enforce field-length limits
- [ ] Store `TMDB_BEARER_TOKEN` only in environment variables or the deployment secret manager
- [ ] Add `.env` to `.gitignore` and provide only `.env.example`
- [ ] Use an ORM or parameterized SQL operations
- [ ] Restrict production CORS to known frontend origins
- [ ] Set timeouts on every TMDB request
- [ ] Respect HTTP `429` responses and avoid bulk scraping
- [ ] Cache only public media metadata
- [ ] Never cache credentials or authorization headers
- [ ] Escape review text when rendering it to prevent XSS
- [ ] Return generic external-service errors to users
- [ ] Log only safe diagnostic information on the server
- [ ] Display TMDB attribution without implying endorsement

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MCP Server Quickstart](https://modelcontextprotocol.io/quickstart/server)
- [Semgrep Getting Started](https://semgrep.dev/docs/getting-started/)
- [TMDB Getting Started](https://developer.themoviedb.org/reference/getting-started)
- [TMDB Application Authentication](https://developer.themoviedb.org/docs/authentication-application)
- [TMDB Movie Search](https://developer.themoviedb.org/reference/search-movie)
- [TMDB TV Search](https://developer.themoviedb.org/reference/search-tv)
- [TMDB Search and Details Workflow](https://developer.themoviedb.org/docs/search-and-query-for-details)
- [TMDB Image Basics](https://developer.themoviedb.org/docs/image-basics)
- [TMDB FAQ and Attribution](https://developer.themoviedb.org/docs/faq)
