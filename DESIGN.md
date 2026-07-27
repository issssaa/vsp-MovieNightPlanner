# DESIGN.md — superseded

This was the first design sketch. It has been **superseded by
[`MovieNightPlanner-design-document-filled.md`](MovieNightPlanner-design-document-filled.md)**,
which is the authoritative spec. Read that file, not this one.

This file is kept only to record where the data model came from and what changed, so nobody
re-proposes a decision that was already made and rejected.

## What this sketch got right

The original three-table shape — `User`, `Movie`, `UserMovie` — is the shape the project actually
uses. Separating shared catalogue metadata from per-user tracking data is what makes the group
recommendation feature a single grouped query. In the final design these became:

| This sketch | Final design | Holds |
|---|---|---|
| `User` | `users` | who is on the instance |
| `Movie` | `media` | shared TMDB metadata, movies **and** TV shows |
| `UserMovie` | `user_media` | one person's status, progress, rating, review |

See Design Decision 2 in the design document for the full rationale.

## What changed, and why

- **The `password` field was removed.** This sketch stored it as a plain `String`. M1 has no
  authentication at all: users are identified by a unique username and nothing else. Storing no
  credential is safer than storing a plaintext one, and password handling does not serve the demo
  contract. See Design Decision 5.
- **TV shows are supported, not just movies.** `media` carries a constrained `media_type`
  (`movie` / `tv`) plus season and episode fields, so `Movie` became `media`.
- **`release_date` became `release_year`,** and `genres` was dropped from M1 — neither is needed by
  the demo contract.
- **`rating` is an integer 1–5, not a float,** and `status` is constrained to
  `watchlist` / `watching` / `completed` / `dropped`.
- **"Recommendations for Tonight" is in scope, but deterministic.** It is a watchlist-overlap query
  across the selected users, not a model or an LLM call. See Design Decision 6.
- **The MCP server wraps the TMDB API,** not "search the database". Its three tools are
  `search_media`, `get_media_details`, and `get_configuration`.
