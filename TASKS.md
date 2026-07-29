# Tasks

Single source of truth for status and what to work on next. Update this file in the same session as any work that completes, starts, or gets rescoped.

This repo is the `game-engine` service (see `docs/architecture.md`'s System architecture table). Tickets below are scoped to this repo; companion repos (`bff`, `frontend`, `market`, `platform`) get
their own `TASKS.md` once they're created, and a ticket here notes when it depends on one of them existing.

The ticket structure below (Why/Industry context/How it works/Read first/Common pitfalls, the retrieval checkpoint, reference-don't-repeat) is defined once, canonically, in the global
`~/.claude/CLAUDE.md`'s "Ticket/Task Breakdown Structure" section — full path `/Users/nseglins/.claude/CLAUDE.md` (a hidden dotfolder, not shown by default in Finder/most file trees, but a normal
file your editor can open directly given that path). It applies across all projects, learning or professional; this file is just where it's actually written down for this one, per that section's
own rule.

Each task below has:
- a ***Why:*** line — the reason this ticket exists at all, not just what it asks for. If the reason isn't obvious, it's written out; if it's a deeper architectural rationale, it points at the
  specific line in `docs/architecture.md` rather than repeating it.
- an ***Industry context:*** line, where a named technology or practice is central to the ticket — not why *this project* uses it, but what's generally worth knowing about it in the industry: where it
  came from, what problem it was actually built to solve, common alternatives, and real tradeoffs. The goal of these tickets isn't checking a box — it's being able to explain and argue the choice
  afterward, not just recite that it worked here.
- a ***How it works:*** line — the practical mechanics: how the pieces actually connect and behave at runtime (what talks to what, what's created once vs. per-request, where config values live and
  why). This is different from *What it is* (a definition) or *Why we use it* (the rationale) — it's the wiring diagram, concrete enough to answer "so what do I actually build, and why does it look
  like that."
- a **Read first** line pointing at whatever explains the concept best — a book (added to `books.md` if it's not there yet), official documentation, or a well-regarded write-up (a respected
  engineering blog, Medium, dev.to). No format is preferred over another; the bar is "does this actually explain it well," not "is it a book." Some tasks are pure setup/administration with no useful
  reading at all; those say so rather than forcing a fit.
- a ***Common pitfalls:*** line, only where a real, already-hit gotcha exists for that specific ticket — not filled in artificially where nothing's actually gone wrong. Capturing a mistake once we've
  actually made it (a scoping error, a stale-environment surprise, a config landing somewhere it shouldn't) means future-you doesn't rediscover it the hard way a second time.

**When a ticket repeats an already-covered concept** (a second REST endpoint, a second State-pattern ticket), keep the same five-part structure — every ticket still gets a *What it is*/*Why we use
it*/*How it works*/*What breaks without it*/*Industry context* — but the content can be a brief pointer back to the ticket that already covered it ("same pattern as X's Industry context"), rather than
a full fresh explanation. The structure stays consistent; the depth doesn't need to.

**Retrieval checkpoint:** before checking a ticket's box, explain its *How it works* flow back in your own words (out loud, in writing, or to me) — not just "it works," but the actual mechanism.
Being asked to retrieve something is a stronger test than having just read it, and it's the cheapest point to catch a gap, before it's buried under the next ticket.

**Practical Object-Oriented Design in Ruby (POODR)** isn't tied to one ticket — read it before starting Phase 1. CLAUDE.md's "Minimal & Readable Code (Sandi Metz Philosophy)" rule comes straight from
this book and governs every class written from the first model onward, not just the service-object extraction in "Resolve combat" below.

## Current Status

Log of major status changes, newest first. Add a new dated entry at the top when something meaningful completes, starts, or gets rescoped — don't edit an old entry to reflect new state, since the
point is to be able to read the project's history top-down.

### 2026-07-20 — Phase 0 ticket 1 complete
`pyproject.toml` now has FastAPI, uvicorn, SQLAlchemy (async), asyncpg, Alembic, and Pydantic as runtime dependencies (previously only the dev group was populated). A minimal `app = FastAPI()` in
`main.py` boots via `uv run uvicorn main:app --reload`. No models, no routes, no Postgres connection yet — that's the rest of Phase 0.

### 2026-07-17 — Stack pivot: Rails → Python/FastAPI/asyncio microservices
All Rails scaffolding removed; project restructured as a multi-repo microservices system (see `docs/architecture.md`) — this repo is the `game-engine` service. `uv init` run. Game design unchanged by
the pivot: a simultaneous-turn, fog-of-war game inspired by both Stratego and Kriegsspiel. Combat-resolution math, win condition, army selection, and timer-expiry behavior are still open design
questions (see `docs/architecture.md`'s Open design questions) — tickets depending on one are marked **[BLOCKED]** and shouldn't start until resolved.

## MVP Definition (Phase 1)

MVP scope is deliberately layered, not flat: this phase builds the simplest possible playable vertical slice — full visibility both ways, fixed identical armies, no setup phase — so there's a working
move → combat → winner loop before tackling the project's actual hard problem. Hidden information and fog of war are Phase 2, not Phase 1, by design.

Two players can play a full game against each other, from a fixed starting position through move submission and combat resolution to a declared winner. Both players see the entire board and every
opponent unit's full stats at all times — no hidden information, no fog of war. Both start with an identical, hard-coded army already placed in a fixed formation; there is no setup phase — the game
begins `in_progress` the moment both players have joined. No matchmaking, no accounts, no polish beyond that. This is intentionally not the finished game — it's the smallest slice that's actually
playable end to end, with hidden info and fog of war layered on in Phase 2.

---

## Phase 0 — Project Setup

- [x] **Initialize the project with uv.** `uv init`, add FastAPI, uvicorn, SQLAlchemy (async) + asyncpg, Alembic, and Pydantic as dependencies via `uv add`. Confirm a minimal FastAPI app boots locally
  via `uvicorn`.
  - *Why:* each package here has a distinct, non-overlapping job in the request lifecycle — leaving any one out breaks a specific thing, not "the setup" in general.
    - **FastAPI**
      - *What it is:* a Python library for building web APIs — you write a function per route (e.g. "create a game"), tell FastAPI which URL/HTTP method triggers it, and it handles turning an incoming
        request into a call to your function and your function's return value into an HTTP response. This is the same job Rails' `routes.rb` + controllers did together, just one library instead of
        two.
      - *Why we use it:* it's the framework every endpoint in this service is built on.
      - *How it works:*
        - The flow: request arrives → route matching (path + method) → path/query param + body validation → your function runs → return value serialized (through a response model, if declared).
        - **Route matching** — `@app.get("/games/{id}")` registers your function against that path/method; the `app` object is really just this registry, nothing more.
        - **Validation happens before your function runs** — params and body are checked against their declared types first, so your function only ever sees already-valid data.
      - *What breaks without it:* you'd be hand-writing HTTP parsing, routing, and response formatting from scratch — solved problems FastAPI gives you for free.
      - *Industry context:*
        - *Origin:* created 2018 by Sebastián Ramírez, built *on top of* two existing libraries (Starlette for the async web layer, Pydantic for validation) rather than reinventing them. Its breakout
          feature was auto-generating interactive API docs (the `/docs` page) straight from your type hints — most competitors don't do this out of the box.
        - *Alternatives:* Flask (older, sync-first, far larger ecosystem, much more manual/explicit — nothing happens unless you write it), Django REST Framework (batteries-included, but tied to
          Django's ORM/admin — heavier than needed for a small service like this one).
        - *Tradeoffs:* versus Flask, FastAPI's type-hint-driven validation and dependency injection are powerful but more implicit — more "magic" to learn, less obvious what's happening just from
          reading a route function.
          - *What this means concretely:* FastAPI lets a route function just declare, as a parameter, something it needs — e.g. a database session — and FastAPI supplies it automatically before the
            function runs, without you ever writing the line that actually creates it. That's **dependency injection**: instead of a function fetching what it needs itself (Flask-style:
            `db = get_db_connection()` written explicitly in the body, so you see exactly where `db` came from), it just declares the need in its parameter list (FastAPI-style:
            `db = Depends(get_db)`) and trusts the framework to call `get_db()` and hand the result over before the function ever runs. Reading the FastAPI version alone doesn't tell you where `db`
            came from — you have to already know the `Depends(...)` convention to trace it, which is exactly the "more magic, less obvious" tradeoff described above.
    - **uvicorn**
      - *What it is:* FastAPI only knows *what to do* once a request arrives — it has no idea how to open a network socket or listen on a port. uvicorn is the separate program that does that
        networking work, and for every request it receives, calls into your FastAPI app to ask "what's the response?" This is Python's equivalent of Puma in Rails: Rails defines your app, Puma is
        what's actually bound to a port listening for connections.
      - *Why we use it:* FastAPI needs an actual running process serving it — `app = FastAPI()` alone doesn't listen for anything.
      - *How it works:*
        - The flow: TCP connection arrives → uvicorn parses the raw HTTP bytes → translated into the ASGI calling convention → your FastAPI `app` is invoked with that.
        - **Your FastAPI code never touches a socket** — uvicorn is the only thing that speaks raw HTTP; your routes just get called with already-parsed request data.
        - **`--reload`** separately watches your source files and restarts this whole process on a change — "the dev server picked up my edit" is literally uvicorn killing and respawning itself.
      - *What breaks without it:* nothing is listening on any port, so no request can ever reach your app, no matter how correct the code is.
      - *Industry context:*
        - *Origin:* uvicorn is an **ASGI** server — ASGI (Asynchronous Server Gateway Interface) is the async-capable successor to **WSGI**, the older standard that's powered Flask and Django for two
          decades and still does for anything sync. "ASGI vs. WSGI" is a common Python-web interview-level distinction worth being able to explain.
        - *Alternatives:* Hypercorn (another ASGI server, more complete HTTP/2 support), Daphne (the original ASGI server, built for Django Channels).
        - *Tradeoffs:* in real production deployments, uvicorn is often run *underneath* Gunicorn (as a worker type) rather than alone, since Gunicorn's process management (restarting crashed workers,
          running several in parallel) is more battle-tested than uvicorn's own.
    - **SQLAlchemy (async)**
      - *What it is:* a library that lets you describe database tables as Python classes (a `Game` class instead of a `games` SQL table) and query/save data with Python instead of writing SQL by hand
        — SQLAlchemy translates your Python into SQL behind the scenes. This is Python's closest equivalent to Rails' ActiveRecord, minus most of Rails' extra "magic" conventions.
      - *Why we use it:* every read/write of a `Game`/`Player`/`Piece` goes through this instead of raw SQL scattered through route handlers.
      - *How it works:*
        - The flow: Python class mapped to a table → build a query object (`select(Game).where(...)`) → execute via a `Session` → SQL sent to Postgres → rows returned → mapped into `Game` instances.
        - **The mapping** (Python class ↔ table) happens once, declaratively, when you define the class — it doesn't re-run per query.
        - **The `Session`** doesn't hold a database connection the whole time — it borrows one from the engine's pool only while actively doing work, then returns it.
      - *What breaks without it:* every database interaction becomes a hand-written SQL string, a manually-managed connection, and manual row-to-object conversion — slow to write and an easy way to
        introduce a SQL injection bug under deadline pressure.
      - *Industry context:*
        - *Origin:* the dominant Python SQL toolkit, first released in 2006 — older than Django's ORM in its current form. It's really two layers in one package: "Core" (a lower-level SQL expression
          builder) and the "ORM" (the class-mapping layer this project actually uses). Version 2.0 (2023) was a deliberate, fairly disruptive rewrite to unify the sync and async APIs, so a lot of
          tutorials/Stack Overflow answers still show older, differently-shaped "1.x-style" code — worth recognizing so outdated examples don't confuse you.
        - *Alternatives:* Django's ORM (simpler, but tightly coupled to Django itself), Tortoise ORM (async-native from the start, syntax closer to Django's).
        - *Tradeoffs:* or no ORM at all — some teams deliberately write raw SQL at scale for query performance and predictability, a real, sometimes-correct position, not just "ORMs are strictly
          better."
    - **asyncpg**
      - *What it is:* SQLAlchemy doesn't actually know how to speak to Postgres over the network by itself — it needs a lower-level library ("driver") that knows Postgres's specific message format and
        handles the raw bytes going back and forth. asyncpg is that driver, built specifically to work with Python's `async`/`await` instead of waiting around blocked.
      - *Why we use it:* while one request is waiting on a slow database query, an async driver lets the server go handle a *different* request in the meantime instead of sitting idle doing nothing.
      - *How it works:*
        - The flow: SQLAlchemy's async engine → delegates to asyncpg → asyncpg opens the socket and speaks Postgres's wire protocol → raw response parsed back into Python values → handed to
          SQLAlchemy.
        - **You never call asyncpg directly** — your code only ever calls SQLAlchemy's own async API (`await session.execute(...)`); asyncpg sits one layer beneath, invisible unless something breaks.
      - *What breaks without it:* using an ordinary (synchronous) driver like `psycopg2` instead would mean that while any one request waits on the database, the entire server process freezes and
        can't handle any other request at all — which defeats the reason this stack is async in the first place.
      - *Industry context:*
        - *Origin:* written in large part by Yury Selivanov, who also worked on asyncio's own internals — known for being unusually fast.
        - *Alternatives:* psycopg2 (the long-standing standard Postgres driver, sync-only), psycopg3 (its modern successor, which does support async and is a closer competitor to asyncpg than psycopg2
          is).
        - *Tradeoffs:* asyncpg's speed comes partly from skipping PEP 249 (Python's standard "DB-API" interface most drivers implement for interchangeability) — so it isn't a drop-in swap for other
          PEP 249-compliant tools, and you're relying on SQLAlchemy to abstract that difference away rather than talking to asyncpg directly.
    - **Alembic**
      - *What it is:* a tool that records changes to your database's structure (adding a table, adding a column) as small, numbered script files, each one saying how to apply the change and how to
        undo it. This is the direct equivalent of Rails' `db/migrate` files and `rails db:migrate` — Alembic pairs with SQLAlchemy the way ActiveRecord migrations pair with Rails.
      - *Why we use it:* as the data model changes (a new field on `Piece`, say), you need one repeatable way to apply that change everywhere — your laptop, CI, production.
      - *How it works:*
        - The flow: `alembic upgrade head` → checks the `alembic_version` tracking table (Alembic creates this itself) → runs every un-applied `upgrade()` in order → updates the tracking table.
        - **The migration chain** — each file is a small script with `upgrade()`/`downgrade()` and a reference to the previous migration's ID, so Alembic always knows the correct order to apply them
          in.
        - **Nothing runs twice** — the tracking table is exactly what prevents re-applying a migration that's already been run.
      - *What breaks without it:* schema changes happen by hand, aren't tracked anywhere, and can't be reliably reproduced across environments or by a second person.
      - *Industry context:*
        - *Origin:* written by Mike Bayer — the same author as SQLAlchemy — specifically to pair with it, rather than being a general-purpose migration tool bolted on afterward.
        - *Alternatives:* Django bundles migrations directly into its own ORM instead of a separate package; other ecosystems solve the same problem with Flyway or Liquibase (Java-world), or
          hand-written numbered SQL files (simpler, but no built-in "undo").
        - *Tradeoffs:* the underlying idea — "migrations as version control for your schema" — is worth knowing independent of Alembic specifically, since it recurs under a different name in nearly
          every backend stack; the tool changes, the concept doesn't.
    - **Pydantic**
      - *What it is:* a library for describing the *shape* data should have (e.g. "a Move has a unit ID and a destination, nothing else") as a Python class, which then automatically checks incoming
        data against that shape and rejects anything that doesn't match. FastAPI uses these same classes to control exactly what fields go out in a response, too.
      - *Why we use it:* it's what makes "reject an illegal move with a generic error" and, later, "the opponent's response never contains a hidden field" actually enforced by the framework rather
        than something you have to remember to check by hand in every route.
      - *How it works:*
        - The incoming flow: raw JSON → passed to your `BaseModel` subclass's constructor → each field checked against its declared type → a validation error (→ HTTP 422) or a validated object
          handed to your route.
        - The outgoing flow: your route's return value → passed through the declared `response_model` → only its fields get serialized, even if the object you returned internally had more on it.
        - **The outgoing flow is the actual enforcement mechanism** behind Phase 2's hidden-rank filtering later — a structural guarantee, not a convention you have to remember to follow.
      - *What breaks without it:* you'd be manually validating incoming JSON and manually building outgoing JSON everywhere — and a forgotten manual check is exactly how a hidden rank would
        accidentally leak later (see Phase 2).
      - *Industry context:*
        - *Origin:* built on Python's type hints (a language feature that matured over many releases) — Pydantic's core idea is using those hints not just for editor autocomplete, but to actually
          validate data at runtime. Version 2 (2023) rewrote its core validation engine in Rust for a major speed jump.
        - *Alternatives:* stdlib `dataclasses` (structure only, no validation), `marshmallow` (an older, more manual validation/serialization library that predates Pydantic's type-hint-driven
          approach).
        - *Tradeoffs:* Pydantic is used widely outside FastAPI too — a general data-validation library, not FastAPI-specific. The Rust rewrite is itself a recognizable pattern: a Python library
          reaching for a compiled language once pure-Python performance becomes the bottleneck, the same story behind pandas' C internals or Ruff being written in Rust.
  - *Common pitfalls:*
    - **`uv add --dev` doesn't cover runtime dependencies.** Running only the `--dev` command (for pytest/ruff/etc.) leaves `dependencies` empty in `pyproject.toml` — `uv run uvicorn ...` then fails
      with "Failed to spawn: uvicorn" because it was never actually installed. Both commands are needed, separately.
    - **`app = FastAPI()` has to be module-level, not inside a function.** uvicorn imports your module and looks for `app` as a top-level attribute — a variable created inside `def main():` doesn't
      exist until that function is called, and uvicorn never calls it. This is a module-scope-vs-function-scope issue, not an uvicorn-specific one.
    - **A freshly-installed CLI tool not being found right after install.** If `uv` (or anything else) was installed in an already-open terminal session, that session's `PATH` was captured before the
      install happened — a new terminal tab, or `source ~/.zshrc`, picks up the change; the existing one won't until then.
  - *Read first:* **Python Concurrency with asyncio** — enough to understand why the app and its dependencies are async-first, before writing the first route.
  - *Learning notes:* `docs/task_learning_notes/phase_0_project_setup/01_initialize_project_with_uv.md` — the actual debugging/discussion behind this ticket (uv scoping, module-scope bug, stale
    PATH, dependency injection).

