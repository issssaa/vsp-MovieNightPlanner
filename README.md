# MovieNightPlanner Design Document

## Overview

MovieNightPlanner is a movie and TV tracking web application for students and casual viewers who want one place to organize what they plan to watch, are currently watching, have completed, or have dropped. Users search for a title, select the correct movie or TV show, and the application retrieves metadata from The Movie Database (TMDB), including the poster, release year, overview, and media type. Users can then save the title, update its viewing status, record TV progress, add a rating, and write a short review.

Because housemates and friends often want to watch something together, the application also supports multiple users on one instance and can combine several users' watchlists to recommend titles they all want to see. This group recommendation is a deterministic overlap query over saved watchlists, not a machine-learning or LLM recommender.

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
- **Secondary flow shown after the magic moment:** With `Dune` on both `alice`'s and `bob`'s watchlists, selecting both users on the Movie night screen returns `Dune` as the one title they both want to see. This is deliberately *not* the magic moment — the single-user search → save → display path stays the 30-second interaction, and the group overlap is shown as the payoff once two lists exist.

**Building it in stages.** At **M1**, MovieNightPlanner will implement the complete search → select → save → display workflow using mocked TMDB responses or seeded data. At **M2**, the mock catalogue service will be replaced by an MCP server connected to the live TMDB API without changing the frontend workflow.

## Current Context

- **What problem does this solve?** Streaming services maintain separate watchlists and histories, and they only cover content available on their own platforms. Users who watch across several services need one independent place to track titles, viewing status, TV progress, ratings, and reviews. A second, related problem is choosing what to watch as a group: when several people each keep their own list, finding the overlap is a manual, argument-prone process.
- **Who are the target users?** Students and casual viewers who watch both movies and TV shows and want a lightweight tracker without a large social network or a complicated recommendation system. Typically a small group — housemates, a couple, or a few friends — sharing one instance.
- **What existing solutions exist and why are they insufficient?** Streaming-platform watchlists are limited to their own catalogues and cannot compare lists across accounts. Letterboxd is primarily movie-focused, while larger tracking platforms may include more social and discovery features than the target user needs. MovieNightPlanner focuses on a direct workflow: search, select, save, update progress, review, and find the overlap between a few users' watchlists.

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
- [ ] The instance supports several named users, and each user's status, progress, rating, and review are independent.
- [ ] A user's saved list shows only that user's own entries.
- [ ] Given two or more users, the system returns the titles that appear on all of their watchlists, so the group can pick one to watch together.
- [ ] The group recommendation reports clearly when there is no overlap, rather than returning an arbitrary title.

### Non-Functional Requirements

- **Performance:** Local CRUD requests should normally complete within 500 ms. TMDB-backed searches should normally complete within 3 seconds. The classroom version should support approximately 20 concurrent users.
- **Reliability:** TMDB timeouts, empty results, authentication failures, and rate-limit responses must produce controlled error messages instead of application crashes.
- **Security:** Validate all request bodies, keep the TMDB bearer token in an environment variable, use parameterized database operations, restrict production CORS origins, and never expose secrets or stack traces to users. Every read and write of personal tracking data must be scoped to a user id so one user's entries are never returned under another user's list.
- **Privacy:** Store only information required by the tracker. The first version does not require a TMDB user login or access to private TMDB account data. Users are identified by a chosen username only; no password, email address, or other personal data is collected. Because there is no authentication in M1, users on one instance are **not** protected from each other — the instance is designed for a small, mutually trusting group, and this limitation is documented for the user rather than hidden. Group recommendation reveals watchlist overlap to the participating users, which is the point of the feature and is stated in the UI.
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

### 2. Separate Shared Catalogue Metadata from Per-User Tracking Data

**Decision:** Use three tables. `media` holds one row per title — both movies and TV shows, distinguished by a constrained `media_type` field. `users` holds one row per person on the instance. `user_media` is a join table holding one row per (user, title) pair, carrying that user's status, progress, rating, and review.

**Rationale:**
- Movies and TV shows still share a single table, because most catalogue fields are common to both and one model keeps search, listing, and filtering simple.
- Catalogue metadata is a property of the title, not of the person. Storing it once means two users who both save *Dune* share one row instead of duplicating the poster, overview, and year.
- Personal fields are a property of the pair, so they belong on the join row. A `UNIQUE (user_id, media_id)` constraint expresses "a user saves a title at most once" directly in the schema.
- The group recommendation becomes a single grouped query over `user_media` instead of a self-join that has to match on `tmdb_id`.
- A TMDB metadata refresh updates one `media` row and automatically benefits every user, with no risk of touching anyone's personal fields.

