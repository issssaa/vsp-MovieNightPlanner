# [Project Name] Design Document

## Overview

One paragraph describing what this project does and who it's for.

## Demo Contract

Fill this in **first**, before the requirements below. It is the promise your project
makes: the one interaction a stranger should be able to try in 30 seconds and remember.
Everything else in this document — the CRUD entities, the MCP server, the tests — exists to
make this one interaction work and to make it trustworthy. If a proposed feature does not
serve the demo contract, it belongs in your Could tier or your Won't tier.

- **Intended audience:** Who is this one interaction for? (Be specific: "a VSP student
  planning a rain-safe Saturday," not "users.")
- **One-sentence problem:** The single problem this interaction solves.
- **Magic moment:** One sentence in the form — *Given this input, the system performs this
  useful transformation, and the user sees this result.* This is the first thing your team
  gets working. (See "Your Magic Moment" in `project-ideas.md` for examples.)
- **Exact demo input → expected output:** The literal input you will type on demo day and the
  literal result you expect back. Write it down now so you can test against it later.
- **Three screens or states you will show:** e.g., empty state → input state → result state.
- **If the external API is unavailable:** What the user sees when the API you wrap is down,
  rate-limited, or slow. ("Nothing" is not an answer — a cached result, a friendly error, or
  seeded sample data all are.)
- **Evidence the result is trustworthy:** What proves the output is correct, not just
  plausible? A test that checks the demo input against the expected output, a validation
  rule, a visible source citation — name at least one.

**Building it in stages.** Several magic moments depend on the external API you will not wrap
until Session 5. That is expected. At **M1**, build a *walking skeleton* of the magic moment:
the full input → output path working end-to-end, with the external call **mocked** or replaced
by seeded data. At **M2**, complete it for real against the live API. You should be able to
demo the magic moment — mocked — the day M1 is due.

## Current Context

- What problem does this solve?
- Who are the target users?
- What existing solutions exist and why are they insufficient?

## Requirements

### Functional Requirements
- [ ] Requirement 1: Description
- [ ] Requirement 2: Description
- [ ] Requirement 3: Description

### Non-Functional Requirements
- Performance: Expected response times, concurrent users
- Security: Authentication, input validation, data protection
- Accessibility: Screen readers, keyboard navigation

## Design Decisions

### 1. [Architecture Choice]

**Decision:** Will use [approach] because:
- Rationale 1
- Rationale 2

**Alternatives considered:**
- Option B: Why rejected
- Option C: Why rejected

### 2. [Technology Choice]

**Decision:** Will use [technology] because:
- Rationale 1
- Rationale 2

## Technical Design

### System Architecture

```
[Client/Frontend] --> [API Layer (FastAPI)] --> [Database (SQLite)]
                                            --> [External APIs via MCP]
```

### Data Models

```python
# Define your core data models here
# Example:
tasks = """
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'todo',
        created_at TEXT DEFAULT (datetime('now'))
    )
"""
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /items | List all items |
| POST | /items | Create new item |
| GET | /items/{id} | Get item by ID |
| PUT | /items/{id} | Update item |
| DELETE | /items/{id} | Delete item |

### MCP Server Design

**External API:** [Which API will your MCP server wrap?]

**Tools to expose:**
1. `tool_name_1` — Description, parameters, return value
2. `tool_name_2` — Description, parameters, return value

**Transport:** STDIO (local) / HTTP (remote)

### File Structure

```
project/
├── app/
│   ├── main.py          # FastAPI entry point
│   ├── db.py            # Database layer
│   ├── routers/         # API endpoints
│   └── services/        # Business logic
├── mcp-server/
│   └── server.py        # MCP server
├── frontend/
│   └── index.html       # Web interface
├── tests/
│   └── test_*.py        # Test files
├── CLAUDE.md            # AI agent context
└── README.md            # Setup and usage docs
```

## Implementation Plan

### Phase 1: Core Application (Week 1)
- [ ] Set up project structure and CLAUDE.md
- [ ] Implement database schema and CRUD operations
- [ ] Build API endpoints
- [ ] Create basic frontend
- [ ] Write initial tests

### Phase 2: MCP Integration (Week 2)
- [ ] Design MCP server tools
- [ ] Implement MCP server
- [ ] Connect MCP server to main application
- [ ] Generate and review test suite with AI
- [ ] Run Semgrep security scan and fix findings

### Phase 3: Polish and Deploy (Week 3)
- [ ] Add remaining features
- [ ] Polish UI/UX
- [ ] Deploy to hosting platform
- [ ] Write documentation
- [ ] Prepare presentation

## Testing Strategy

### Unit Tests
- Test each API endpoint (happy path + error cases)
- Test database operations
- Test MCP server tools

### Integration Tests
- Test MCP server connected to main app
- Test full user workflow (create -> read -> update -> delete)

### Security Testing
- Run Semgrep on all code
- Check for SQL injection, XSS, hardcoded secrets
- Validate all user inputs

## Security Considerations

- [ ] Input validation on all endpoints
- [ ] No hardcoded API keys (use environment variables)
- [ ] SQL parameterized queries (no string concatenation)
- [ ] CORS configuration
- [ ] Rate limiting on external API calls

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MCP Server Quickstart](https://modelcontextprotocol.io/quickstart/server)
- [Semgrep Getting Started](https://semgrep.dev/docs/getting-started/)