- [ ] **Set up Postgres via SQLAlchemy (async) + Alembic.** Configure an async database connection and confirm a first (empty) Alembic migration runs against a local Postgres instance. This service
  owns its own database — see `docs/architecture.md`'s data-ownership rule.
  - *What it is:* Postgres (PostgreSQL) is a relational database — software that stores structured data in tables with defined relationships between them, and lets many concurrent connections
    query and modify that data safely at the same time. It runs as its own separate server process your app connects to over a network socket, unlike SQLite, which is just a file your app reads
    directly.
  - *Why we use it:*
    - **Postgres, not SQLite** — SQLite locks the whole file under concurrent writes, a problem the moment two games are being played at once (see `docs/architecture.md`'s "Postgres, not SQLite"
      bullet for the full rationale).
    - **This service owning its own database** — rather than sharing one with a future `market` service, is what makes the multi-repo split actually mean something instead of being a monolith with
      extra network hops (see `docs/architecture.md`'s "One database per service" bullet).
  - *How it works:*
    - The flow, startup to per-request: `.env` (`DATABASE_URL`) → `Settings` (read once, at startup) → `AsyncEngine` (created once) → `Session` (created per request) → Postgres server.
    - **`.env`** holds one connection string, bundling driver, user, host, port, and database name (`postgresql+asyncpg://user@host:port/dbname`) — the one thing that changes per environment
      (laptop, CI, and production all point at different servers).
    - **`Settings`** (via `pydantic-settings`) reads that file once, when the app boots, into a typed object kept in memory for the rest of the process's life — not re-read per request.
    - **`AsyncEngine`** is created once, from `settings.database_url`, at startup. Engines manage a connection pool and are expensive to create, cheap to reuse — there's exactly one for the app's
      entire lifetime, never one per request.
    - **`Session`** is created fresh for each incoming request (via a FastAPI dependency like `Depends(get_db)`), borrows a connection from the engine's pool, runs that request's queries, then
      closes — cheap and short-lived by design, unlike the engine above it.
    - *One constant, not five:* SQLAlchemy expects a single URL string, so `DATABASE_URL` alone is enough — splitting it into `DB_HOST`, `DB_PORT`, `DB_USER`... would just mean reassembling them
      back into a string in code, for no benefit at this project's scale. (Some larger setups do split it — e.g. a secrets manager injecting the password separately for rotation — solving a problem
      this project doesn't have.)
  - *What breaks without it:* without a real database, this service would need to invent its own way to persist and safely query game state under concurrent access — reinventing transactions,
    indexing, and concurrency control badly and slowly instead of using tools that have solved these problems for decades.
  - *Industry context:*
    - *Origin:* PostgreSQL, first released in 1996 — one of the oldest actively-developed open-source relational databases, known for strict SQL-standards compliance and a reputation for extensibility
      (custom types, extensions like PostGIS for geodata).
    - *Alternatives:* MySQL/MariaDB (historically more common for simple web apps, weaker at complex queries and JSON handling for most of its history, though it's closed much of that gap),
      CockroachDB (Postgres-wire-compatible but built for horizontal scaling across multiple machines).
    - *Tradeoffs:* Postgres is a full client-server database requiring its own running process to manage — SQLite's biggest advantage (zero setup, just a file) is exactly what you give up by choosing
      Postgres. Worth it here because concurrent games writing moves is precisely the case SQLite handles badly (see the Why above).
  - *Common pitfalls:*
    - **A local Postgres server's data directory ending up inside this repo.** If Postgres.app's "location" is pointed anywhere inside `learn_rails/`, the data directory is untracked and *not*
      excluded by `.gitignore` — a careless `git add -A` would try to commit raw binary database files. Keep the data directory outside any project folder entirely.
    - **Port 5432 already being in use.** If another local Postgres instance is already running (a different project, a background service), Postgres.app will fail to start on the default port —
      give this project's instance its own port (e.g. `5433`) rather than fighting over 5432, and remember every client tool (`psql`, `createdb`, the app's connection URL) needs that port passed
      explicitly, since they all assume 5432 unless told otherwise.
  - *Read first:* **SQLAlchemy 2 In Practice** (Miguel Grinberg) — Chapter 7, "Asynchronous SQLAlchemy," covers the async engine/session setup directly. No book covers Alembic specifically, so for
    migrations go straight to Alembic's own ["Using asyncio with Alembic"](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic) cookbook entry — note the `-t async`
    flag on `alembic init`, easy to miss, which produces a different template than the default (sync) one.
  - *Learning notes:* `docs/task_learning_notes/phase_0_project_setup/02_setup_postgres_sqlalchemy_alembic.md` — the actual debugging/discussion behind this ticket (port conflicts, the
    client-server database model, the `Settings`/engine/session debugging, and a full detour into the async "function coloring" problem via this ticket's own Read first).

- [ ] **Set up pytest + httpx for request-style specs.** Add `pytest`, `pytest-asyncio`, `httpx` (for `AsyncClient` against the FastAPI app), and `factory_boy` (per CLAUDE.md's Testing Conventions).
  Confirm `pytest` runs (even with zero tests).
  - *Why:*
    - **pytest-asyncio**
      - *What it is:* a plugin that teaches pytest (the test runner) how to run `async def` test functions. A normal Python function runs straight through top to bottom; an `async def` function is
        written to pause and resume (e.g. while waiting on a database call), and pytest has no built-in idea how to drive that pause/resume cycle on its own — this plugin adds it.
      - *Why we use it:* your FastAPI routes are `async def` functions, so testing them properly means calling them the same way.
      - *How it works:*
        - The flow: `async def test_...()` → marked (`@pytest.mark.asyncio`) or auto-applied (`asyncio_mode = "auto"`) → wrapped in its own event loop → awaited to completion → pass/fail decided.
        - **Without the plugin**, pytest treats the coroutine object itself as the test's result — the test "passes" without its body ever actually running.
      - *What breaks without it:* an `async def test_...()` either errors outright or silently doesn't run its body the way you'd expect, since plain pytest can't execute it correctly.
      - *Industry context:*
        - *Origin:* pytest itself is the dominant Python test framework, largely having replaced the stdlib `unittest` (more verbose, class-based, Java-flavored) — its plugin ecosystem, of which this
          is one of thousands of plugins, is a big reason for that dominance.
        - *Alternatives:* `anyio`'s own pytest plugin, which supports multiple async backends (asyncio and trio) rather than being asyncio-only.
        - *Tradeoffs:* no real downside at this project's scale — pytest-asyncio is the standard, unopinionated choice for an asyncio-only codebase like this one; `anyio`'s plugin only earns its keep
          if you ever need backend-agnostic async support.
    - **httpx's `AsyncClient`**
      - *What it is:* a library for making HTTP requests from Python. Its `AsyncClient` can talk directly to your FastAPI app object in memory — simulating a real request without opening an actual
        network port or starting a real server — while still exercising your app the same async way a real server would call it.
      - *Why we use it:* this is what CLAUDE.md's "Test Against the Endpoint" actually means in practice — sending a simulated request into the app and checking the real response, the same way Rails'
        request specs hit routes rather than calling model methods directly.
      - *How it works:*
        - The flow: `AsyncClient(app=app)` → hooks into your FastAPI app's ASGI interface directly (no real socket) → `await client.post(...)` drives a real request through your actual
          routing/validation/response logic, in-process → a real response object comes back to assert against.
      - *What breaks without it:* you'd be left testing individual functions in isolation, which CLAUDE.md explicitly says is *not* the primary test layer here — a passing unit test doesn't prove the
        actual HTTP behavior works end to end.
      - *Industry context:*
        - *Origin:* written explicitly as a modern successor to `requests` — Python's hugely popular, long-standing HTTP client — adding async support while deliberately keeping a very similar,
          familiar API.
        - *Alternatives:* `aiohttp` (an older, more established async HTTP client/server library, with a less `requests`-like API).
        - *Tradeoffs:* httpx is generally considered the more modern, ergonomic choice today, but `aiohttp` still has a much larger installed base in older codebases — expect to see it a lot if you
          read other people's Python projects.
    - **factory_boy**
      - *What it is:* a library for defining, once, "how to build a valid test `Game`/`Player`/`Piece`" as a reusable factory, instead of constructing the full object by hand inside every test. It's
        the direct Python equivalent of Rails' FactoryBot — same idea, same lineage (factory_boy was ported from Ruby's original `factory_girl`, later renamed FactoryBot).
      - *Why we use it:* CLAUDE.md's Testing Conventions call for factories with traits for meaningful states (e.g. "a game already in progress," "a piece that's already revealed") — this is the tool
        that provides that.
      - *How it works:*
        - The flow: define a `Factory` subclass with default field values (`status = "in_progress"`) → call it in a test (`GameFactory()`) → a real row is built with those defaults → override just
          what matters for that test (`GameFactory(status="finished")`).
      - *What breaks without it:* every test needing a database record hand-rolls its own setup code, which duplicates across the suite and quietly drifts out of sync as the model changes.
      - *Industry context:*
        - *Origin:* the Python port of Ruby's `factory_girl` (thoughtbot's gem, later renamed FactoryBot in 2017) — factory_boy's name is a deliberate pun on the original Ruby name, not a coincidence.
          Worth knowing the ancestry runs Ruby → Python here, unlike SQLAlchemy/Alembic/pytest above, which have no Rails lineage at all.
        - *Alternatives:* plain pytest fixtures (hand-rolled, no shared "recipe" concept), `model_bakery` (a similar factory library, but specific to Django's ORM).
        - *Tradeoffs:* factory_boy adds a small amount of setup/learning overhead versus just hand-writing objects in each test — it only pays off once the suite is big enough that the duplication it
          avoids actually starts to hurt.
  - *Read first:* **Python Testing with pytest** — the fixtures/async-test chapter, so config choices here are deliberate.

- [ ] **Add a Dockerfile for local containerization.** A minimal image that runs the FastAPI app via uvicorn — the basis for both local docker-compose use and the eventual GKE deploy.
  - *What it is:* Docker packages this service together with everything it needs to run (the Python interpreter, installed dependencies, system libraries) into a single portable image, which then
    runs identically on your laptop, in CI, or in production — the same image, not just "the same code."
  - *Why we use it:* building this now, rather than waiting for the Phase 3 deploy ticket, means every ticket from here on can be sanity-checked in the same environment that will eventually run in
    production. A container-specific bug (a missing system library, a path assumption that only holds on your laptop) is cheap to catch here and expensive to discover for the first time during an
    actual deploy.
  - *How it works:*
    - The flow: `Dockerfile` instructions (base image → copy dependency files → install deps → copy app code → set start command) → each becomes a cached layer → `docker build` → an image →
      `docker run` → an isolated container.
    - **Layer ordering matters** — installing dependencies before copying your app code means editing a line of app code doesn't invalidate the dependency-install layer's cache, keeping rebuilds fast.
    - **A container isn't a VM** — it uses the host kernel's namespaces/cgroups to only see the filesystem/processes the image gives it, rather than running its own separate kernel.
  - *What breaks without it:* without a container image, "works on my machine" has no guarantee of meaning "works anywhere else" — a missing system library or OS-level difference can silently break
    the app somewhere it was never tested, and there's no single artifact to actually hand to Kubernetes later.
  - *Industry context:*
    - *Origin:* Docker (Solomon Hykes, 2013) didn't invent containers — Linux's own `cgroups` and namespaces predate it by years — it made using them dramatically easier via one consistent CLI and
      image format.
    - *Alternatives:* Podman (a daemonless alternative with a largely drop-in-compatible CLI), containerd (what Docker itself runs on under the hood, and what Kubernetes talks to directly without
      necessarily needing "Docker" installed at all).
    - *Tradeoffs:* worth knowing a container isn't a lightweight VM — there's no separate OS kernel involved, which is why one machine can run far more containers than VMs, but also why containers
      share the host kernel: a real security-boundary difference from VMs, relevant given this project's security-conscious framing.
  - *Read first:* **Docker Deep Dive** — image-building fundamentals chapter.

- [ ] **Add the `LICENSE` file.** All Rights Reserved text, per the decision noted in `CLAUDE.md`'s Document Map.
  - *Why:* this is a public repo. Without an explicit license, whether the code can legally be reused by anyone who finds it is ambiguous — "All Rights Reserved" just makes explicit what's already the
    default, removing that ambiguity.
  - *Read first:* none — this is administrative, not technical.

## Phase 1 — MVP: Core Game Loop

Full visibility both ways, fixed identical armies, no setup phase. See MVP Definition above.

- [ ] **Create a game with a fixed starting army.** A player starts a new game and receives a shareable code/ID for the second player to join; both players are assigned an identical, hard-coded army
  in a fixed starting formation, and the game begins `in_progress` immediately — no setup phase, no player-driven placement or army selection (see Phase 4 for those, once designed). Acceptance: two
  players can both be attached to the same `Game` record via that code, with no third player able to join, and both start with the same fixed roster already placed on the board.
  - *What it is:* REST models an API around nouns (resources) rather than verbs — a "game" is a thing that exists at its own URL, and standard HTTP methods (`POST` to create, `GET` to read) act on
    it, instead of each action getting its own custom-named endpoint.
  - *Why we use it:* this is the smallest slice that produces a real, shared object two players are actually attached to — every later ticket (moves, combat, win detection) needs a `Game` to operate
    on, so it has to exist first regardless of what game rules end up being decided.
  - *How it works:*
    - The flow: `POST /games` → parsed + validated against a "create game" schema → a new `Game` row created via SQLAlchemy → response includes its generated ID/code.
    - **That ID is the game's whole identity from then on** — every later request (joining, submitting moves) references it in its own URL or payload; nothing else about "which game" gets passed
      around separately.
  - *What breaks without it:* without treating "a game" as a resource with its own identity, every action needs its own bespoke endpoint and URL scheme invented from scratch, and nothing about the
    API's shape is predictable from one endpoint to the next.
  - *Industry context:*
    - *Origin:* `POST`-to-create-a-resource, returning an identifier the client uses for everything after, is the core idea of **REST** (Representational State Transfer) — a style described in Roy
      Fielding's 2000 PhD dissertation, not a FastAPI feature. FastAPI doesn't enforce RESTfulness; it just makes it convenient to follow.
    - *Alternatives:* RPC-style APIs (verbs in the URL, e.g. `POST /createGame`, `POST /submitMove`, instead of resources), or GraphQL (one endpoint, the client specifies exactly what data shape it
      wants back).
    - *Tradeoffs:* REST's resource-oriented style tends to age well and map cleanly onto CRUD-shaped operations like this one, but doesn't always fit an action like "submit move orders" as naturally
      as a pure RPC verb would — worth noticing that friction when it comes up rather than forcing every action into REST dogma.
  - *Read first:* FastAPI's own ["First Steps"](https://fastapi.tiangolo.com/tutorial/first-steps/) tutorial — covers path operations and the request/response cycle this ticket is built from
    directly.
  - *Learning notes:* `docs/task_learning_notes/phase_1_mvp_core_game_loop/01_create_a_game_with_a_fixed_starting_army.md` — theoretical basis prepared before starting (resource identity/UUID
    decision, test-isolation setup).

- [ ] **Submit move orders for a round, with a round timer.** A player can queue movement orders for any subset of their own units during the round's countdown timer (each unit capped by its own
  movement allowance), then submit the batch. Acceptance: illegal orders (insufficient movement allowance remaining, moving an immobile unit) are rejected with a generic error; a submitted batch stays
  invisible to the opponent until the round resolves.
  - *What it is:* the Command pattern means representing "do this action" as a plain data object (what unit, what destination) instead of immediately executing a function — the object itself can
    be validated, stored, queued, or replayed before (or instead of) actually being applied.
  - *Why we use it:* modeling a queued move as a first-class object (rather than a bag of params) up front is what makes both this ticket's own validation and Phase 4's replay ticket tractable
    later — retrofitting that structure after moves are already scattered through ad-hoc code is much more expensive than starting with it.
  - *How it works:*
    - The flow: a move is submitted → validated and stored as its own object → held (not applied) until the round timer expires → every player's stored batch resolves together.
    - **"Receive an order" and "apply an order" are two separate steps**, mediated by that stored object — exactly what makes "wait for both players" and Phase 4's replay both possible without
      restructuring anything later.
  - *What breaks without it:* without a first-class move object, queuing multiple orders before the round resolves, validating them before applying, and replaying them later (Phase 4) all have to
    be bolted on after the fact, onto code that was never structured to support any of them.
  - *Industry context:*
    - *Origin:* modeling an action as an object instead of executing it immediately is the **Command pattern**, one of the original Gang-of-Four design patterns (1994) — the same underlying idea
      behind Redux actions in frontend JS, a Git commit, or a database transaction log.
    - *Alternatives:* just calling a function directly and applying its effect immediately — simpler, but it loses the ability to queue, validate-before-applying, undo, or replay, all of which this
      project actually needs.
    - *Tradeoffs:* a Command object adds a layer of indirection versus a plain function call. Worth it here because queuing/validation/replay are real requirements for this ticket and Phase 4 — not
      because "patterns are good" in the abstract.
  - *Read first:* **Game Programming Patterns** — the Command chapter.
  - *Learning notes:* `docs/task_learning_notes/phase_1_mvp_core_game_loop/02_submit_move_orders_for_a_round.md` — theoretical basis prepared before starting (the queued-`Move`-table shape, the
    round-timer mechanism options, the race condition to decide ahead of time).
  - *Blocked on:* timer-expiry behavior (auto-submit the queued-so-far batch vs. forced no-op) — see Open design questions in `docs/architecture.md`.

- [ ] **Self-play sandbox mode.** A game where the same authenticated player is registered as both armies, for solo rules/tactics practice without a second human or any bot. Acceptance: a player can
  create a sandbox game with `player_one_id == player_two_id` set to their own ID, submit move orders for either army through the same move-submission endpoint used elsewhere, and both armies' full
  state (no hidden rank, no fog of war) is visible in their own response.
  - *What it is:* the same `Game`/move-submission machinery from the previous two tickets, with one relaxed constraint — normally two different players are each registered to one army; a sandbox game
    registers one player to both.
  - *Why we use it:* solo rules/tactics practice doesn't require an opponent that plays *well* — only that legal orders exist for both sides. A human controlling both armies (like playing chess
    against yourself) satisfies that fully, with no scoring function or decision-making logic involved at all; a heuristic bot was considered and deliberately rejected as unnecessary work for this
    need.
  - *How it works:*
    - The flow: `POST /games` with a sandbox flag → both army slots assigned to the requesting player's own ID → moves for either army submitted and validated through the exact same
      move-submission endpoint every other game uses.
    - **No new authorization logic is needed** — the existing rule ("you may only submit orders for the army you're registered as controlling") already permits this, because it's still true in a
      sandbox game that the submitter controls the army they're submitting for. This is a permission relaxation at the data level (who's registered to what), not a new code path.
    - Hidden rank and fog of war (Phase 2) don't apply here: those rules exist to stop an *opponent* from seeing your hidden state — in self-play there is no separate opponent, so there's nothing for
      the rule to protect against. Showing the player everything is correct, not a leak.
  - *What breaks without it:* solo rules or tactics practice otherwise requires a second human being available, even though that's not actually necessary for this need.
  - *Industry context:*
    - *Origin:* "hotseat" or self-play modes are a long-standing convention in board/strategy games (chess, most digital wargames) predating any AI-opponent feature — solving "practice alone" by
      relaxing turn ownership, not by building an opponent.
    - *Alternatives:* a heuristic AI opponent that submits moves on its own — considered and rejected for this project; it requires the submitted moves to be *good*, not merely legal, which is
      meaningfully more work than this ticket's authorization relaxation, for a need this ticket already covers.
    - *Tradeoffs:* none of real weight — this is close to free once game creation and move submission exist, since it reuses their authorization logic unchanged.
  - *Read first:* no dedicated reading — this ticket is a direct, small extension of the two tickets immediately above it; re-read their own `Read first` entries if the resource-identity or
    move-submission mechanics need a refresher.
  - *Learning notes:* `docs/task_learning_notes/phase_1_mvp_core_game_loop/03_self_play_sandbox_mode.md`.