**Trade-off accepted:** The rule "progress fields are only valid for TV shows" spans two tables — `media_type` lives on `media` while `current_season` lives on `user_media` — so SQLite cannot enforce it with a single `CHECK`. It is enforced in the Pydantic/service layer instead and covered by a unit test. This is the main cost of the split and is accepted deliberately.

**Alternatives considered:**
- **One `media_items` table with a `user_id` column:** Rejected because catalogue metadata would be duplicated per user, a refresh would have to update N rows, and the group overlap query would need a self-join on `tmdb_id`. It is a smaller change but pushes complexity into every later query.
- **Separate `movies` and `tv_series` tables:** Rejected because this duplicates the shared catalogue and tracking fields and doubles every query.
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

### 5. Identify Users by Username Only, With No Authentication in M1

**Decision:** Users are created with a unique username and are selected explicitly. The client passes a `user_id` with each tracking request. There is no password, session, or token.

**Rationale:**
- The feature that needs multiple users is group recommendation, which needs *identity* (whose list is this?) but not *authentication* (can you prove it?).
- Storing passwords correctly — hashing, salting, reset flows, session management — is a large amount of work that does not serve the demo contract.
- Collecting no password and no email means there is no credential to leak.
- The target deployment is a small trusted group on one instance.

**Consequence, stated plainly:** Any client can read or modify any user's list by passing that user's id. This is acceptable for a classroom-scale trusted-group tool and is documented in the README, but it is the first thing that would need to change before any real deployment.

**Alternatives considered:**
- **Full password authentication in M1:** Deferred. It is the natural next step after the demo contract works, and the schema is designed so that adding a `password_hash` column to `users` does not require changing any other table.
- **A plaintext `password` column** (as sketched in the original `DESIGN.md`): Rejected outright. Storing plaintext passwords is worse than storing none, because users reuse passwords across services.
- **Single hardcoded user:** Rejected because it cannot support group recommendation at all.

### 6. Compute Group Recommendations by Deterministic Watchlist Overlap

**Decision:** Given a set of user ids, return the titles that appear on every one of those users' watchlists, ranked by the group's average rating where ratings exist. No model, no external recommendation service.

**Rationale:**
- The result is explainable: "all three of you have this on your watchlist" is a reason a user can verify, which satisfies the trustworthiness requirement.
- It is a single grouped SQL query, so it is fast and easy to test against fixed data.
- It has no external dependency, so it keeps working when TMDB is unavailable.
- It cannot hallucinate a title that nobody saved.

**Alternatives considered:**
- **LLM or ML-based recommendation:** Rejected for this version. It would add an unverifiable output to a project whose demo contract is built on verifiable results, and it remains in the Won't tier.
- **Genre-similarity scoring across users' completed titles:** Rejected as scope creep; it also produces suggestions no user has expressed interest in, which is harder to defend in a demo than a plain overlap.
- **Returning a union with a match count instead of a strict intersection:** Kept as a documented fallback for when the strict intersection is empty, rather than as the default, so the primary answer stays unambiguous.

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

