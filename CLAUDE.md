# CLAUDE.md

This file provides guidance to Claude Code when working in this repository. It holds standing rules and directions only — current status and design decisions live in the files below.

## What This Project Is

A two-player, turn-based strategy board game, in the style of Stratego — units with hidden ranks, moved on a grid, with combat resolved on collision. Built to learn a Python/FastAPI, cloud-native microservices stack hands-on rather than follow a course passively; not an attempt to compete with existing implementations (e.g. BoardGameArena). Previously built on Rails as a monolith — the game design carries over unchanged, only the implementation stack and system shape have changed.

**This repo is the `game-engine` service**, one piece of a multi-repo system (`bff`, `frontend`, `market`, `platform` — see `docs/architecture.md`'s System architecture section for the full picture and each repo's role). It owns board state, turn/round resolution, combat, and the hidden-information boundary; it does not serve a browser page or hold player-facing auth.

Core technical challenge: hidden information. Each player must only ever receive their own full army plus the opponent's revealed pieces — never the opponent's hidden ranks, even in a payload or event a UI just chooses not to render. See `docs/architecture.md` for the full design.

## Document Map

| File | What it contains |
|---|---|
| `docs/architecture.md` | What this project is, system architecture (multi-repo split), data model, transport design, hidden-information handling, key design decisions |
| `TASKS.md` | MVP scope, phased roadmap, current status, task backlog — scoped to this repo, notes cross-repo dependencies |
| `books.md` | Technical reading list, ordered by project phase |
| `LICENSE` | All Rights Reserved — public repo, no reuse rights granted |

**`TASKS.md` is the single source of truth for status and what to work on next.** When work is completed, started, or rescoped, update `TASKS.md` in the same session — don't leave it stale, and don't duplicate status information back into this file.

## Development Rules

### Teaching & Collaboration Style

Governed by `~/.claude/CLAUDE.md`'s "Teaching & Collaboration Style" section — one ruling for all projects. Not restated here.

### Learning Mode — No Code Generation

Restated from `../CLAUDE.md` (already inherited from the Udemy root, but this is the single most important rule for this repo specifically):

- Claude leads, explains, and points in the right direction. The user writes the code.
- No completing functions, filling in implementations, or writing specs on the user's behalf.
- Pseudocode and general illustrative examples (not tied to the specific problem) are fine to demonstrate a concept.
- Exception: code generation only if explicitly asked for, AND confirmed a second time.

### Explain Before Code

Explain what a piece of code will do and why before giving any implementation guidance. No code dumps without context.

### Tests First (TDD)

Write failing tests before implementation. Tests define the expected behavior. Only enough code to make tests pass. After running the full suite, report exact pass/fail counts.

### Test Against the Endpoint

Endpoint tests (pytest + `httpx.AsyncClient` against the FastAPI app) are the primary test layer — they prove the actual behavior works, not internals. Every endpoint test asserts HTTP status, response shape, and relevant side effects. A move-submission test must also assert what's *absent* from the opposing player's response (unrevealed piece ranks), not just what's present. Mock only genuinely external services, not internal logic.

### Minimal & Readable Code (Sandi Metz Philosophy)

- Each class does one thing; each function does one thing
- Description test: "this does X" — no "and", no "or". If you need one, split it.
- No over-engineering or premature abstraction
- Clear names over comments
- Delete dead code, don't comment it out

### Single-Purpose Tickets

Each ticket in `TASKS.md` does ONE thing, with clear acceptance criteria and no code samples — describe behavior, not implementation.

### Security & Performance Review Gate

Before marking any task done, review it for security vulnerabilities and performance issues — for this project, that includes re-checking that no change accidentally leaks hidden game state, now across a service boundary rather than within a single app.

## Code Editing / Accuracy

Before answering questions about or editing any file, re-read the current file state from disk — never reason from a previously-cached or assumed version.

## Testing Conventions

- pytest + `pytest-asyncio` + `httpx.AsyncClient`
- `factory_boy` for building test data; direct construction for simple cases, factories once persistence or relationships matter
- Minimal mocking — prefer real objects; mock only external services
- Factories with traits for meaningful states, not hand-rolled test objects in every spec

## Documentation

Keep the README and any notes concise — no unrequested caveats, comparisons, or scope beyond what's actually built.

## Commands

### Development Server
| Task | Command |
|------|---------|
| Start server | `uv run uvicorn app.main:app --reload` |

### Testing
| Task | Command |
|------|---------|
| Run all tests | `uv run pytest` |
| Run specific test | `uv run pytest tests/path/to/test_file.py` |

### Database
| Task | Command |
|------|---------|
| Run migrations | `uv run alembic upgrade head` |
| Create a migration | `uv run alembic revision --autogenerate -m "description"` |

### Code Quality
| Task | Command |
|------|---------|
| Lint | `uv run ruff check .` |
| Lint (auto-fix) | `uv run ruff check --fix .` |