- [ ] **[BLOCKED] Resolve combat.** Moving into conflict with an opponent's unit — via a direct attack order, a crossed path, or both units arriving on the same square (resolved via the bounce-back
  rule) — triggers a battle. Acceptance criteria can't be written until the combat-resolution math (HP/Attack/Defence formula) is decided — see Open design questions in `docs/architecture.md`. Do not
  start implementation until that's resolved.
  - *What it is:* a service object is a plain class whose only job is one piece of business logic — here, resolving a battle — instantiated, given what it needs, and asked to do exactly that one
    thing, rather than that logic living inside a route handler or a `Game`/`Piece` model method.
  - *Why we use it:* combat is where two players' independent, simultaneous move batches actually collide — without it, "submit moves" and "declare a winner" have nothing connecting them.
  - *How it works:*
    - The flow: round resolution needs an outcome → instantiates something like `CombatResolver(attacker, defender)` → it applies the (eventually-decided) combat math → returns/persists the result.
    - **It knows nothing about HTTP, FastAPI, or how it was called** — just the two pieces involved — which is what makes it directly unit-testable with plain Python objects, no request cycle
      required.
  - *What breaks without it:* combat-resolution logic ends up scattered across route handlers and models, making it hard to test in isolation and easy to accidentally duplicate or diverge between
    the places it's needed.
  - *Industry context:*
    - *Origin:* pulling business logic out of a route handler or model into its own object is often called a **service object** (Rails world) or **application service** (Domain-Driven Design
      terminology) — the general principle: framework entry points should stay thin, and logic complex enough to need its own tests deserves its own class.
    - *Alternatives:* a "fat controller" (all logic in the route handler) or a "fat model" (all logic on the `Game`/`Piece` classes) — both common, real anti-patterns, not hypothetical ones.
    - *Tradeoffs:* an extra class for logic that could technically fit in fewer lines elsewhere — the payoff is testability and CLAUDE.md's "one thing" rule, not raw line count.
  - *Read first:* **Dive Into Design Patterns** and **Practical Object-Oriented Design in Ruby (POODR)** — on extracting a focused service-layer object. Battle resolution is business logic that
    doesn't belong in a route handler or model.
  - *Learning notes:* `docs/task_learning_notes/phase_1_mvp_core_game_loop/04_resolve_combat.md` — the service-object shape prepared ahead of the still-open combat-math design question.