Three tables: `users` (who), `media` (shared catalogue metadata), and `user_media` (one person's relationship to one title).

```python
users = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        display_name TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
"""

# One row per title. Shared by every user who saves it.
media = """
    CREATE TABLE media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tmdb_id INTEGER,
        media_type TEXT NOT NULL
            CHECK (media_type IN ('movie', 'tv')),
        title TEXT NOT NULL,
        original_title TEXT,
        overview TEXT,
        poster_path TEXT,
        release_year INTEGER,
        total_seasons INTEGER,
        total_episodes INTEGER,
        source TEXT NOT NULL DEFAULT 'tmdb'
            CHECK (source IN ('tmdb', 'manual')),
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (tmdb_id, media_type)
    );
"""

# One row per (user, title). Carries everything personal.
user_media = """
    CREATE TABLE user_media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL
            REFERENCES users(id) ON DELETE CASCADE,
        media_id INTEGER NOT NULL
            REFERENCES media(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'watchlist'
            CHECK (status IN ('watchlist', 'watching', 'completed', 'dropped')),
        current_season INTEGER
            CHECK (current_season IS NULL OR current_season >= 0),
        current_episode INTEGER
            CHECK (current_episode IS NULL OR current_episode >= 0),
        rating INTEGER CHECK (rating BETWEEN 1 AND 5),
        review TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (user_id, media_id)
    );
"""
```

Group recommendation query — the titles every listed user has on their watchlist:

```sql
SELECT m.id, m.title, m.media_type, m.release_year, m.poster_path,
       AVG(um.rating) AS group_avg_rating
FROM user_media AS um
JOIN media AS m ON m.id = um.media_id
WHERE um.user_id IN (:user_ids)
  AND um.status = 'watchlist'
GROUP BY um.media_id
HAVING COUNT(DISTINCT um.user_id) = :user_count
ORDER BY group_avg_rating DESC NULLS LAST, m.title;
```

Validation rules:

- `tmdb_id` may be null only for manually created items (`source = 'manual'`).
- Ratings must be integers from 1 to 5.
- Reviews are limited to 2,000 characters.
- Season and episode values must be zero or greater — enforced by `CHECK`.
- Progress fields are accepted only when the joined `media.media_type` is `tv`. This constraint spans two tables, so it is enforced in the service/schema layer and covered by a unit test rather than by SQLite.
- Saving a title a user has already saved returns HTTP `409 Conflict` (`UNIQUE (user_id, media_id)`). Two *different* users saving the same title is normal and must succeed.
- Importing a TMDB title that already exists in `media` reuses the existing row instead of inserting a duplicate.
- `SQLite` does not enforce foreign keys unless `PRAGMA foreign_keys = ON` is set per connection; the application must enable it so `ON DELETE CASCADE` actually applies.
- Requests for a `user_id` that does not exist return HTTP `404`.
- Group recommendation requires at least two distinct user ids, otherwise HTTP `422`.

### API Endpoints

In every path below, `{id}` is a `user_media.id` — the identifier of one user's saved entry, not the shared catalogue row. Endpoints that read or write personal data require a `user_id`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Return application and database status |
| GET | `/users` | List users on this instance |
| POST | `/users` | Create a user from a unique username |
| GET | `/users/{user_id}` | Get one user |
| GET | `/search?query={title}&media_type={movie\|tv\|all}` | Search TMDB through the MCP server |
| GET | `/media?user_id={id}` | List that user's saved media, with optional status, type, and title filters |
| POST | `/media` | Save a selected TMDB result or manual entry to a user's list |
| GET | `/media/{id}` | Get one saved entry |
| PATCH | `/media/{id}` | Update status, progress, rating, or review |
| PATCH | `/media/{id}/status` | Update only the watch status |
| PATCH | `/media/{id}/progress` | Update TV season and episode progress |
| DELETE | `/media/{id}` | Remove the entry from that user's list (the shared `media` row remains) |
| POST | `/media/{id}/refresh` | Refresh TMDB metadata on the shared row while preserving all users' personal fields |
| GET | `/recommendations?user_ids=1,2,3` | Titles on every listed user's watchlist, ranked by group average rating |
| GET | `/stats?user_id={id}` | Counts by status and media type plus average rating, for one user |

Example create request:

```json
{
  "user_id": 1,
  "tmdb_id": 438631,
  "media_type": "movie",
  "status": "watchlist"
}
```

The backend uses the selected TMDB ID to retrieve or verify the title metadata before saving it. It does not blindly trust title, poster, or overview values supplied by the browser. If a `media` row for that `(tmdb_id, media_type)` already exists — because another user saved it earlier — the existing row is reused and only a new `user_media` row is created.

Example group recommendation response:

```json
{
  "user_ids": [1, 2],
  "count": 1,
  "results": [
    {
      "media_id": 7,
      "title": "Dune",
      "media_type": "movie",
      "release_year": 2021,
      "poster_path": "/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
      "on_watchlist_of": [1, 2],
      "group_avg_rating": null
    }
  ]
}
```

When the intersection is empty, the endpoint returns `count: 0` with an empty `results` array and a `message` explaining that these users have no watchlist titles in common — it never substitutes an arbitrary title.

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
│   ├── database.py             # engine, SessionLocal, Base, get_db
│   ├── models/                 # package, one module per table
│   │   ├── user.py
│   │   ├── media.py
│   │   └── user_media.py
│   ├── schemas/                # package, mirrors models/
│   │   ├── user.py
│   │   ├── media.py
│   │   └── user_media.py
│   ├── routers/
│   │   ├── users.py
│   │   ├── media.py
│   │   ├── search.py
│   │   ├── recommendations.py
│   │   └── stats.py
│   └── services/
│       ├── media_service.py
│       ├── recommendation_service.py
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
│   ├── test_users_api.py
│   ├── test_search_api.py
│   ├── test_media_service.py
│   ├── test_recommendations.py
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
- [ ] Implement the SQLite schema (`users`, `media`, `user_media`) and database initialization
- [ ] Enable `PRAGMA foreign_keys = ON` per connection
- [ ] Implement user create and list endpoints
- [ ] Implement media CRUD operations scoped to a user
- [ ] Reuse an existing `media` row when a second user saves the same title
- [ ] Implement watch-status updates
- [ ] Implement TV progress validation across the `media` / `user_media` join
- [ ] Implement ratings and reviews
- [ ] Implement the group recommendation overlap query and empty-overlap response
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
- [ ] Add a user switcher and a create-user form
- [ ] Add a "Movie night" screen: pick two or more users, show the overlap, handle the empty-overlap case
- [ ] Add viewing statistics
- [ ] Add metadata refresh and placeholder posters
- [ ] Add TMDB attribution and a credits page
- [ ] Deploy the frontend and backend
- [ ] Configure production CORS and secrets
- [ ] Write setup, architecture, API, and troubleshooting documentation
- [ ] Rehearse the exact demo flow
- [ ] Prepare seeded fallback data for demo day

### Won't Tier for the Initial Version

- [ ] AI- or ML-generated recommendations. The group recommendation **is** in scope, but only as the deterministic watchlist-overlap query described in Design Decision 6 — no model inference, no genre-similarity scoring, no suggesting titles nobody saved.
- [ ] Password authentication, sessions, and access control between users (see Design Decision 5)
- [ ] Friends, follow relationships, comments, or social feeds. Group recommendation is an explicit, ad-hoc list of user ids, not a persistent social graph.
- [ ] Automatic Netflix, Disney+, or Prime history import
- [ ] A database record for every individual episode
- [ ] Episode-level reviews
- [ ] Live streaming-provider availability by country
- [ ] TMDB account synchronization

## Testing Strategy

### Unit Tests

- Validate allowed watch statuses
- Validate rating range
- Reject TV progress fields for movies — the cross-table rule SQLite cannot enforce
- Reject negative season or episode values
- Normalize movie and TV responses into the same result format
- Build valid poster URLs from image configuration and poster paths
- Preserve every user's personal fields when refreshing shared TMDB metadata
- Convert TMDB timeouts and error responses into controlled application errors
- Overlap query returns only titles on *all* listed users' watchlists
- Overlap query ignores titles whose status is `watching`, `completed`, or `dropped`
- Overlap query returns an empty result, not an arbitrary title, when there is no intersection
- Overlap ranking places higher group average ratings first and sorts unrated titles last
- A single user id, or a repeated user id, is rejected rather than trivially "matching"

### API Tests

- Create, read, update, filter, and delete media items
- Create and list users; reject a duplicate username with `409`
- Return `404` for unknown local IDs and for an unknown `user_id`
- Return `409` when the *same* user saves the same title twice
- Two *different* users saving the same title both succeed and share one `media` row
- `GET /media?user_id=A` never returns user B's entries
- Deleting user A's entry leaves user B's entry for the same title intact
- Return `422` for invalid status, rating, or progress values
- Return `422` for a recommendation request with fewer than two distinct user ids
- Allow `tmdb_id` to be null for valid manual entries

### Integration Tests

- Test the complete demo workflow:
  1. Search for `Dune`
  2. Select the 2021 movie result
  3. Add it to `watchlist`
  4. Retrieve it from `/media`
  5. Verify title, year, media type, poster path, status, source, and TMDB ID
- Test the group recommendation workflow:
  1. Create users `alice` and `bob`
  2. Both add `Dune (2021)` to `watchlist`; only `alice` adds a second title
  3. `GET /recommendations?user_ids=alice,bob` returns exactly `Dune`, not the title only `alice` saved
  4. Verify one shared `media` row backs both users' entries
- Test FastAPI-to-MCP integration
- Mock TMDB HTTP calls during automated tests
- Test unavailable-API, cached-result, and manual-entry fallback paths
- Test the full CRUD workflow: create → read → update → delete

### Security Testing

- Run Semgrep on Python and frontend code
- Verify that `.env` and real tokens are excluded from Git
- Test overly long and malicious search or review input
- Confirm parameterized ORM/database operations, including the `user_ids IN (...)` list in the overlap query, which must be bound rather than string-formatted
- Confirm every personal-data query filters on `user_id`
- Confirm that a review written by one user is escaped when rendered on a shared group screen
- Confirm that production CORS does not allow arbitrary origins
- Confirm that errors do not expose tokens, request headers, stack traces, or database paths

## Security Considerations

- [ ] Validate all input and enforce field-length limits
- [ ] Scope every personal-data read and write to a `user_id`; never return one user's entries under another's list
- [ ] Never store a password. `users` holds a username and optional display name only (see Design Decision 5)
- [ ] Document in the README that M1 has no authentication and any client may act as any user
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