- [ ] **[BLOCKED] Detect win conditions.** The win condition itself is an open design question (Flag-capture equivalent vs. something else) — see Open design questions in `docs/architecture.md`. Do
  not start implementation until that's resolved.
  - *What it is:* the State pattern means giving a thing (here, a `Game`) an explicit, named current state (e.g. `in_progress`, `finished`) and defining exactly which transitions between states are
    legal, rather than inferring "is this game still playable?" from scattered conditions elsewhere.
  - *Why we use it:* without an explicit terminal state, a finished game would keep silently accepting moves — this is what turns "the game is over" into an enforced guarantee instead of something
    the UI just happens to assume.
  - *How it works:*
    - The flow: a round resolves → a check evaluates the (eventually-decided) win condition → if met, `Game.status` transitions to `finished`.
    - **Every route that could accept a move checks `status` first** and rejects the request if the game's already finished — `status` is the single source of truth every other piece of code
      defers to, not something inferred independently in multiple places.
  - *What breaks without it:* without an explicit state machine, "is the game over" ends up checked inconsistently in different places, and it's easy for a code path to accidentally accept a move
    against a game that should already be finished.
  - *Industry context:*
    - *Origin:* an explicit "what states can this thing be in, and what transitions are legal" model is the **State pattern**, another Gang-of-Four pattern — the same underlying concept as a traffic
      light, a TCP connection, or an order-fulfillment pipeline: nameable states, enforced legal transitions between them.
    - *Alternatives:* scattered boolean flags (`is_finished`, `is_in_progress`) checked ad hoc wherever relevant — the common default this pattern specifically replaces, easy to reach for without
      deciding to.
    - *Tradeoffs:* a formal state machine is more setup than a boolean flag for a genuinely simple case. Worth it here because "finished" needs to be an enforced guarantee (no further moves accepted
      anywhere), not just a display detail.
  - *Read first:* **Game Programming Patterns** — the State chapter, specifically the "terminal state" framing (a state-machine guard, not an ad-hoc `if`).
  - *Learning notes:* `docs/task_learning_notes/phase_1_mvp_core_game_loop/05_detect_win_conditions.md` — the `Enum`-backed status field and guard-clause pattern prepared ahead of the still-open
    win-condition design question.

- [ ] **Publish a round-resolution event.** When a round resolves, this service publishes an event (Pub/Sub) with the outcome. Since MVP has no hidden information yet, one event body is fine for both
  players — this gets split into per-player-filtered events in Phase 2. Acceptance: a test confirms an event is published containing the resolved round's outcome.
  - *What it is:* event-driven architecture means a service announces "this happened" (an event) without knowing or caring who's listening, and any other service that cares subscribes to hear about
    it — as opposed to the publisher calling every interested party directly.
  - *Why we use it:* this is the seam the future `bff` repo will consume to push live updates to a browser connection. Building the publishing mechanism now, even in its simplest unfiltered form,
    means Phase 2 only has to change *what's in* the event, not invent how events get published from scratch.
  - *How it works:*
    - The flow: round resolves → a message describing the outcome is constructed → published to a named topic (GCP Pub/Sub) → the call returns immediately, before anything consumes it.
    - **This service never knows or waits for who's listening** — any future consumer (the `bff`, eventually) subscribes to that same topic independently; this service's only job is publishing a
      correct message.
  - *What breaks without it:* without a publish mechanism, every future consumer (the `bff`, eventually a notifications service) would need this service to call it directly and by name, meaning
    game-engine would need to know about and be modified for every new consumer that ever gets added.
  - *Industry context:*
    - *Origin:* publishing a fact ("this happened") for other interested parties to react to, without the publisher knowing or caring who's listening, is **event-driven architecture** — GCP Pub/Sub is
      one implementation of a much older, general idea also implemented by Kafka, RabbitMQ, and AWS SNS/SQS.
    - *Alternatives:* the publisher directly calling every interested service's API instead — tighter coupling, since the publisher then needs to know who all its consumers are, and breaks if a
      consumer happens to be down at that moment. That's exactly the problem message brokers exist to avoid.
    - *Tradeoffs:* event-driven systems trade that tight coupling for eventual consistency and a harder-to-trace request flow — a bug can be "somewhere in this chain of events" rather than one obvious
      call stack. A real cost, not just a stylistic preference.
      - *What this means concretely:* **eventual consistency** means: right after something happens, different parts of the system might briefly disagree about the current state, and that's accepted
        as normal rather than prevented. Concretely here: the instant a round resolves, game-engine's own database is immediately correct, but the event announcing that outcome takes a small amount of
        time to actually reach whichever service consumes it — there's a brief window where the source of truth has already moved on but a consumer hasn't caught up yet. Contrast this with a direct,
        synchronous API call, where the caller only gets control back once the other side has already processed the request — slower and more tightly coupled, but no such gap exists.
  - *Read first:* GCP Pub/Sub's ["Publish messages to topics"](https://cloud.google.com/pubsub/docs/publisher) docs — the concrete publish workflow (topics, message data) this ticket needs, even
    before any real GCP infrastructure exists locally.
  - *Learning notes:* `docs/task_learning_notes/phase_1_mvp_core_game_loop/06_publish_a_round_resolution_event.md` — the Pub/Sub client's non-async `.result()` gotcha, worth knowing before writing
    the route (a direct callback to the async coloring problem).

## Phase 2 — Hidden Information & Fog of War

This is the project's actual core problem (see `CLAUDE.md`) — deliberately tackled only once Phase 1's game loop already works end to end with full visibility, so this phase changes *what's visible*,
not the underlying move/combat logic.

- [ ] **Enforce hidden rank in every payload.** Opponent units show position and unit type always; quality tier and full stats stay omitted from the response entirely unless `revealed` is `true`.
  Acceptance: a test asserts the literal serialized response body never contains an unrevealed opponent unit's quality tier or stats — not just that a UI doesn't render them.
  - *What it is:* server-authoritative state means the server holds the one complete truth (every unit's real rank), and every response is a filtered *view* of that truth computed specifically for
    its recipient — never the raw truth itself, and never something the client is trusted to hide on its own.
  - *Why we use it:* this is the project's actual reason for existing (see `CLAUDE.md`'s "Core technical challenge") — a client that can inspect network traffic and find an opponent's hidden rank
    has broken the one guarantee the whole system is built around, no matter what the UI chooses to render.
  - *How it works:*
    - The flow: full game state (DB) → a per-player filter function (checks the `revealed` flag) → a filtered response → sent to that one player only.
    - **The filter runs server-side, per request, per player** — recomputed every time, never cached or reused across players — and is applied at the response-serialization boundary itself, not
      left to a route handler to remember.
  - *What breaks without it:* if any response accidentally includes a full `Piece` object (a debug dump, a naive `return piece` instead of the filtered schema), the opponent's hidden rank leaks —
    even if the frontend never renders that field, it's sitting in the raw HTTP response for anyone to inspect via browser dev tools.
  - *Industry context:*
    - *Origin:* server-authoritative architecture is standard in multiplayer game networking since at least the era of competitive anti-cheat design — client-held data is untrustworthy, full stop.
    - *Alternatives:* client-authoritative/client-trusted models, where the client holds the full state and is trusted to only display what it should — exploitable by simply reading client
      memory or network traffic, which is exactly why a hidden-rank game can't use this model.
    - *Tradeoffs:* server-authoritative design costs more server-side compute (filtering per player, per request) and more implementation discipline than a client-trusted model's simplicity — not
      negotiable here, since hidden information is the entire point of the game.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the chapter on client-server authority and hiding information from clients.

- [ ] **Enforce fog of war in every payload.** Opponent units outside your own units' sight radius are structurally absent from your payload — not present-but-unrevealed, genuinely missing.
  Acceptance: a test asserts an out-of-range opponent unit is absent from the response body.
  - *What it is:* fog of war means a viewer only perceives entities within a defined visibility boundary (here, within any of their own units' sight radius) — anything outside it is structurally
    absent from what that viewer receives, not merely unrendered.
  - *Why we use it:* same guarantee as the ticket above, different axis — this one is about *position* leaking rather than *rank* leaking, which is why it's a separate single-purpose ticket instead
    of folded into the one above.
  - *How it works:*
    - The flow: for each opponent unit, compute distance to every one of the viewer's own units → if within any one's sight radius, include it (position/type, subject to reveal rules) →
      otherwise, omit it entirely.
    - **Same filter function as hidden rank, one more condition** — not a separate pass, run at the same place and time in the request/event lifecycle.
  - *What breaks without it:* a player could see the full board regardless of their own units' vision, turning a game about scouting and positioning into one with full information.
  - *Industry context:*
    - *Origin:* one of the oldest strategy-game mechanics, from tabletop wargaming's "hidden movement" rules, popularized digitally by 1990s RTS games (Warcraft, Command & Conquer, StarCraft).
    - *Alternatives:* implementing fog of war purely client-side (a black overlay over unexplored areas, while still sending the client the full map) — the exact anti-pattern this project's
      design explicitly avoids, since client-side-only hiding isn't real hiding.
    - *Tradeoffs:* real per-unit sight-radius visibility computed server-side, every round, for every player, is more compute-intensive than a client-side overlay trick — but it's the only
      version that's actually secure against a client inspecting network traffic.
  - *Read first:* same chapter as above — sight radius is the other half of "client-server authority over what's visible."

- [ ] **Upgrade round-resolution events to per-player filtering.** Now that hidden rank and fog of war exist, the single event from Phase 1 must become a separate, differently-filtered event per
  affected player — same filtering rule as the HTTP payload above applies to the event body. Acceptance: a test confirms the two players' published events are never identical when hidden information
  differs between them.
  - *What it is:* taking Phase 1's single unfiltered event body and applying the exact same per-player filtering logic already built for HTTP responses to the Pub/Sub event body too.
  - *Why we use it:* Phase 1's single shared event was only safe because nothing was hidden yet — leaving it unfiltered now would leak exactly what the two tickets above just spent effort
    protecting in the HTTP response, just through a different channel.
  - *How it works:*
    - The flow: round resolves → for each of the two players, compute their filtered view (reusing the same filter function from the two tickets above) → publish one event per player, each
      containing only that player's own filtered content.
    - **Reuses the same filtering logic as the HTTP path** — not a second, parallel implementation, which would risk the two drifting out of sync (fixed in one place, forgotten in the other).
  - *What breaks without it:* precisely the risk already named in Phase 1 — a shared event body would leak exactly what the HTTP filtering was built to prevent, just through a different channel
    (a future `bff` event consumer, or a debug log, seeing the opponent's hidden rank).
  - *Industry context:*
    - *Origin:* the general principle of maintaining one canonical authorization/filtering boundary across multiple output channels (HTTP responses, events, logs) rather than reimplementing "who
      can see what" per channel — a well-known real source of security bugs (an API that correctly redacts a field in its REST response but leaks it in a webhook or audit log built from a
      different code path).
    - *Alternatives:* separate, channel-specific filtering logic for HTTP vs. events — tempting since the two are different code paths, but exactly the duplication that drifts.
    - *Tradeoffs:* reusing one shared filter function requires it to be genuinely channel-agnostic (return a plain filtered structure, let each channel serialize it differently) — a small design
      constraint worth respecting deliberately.
  - *Read first:* none additional — this is the direct payoff of the two tickets above.

- [ ] **[BLOCKED] Threat-model the hidden-information boundary using STRIDE.** Apply STRIDE's six threat categories — particularly Information Disclosure — to the BFF ↔ game-engine boundary, to
  identify how the design prevents an opponent's hidden rank from leaking into any API response, event, or log. Acceptance criteria can't be written until the `bff` repo (and its side of that
  boundary) exists.
  - *What it is:* STRIDE is a threat-modeling framework — six categories (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) used to systematically
    ask "what could go wrong here" about a system boundary, rather than relying on ad hoc "did we think of everything" review.
  - *Why we use it:* the three enforcement tickets above prove the payload is correct *today* — a structured threat model is what catches the ways a future change (a new field, a debug log, a new
    event type) could reopen the leak later without anyone noticing during code review.
  - *How it works:*
    - The flow: draw the actual boundary (BFF ↔ game-engine) → for each of STRIDE's six categories, ask whether it applies here and how the current design prevents it → document findings,
      weighted heavily toward Information Disclosure — the category matching this project's actual core risk.
    - **This is a structured walkthrough, not six equal boxes** — the letters are prompts to consider systematically, not sections needing equal depth.
  - *What breaks without it:* without a structured pass, review of "could this leak hidden info" tends to be ad hoc — someone eyeballs the code, catches obvious cases, and misses subtle ones (a
    new field, a debug log, a serialization shortcut) that a systematic pass is specifically designed to catch.
  - *Industry context:*
    - *Origin:* developed at Microsoft in the late 1990s (Loren Kohnfelder and Praerit Garg), popularized through Microsoft's Security Development Lifecycle — one of the most widely taught
      threat-modeling frameworks in the industry.
    - *Alternatives:* PASTA (Process for Attack Simulation and Threat Analysis, more business-risk-focused), attack trees, or ad hoc code review without a named framework at all.
    - *Tradeoffs:* STRIDE is quick to apply and easy to remember (six letters) but is more of a checklist/prompt than a rigorous quantitative risk model — PASTA or formal risk scoring go further
      but take much more effort; "structured but lightweight" is the right tradeoff at this project's size.
  - *Read first:* **Alice and Bob Learn Application Security** — the threat-modeling/STRIDE chapters.
  - *Blocked on:* the `bff` repo being created.

## Phase 3 — Hardening

- [ ] **Set up CI with GitHub Actions.** A workflow runs the test suite and lint on every push/PR; once a real registry exists, a separate step builds this service's Docker image and pushes it,
  tagged with the commit SHA — the artifact the `platform` repo's ArgoCD side will eventually deploy. Acceptance: a workflow file runs `pytest` and `ruff check` on every PR; the build-and-push step
  can be stubbed or deferred until Artifact Registry access exists.
  - *What it is:* GitHub Actions is GitHub's own CI/CD system — a YAML file in `.github/workflows/` describes jobs (each a sequence of steps) that run automatically on events like "a PR was opened"
    or "code was pushed to main," on GitHub-hosted runners.
  - *Why we use it:* catches a broken test or lint failure before it's merged, instead of relying on remembering to run the suite locally every time — and later, produces the actual image artifact
    the deploy ticket depends on.
  - *How it works:*
    - The flow: a push/PR triggers → GitHub spins up a fresh runner → checks out the repo → runs each step in order (install deps, test, lint) → reports pass/fail back on the PR.
    - **Each run starts from a clean environment** — nothing carries over between runs, which is why the workflow has to explicitly install dependencies (`uv sync`) rather than assuming anything's
      already there.
    - **The build-and-push step** (once a registry exists) authenticates to it, builds the image from this repo's Dockerfile, tags it with the commit SHA, and pushes it — that tag is what the
      `platform` repo's manifests eventually get updated to reference.
  - *What breaks without it:* a broken test or lint issue can get merged silently, discovered later and further from when it was introduced; there's also no automated path from "code merged" to "a
    new image exists" — deploys would have to be built and pushed by hand every time.
  - *Industry context:*
    - *Origin:* GitHub Actions launched in 2019, folding what used to require a separate CI service (Travis CI, CircleCI, Jenkins) directly into GitHub — configured via YAML files living in the
      repo itself, versioned alongside the code they test.
    - *Alternatives:* CircleCI and Jenkins (older, more configurable, but external services to maintain separately), GitLab CI (the equivalent if hosted on GitLab instead).
    - *Tradeoffs:* the path of least friction specifically because this repo is already on GitHub — no separate service to wire up — at the cost of some lock-in to GitHub's specific YAML syntax and
      runner model versus a more portable CI config.
  - *Read first:* **Learning GitHub Actions** (Brent Laster) — Chapters 1-2 ("The Basics" and "How Does Actions Work?"), covering triggers, jobs, steps, and runners directly.

- [ ] **Expose a full-current-state endpoint for reconnection.** A rejoining player's client needs to fetch their own complete, correctly-filtered current view of the game in one call, rather than
  relying on missed events. Acceptance: the response is identical in shape and filtering to what a live round-resolution event would have contained.
  - *What it is:* an endpoint that returns a player's complete, correctly-filtered current view of an in-progress game — the same shape/content a live round-resolution event would have delivered,
    fetched on demand instead of pushed.
  - *Why we use it:* without this, a player who refreshes or drops mid-game has no way back into a correctly-filtered view except waiting for the next event to arrive — which might never happen
    if nothing changes while they're gone.
  - *How it works:*
    - The flow: client reconnects → calls this endpoint with the game ID and its own player identity → the server recomputes the same per-player filtered view used elsewhere (Phase 2's filter
      function, reused, not reimplemented) → returns it as a plain response → client resubscribes to future live events going forward.
    - **No "resume" or event-replay logic needed** — it just answers "what does the current state look like for you, right now," using logic that already exists.
  - *What breaks without it:* a player who refreshes or drops connection has no way back into a correct view except waiting for the next event — which might never come, leaving them stuck on
    stale or blank state indefinitely.
  - *Industry context:*
    - *Origin:* the standard resynchronization pattern for any system with both a push channel (WebSockets, Pub/Sub) and reconnect scenarios — reconnect logic almost universally works by
      discarding assumptions about "what was missed" and re-fetching current truth, rather than replaying every intermediate event.
    - *Alternatives:* event replay (storing and re-delivering every missed event in order) — more complex, and unnecessary here since only current state matters, not the history of how it got
      there (that's Phase 4's separate replay ticket).
    - *Tradeoffs:* re-fetch-current-state is simpler and sufficient when only the latest state matters; event replay is the right tool when the intermediate steps themselves matter — picking the
      wrong one is either wasted complexity or a missing capability.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the section on reconnection and state resynchronization.

- [ ] **Deploy.** Containerize and deploy this service to GKE via the `platform` repo's ArgoCD-managed manifests. Acceptance criteria can't be finalized until the `platform` repo exists.
  - *What it is:* taking this service's Docker image (Phase 0) and running it on GKE, with the `platform` repo's ArgoCD watching for new image tags and syncing them into the cluster automatically.
  - *Why we use it:* a game that only runs on one laptop isn't actually shareable — this is what turns the project from "works on my machine" into something a second real person can connect to.
  - *How it works:*
    - The flow: CI (previous ticket) builds and pushes a tagged image → a commit updates the `platform` repo's manifest to reference that tag → ArgoCD detects the change → applies the updated
      manifest to the GKE cluster → Kubernetes rolls out new pods running the new image.
    - **This repo's own role is minimal**: be correctly containerized (Phase 0) and expose whatever health/readiness signals Kubernetes needs to know a pod is ready to serve traffic.
  - *What breaks without it:* a service that only runs locally isn't shareable — nobody else can play the game, and every future companion repo (`bff`, `frontend`) has nothing real to connect to.
  - *Industry context:*
    - *Origin:* this whole flow is GitOps — using git commits (not manual `kubectl apply` or a cloud console) as the single source of truth for what's deployed, with a tool like ArgoCD or Flux
      continuously reconciling the cluster to match. Popularized as a term around 2017 by Weaveworks.
    - *Alternatives:* manual deploys (`kubectl apply` run by hand or from a CI script, no separate reconciling agent) — simpler for a small solo project, but loses GitOps's audit trail (every
      deploy is a traceable commit) and self-healing property (ArgoCD reverts manual cluster drift back to match git).
    - *Tradeoffs:* GitOps adds real setup overhead (a whole separate `platform` repo, ArgoCD itself) a solo project doesn't strictly need functionally — chosen here because learning that workflow
      is a stated project goal, not because the game demands it at this scale.
  - *Read first:* **Kubernetes Up & Running** for the GKE/orchestration side, and **Google Cloud Certified Associate Cloud Engineer Study Guide** for the GCP-specific pieces (IAM, Cloud SQL, VPC)
    Kubernetes' own docs won't cover — once this ticket actually starts, not before.
  - *Blocked on:* the `platform` repo being created.

## Phase 4 — Post-MVP Features

- [ ] **Player-driven setup & army selection.** Each player chooses their army composition and places their units in a formation of their choosing before the game starts, replacing Phase 1's
  hard-coded fixed army. Acceptance: a player cannot see the opponent's placement during setup; the game only moves to `in_progress` once both players have finished placing.
  - *What it is:* replacing Phase 1's hard-coded identical army with a real setup phase — each player chooses their own formation, gated by a `Game.status` of `setup` before the transition into
    `in_progress`.
  - *Why we use it:* Phase 1's hard-coded army was a deliberate MVP simplification, not the target design — army composition and placement choices are a core part of what makes a Stratego-like
    actually interesting strategically, so this is where the game becomes the game it's meant to be.
  - *How it works:*
    - The flow: game created → `status = setup` → each player submits their placement → once both have submitted, `status` flips to `in_progress` → the round loop (Phase 1's existing logic)
      begins.
    - **Each player's placement stays invisible to the other during setup** — the same per-player filtering principle as Phase 2, applied to a new phase of the game rather than ongoing rounds.
  - *What breaks without it:* the game stays permanently limited to the MVP's identical-fixed-army version — no strategic depth from formation/composition choice, which is a core part of what
    makes a Stratego-like a real game rather than a tech demo.
  - *Industry context:*
    - *Origin:* the classic "deployment phase" mechanic present in essentially every wargame/Stratego-like, going back to the original Stratego (1942) and Kriegsspiel before it — a standard
      game-design pattern, not specific to this project.
    - *Alternatives:* no setup phase at all (staying in the MVP's simplified state), or a blind-bidding draft mechanic instead of placing a fixed roster — tied to the still-open army-selection
      question.
    - *Tradeoffs:* player-chosen placement adds real state-machine complexity (a new `setup` phase to test, a second visibility boundary) versus the MVP's zero-setup simplicity — worth it since
      this is where the game becomes strategically interesting.
  - *Read first:* **Game Programming Patterns** — the State chapter. "Setup" vs "in progress" vs "finished" is exactly the state-machine problem that chapter is about.
  - *Note:* how a player's army composition/roster is chosen is still an open design question (see `docs/architecture.md`) — this ticket only covers placing a given army, not assembling one.

- [ ] **Matchmaking queue.** Players can join a queue and be auto-paired instead of needing a manually shared game ID. Folded into this repo as an internal module for now — split into its own service
  later only if it earns that separation (see `docs/architecture.md`).
  - *What it is:* a mechanism letting a player join a queue and be automatically paired with another waiting player, instead of needing to already know and message someone specific.
  - *Why we use it:* without it, playing a game requires already knowing a specific other person and manually sharing a link/code — this removes that requirement.
  - *How it works:*
    - The flow: player joins the queue → added to a waiting list (a table row for now, Redis once Phase 5's ticket lands) → a matching process pairs the two oldest waiting entries → both entries
      are removed and a new `Game` is created for them (reusing Phase 1's "create a game" logic) → both are notified (reusing the existing event-publishing mechanism).
    - **Plain Postgres is enough at MVP scale** — Redis only earns its keep once queueing needs to be fast/shared across multiple running instances.
  - *What breaks without it:* every game requires the two players to already know each other and manually share a link — fine for testing with a friend, but blocks any "play against a stranger"
    experience.
  - *Industry context:*
    - *Origin:* one of the most studied problems in online multiplayer games — from simple FIFO queues to skill-based matchmaking (ELO/Glicko-driven, as in chess.com or competitive shooters)
      balancing wait time against match fairness.
    - *Alternatives:* skill-based matchmaking (pairing similar ratings, once Phase 5's ranking system exists) versus simple FIFO pairing — this ticket deliberately starts with FIFO, since
      skill-based matching needs a rating system that doesn't exist yet.
    - *Tradeoffs:* FIFO is trivial to build but can pair a beginner against an expert; skill-based matching is fairer but needs a working rating system first — sequencing this before Phase 5's
      ranking ticket is a deliberate scope decision, not an oversight.
  - *Read first:* **Patterns of Enterprise Application Architecture** — general data-modeling patterns apply here (a queue is just state + a matching query). If the queue moves to Redis for speed,
    **Redis in Action** is the natural follow-up.

- [ ] **Spectator mode.** A third party can watch a game in progress without being able to see hidden information belonging to either player.
  - *What it is:* a third kind of viewer — neither player — who can watch a game in progress, receiving a filtered view that hides *all* hidden information belonging to either player, stricter
    than either player's own view.
  - *Why we use it:* extends the exact per-viewer filtering logic Phase 2 already built to a third kind of viewer, rather than needing new infrastructure — a good test of whether that filtering was
    actually built generically or accidentally hard-coded to "exactly two players."
  - *How it works:*
    - The flow: spectator requests to watch → the same per-player filter function is reused a third time, with "no owned units" as input, so nothing is ever revealed by ownership — only
      information both players have mutually revealed through combat is visible.
    - **This is a direct test of the earlier filtering design** — whether it was parameterized by "which pieces does this viewer own" or accidentally assumed exactly two symmetric players.
  - *What breaks without it:* nobody except the two active players can ever watch a game — no ability to show off an interesting match, stream it, or build any social feature around watching.
  - *Industry context:*
    - *Origin:* standard in essentially every competitive multiplayer game — esports broadcasting is built entirely on this capability, the same general pattern of a third view with its own,
      typically most-restricted, visibility rules.
    - *Alternatives:* no spectator support, or a spectator mode that insecurely reuses one player's own view rather than a genuinely separate, more restricted one — the latter leaks that player's
      hidden information to the spectator, exactly the kind of bug Phase 2's STRIDE pass is meant to catch.
    - *Tradeoffs:* building this as a true third viewer type costs a small amount of extra filtering logic but is the only version that doesn't leak information — non-negotiable, same reasoning
      as hidden rank itself.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — a spectator is a third "view" of the same authoritative state.

- [ ] **Move history / replay.** A finished game can be replayed move-by-move after the fact.
  - *What it is:* the ability to step back through a finished game's moves, one at a time, after the fact.
  - *Why we use it:* this is the payoff (or the bill coming due) for whether moves got modeled as first-class command objects back in Phase 1 — cheap here if that was done, expensive if it wasn't.
  - *How it works:*
    - The flow: every move already exists as a stored Command object (Phase 1) → a replay view reads those stored objects back in original order and re-presents them one at a time, rather than
      re-deriving anything.
    - **Open question worth flagging, not assumed:** a finished game's hidden information may no longer be as sensitive (both armies were likely revealed through play) — does replay show full
      information post-game, or still respect original per-player visibility if watched by a non-participant? Worth resolving explicitly when this ticket starts.
  - *What breaks without it:* without moves modeled as reusable objects (already done in Phase 1), replay would require re-deriving move history from scratch — this ticket is really where that
    earlier Command-pattern decision either pays off cheaply or turns out to have been skipped and now costs a retrofit.
  - *Industry context:*
    - *Origin:* replay systems are common across turn-based and RTS games (chess.com's move-by-move review, StarCraft's replay files) — almost universally built by storing the sequence of player
      actions/commands rather than recording video or full state snapshots.
    - *Alternatives:* recording full board-state snapshots after every round instead of individual commands — simpler to reason about but far more storage, and loses the ability to show the
      actual order of individual actions within a round.
    - *Tradeoffs:* command-based replay is compact and was already set up for free by Phase 1's design choice; snapshot-based replay would have been simpler to add later but wasteful, and was
      avoided by that earlier decision.
  - *Read first:* **Game Programming Patterns** — the Command chapter, revisited.

## Phase 5 — Stretch / Scale

- [ ] **Ranking system.** Track win/loss record and a simple rating (e.g. Elo) across games.
  - *What it is:* tracking each player's win/loss record and a single numeric rating that rises after a win and falls after a loss, weighted by the opponent's own rating.
  - *Why we use it:* gives repeat play a reason to matter beyond the outcome of a single match.
  - *How it works:*
    - The flow: a game finishes → the win-condition ticket's outcome (already built) is read → both players' current ratings are fetched → a rating formula (e.g. Elo's expected-score
      calculation) computes each player's new rating based on actual versus expected result → both are updated and stored.
    - **The rating calculation is a pure function** (two ratings + an outcome in, two new ratings out) — a good candidate for its own small, directly-testable service-layer object, the same "one
      thing, easily tested" principle as Phase 1's combat-resolution service object.
  - *What breaks without it:* without any persistent rating, every game is disconnected from every other — no sense of "am I improving," no way to support skill-based matchmaking later, no
    leaderboard.
  - *Industry context:*
    - *Origin:* the Elo rating system, developed by Arpad Elo in the 1960s originally for chess ratings, since adopted (often in modified forms — Glicko, TrueSkill) across nearly every
      competitive game with ranked play.
    - *Alternatives:* a simpler win/loss-count-only system, no rating number — much simpler, but can't answer "how good is this player relative to that one," and can't drive skill-based
      matchmaking.
    - *Tradeoffs:* Elo is simple to implement (one formula) but has known weaknesses (slow to converge on a new player's true skill, doesn't model uncertainty) that Glicko/TrueSkill address at
      real implementation cost — a reasonable starting choice, with room to upgrade later if it matters.
  - *Read first:* **Patterns of Enterprise Application Architecture** — for modeling the rating/history data cleanly. **Domain-Driven Design** is a possible deeper follow-up if the rating rules grow
    complex enough to need a dedicated domain model.

- [ ] **Redis-backed presence/pub-sub.** Only needed once this service (or matchmaking) runs more than one instance, or needs shared presence state.
  - *What it is:* using Redis as a fast, shared, in-memory store for ephemeral state (connected players, matchmaking queue entries) once this service — or matchmaking — runs as more than one
    process.
  - *Why we use it:* a single running process's in-memory state is sufficient before that point — adding Redis earlier means solving a scaling problem that doesn't exist yet, at the cost of real
    operational complexity (see `docs/architecture.md`).
  - *How it works:*
    - The flow: once game-engine (or matchmaking) scales to multiple instances, in-memory Python state stops being reliable, since each instance has its own separate copy — Redis becomes the
      single shared place all instances read/write that state, so it stays consistent regardless of which instance handles a given request.
    - **Redis Pub/Sub specifically** lets instances notify each other (e.g. "a match was found, tell whichever instance holds that player's connection") — necessary once WebSocket connections
      might be held by a different process than the one that triggered an event.
  - *What breaks without it:* without a shared store, each instance has its own inconsistent view of shared state (e.g. two instances could each think they've matched the same waiting player with
    someone different) — a correctness bug that only appears once scaled past one process.
  - *Industry context:*
    - *Origin:* Redis (2009, Salvatore Sanfilippo) is one of the most widely used in-memory data stores specifically for this class of problem — shared ephemeral state and pub/sub messaging
      across processes.
    - *Alternatives:* Memcached (simpler, pure key-value cache, no pub/sub or richer data structures), or using Postgres itself for this shared state (`LISTEN`/`NOTIFY`, or polling a table) —
      workable at small scale but slower and not designed for this specific job.
    - *Tradeoffs:* adding Redis means a new piece of infrastructure to run and reason about — not justified until there's an actual second running instance; introducing it earlier solves a
      scaling problem that doesn't exist yet, exactly the "no premature optimization" reasoning in this ticket's own Why.
  - *Read first:* **Redis in Action** — exactly why this book is on the list.
