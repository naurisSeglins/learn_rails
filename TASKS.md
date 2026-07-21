# Tasks

Single source of truth for status and what to work on next. Update this file in the same session as any work that completes, starts, or gets rescoped.

This repo is the `game-engine` service (see `docs/architecture.md`'s System architecture table). Tickets below are scoped to this repo; companion repos (`bff`, `frontend`, `market`, `platform`) get
their own `TASKS.md` once they're created, and a ticket here notes when it depends on one of them existing.

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
  - *Blocked on:* timer-expiry behavior (auto-submit the queued-so-far batch vs. forced no-op) — see Open design questions in `docs/architecture.md`.

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

## Phase 2 — Hidden Information & Fog of War

This is the project's actual core problem (see `CLAUDE.md`) — deliberately tackled only once Phase 1's game loop already works end to end with full visibility, so this phase changes *what's visible*,
not the underlying move/combat logic.

- [ ] **Enforce hidden rank in every payload.** Opponent units show position and unit type always; quality tier and full stats stay omitted from the response entirely unless `revealed` is `true`.
  Acceptance: a test asserts the literal serialized response body never contains an unrevealed opponent unit's quality tier or stats — not just that a UI doesn't render them.
  - *Why:* this is the project's actual reason for existing (see `CLAUDE.md`'s "Core technical challenge") — a client that can inspect network traffic and find an opponent's hidden rank has broken the
    one guarantee the whole system is built around, no matter what the UI chooses to render.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the chapter on client-server authority and hiding information from clients.

- [ ] **Enforce fog of war in every payload.** Opponent units outside your own units' sight radius are structurally absent from your payload — not present-but-unrevealed, genuinely missing.
  Acceptance: a test asserts an out-of-range opponent unit is absent from the response body.
  - *Why:* same guarantee as the ticket above, different axis — this one is about *position* leaking rather than *rank* leaking, which is why it's a separate single-purpose ticket instead of folded
    into the one above.
  - *Read first:* same chapter as above — sight radius is the other half of "client-server authority over what's visible."

- [ ] **Upgrade round-resolution events to per-player filtering.** Now that hidden rank and fog of war exist, the single event from Phase 1 must become a separate, differently-filtered event per
  affected player — same filtering rule as the HTTP payload above applies to the event body. Acceptance: a test confirms the two players' published events are never identical when hidden information
  differs between them.
  - *Why:* Phase 1's single shared event was only safe because nothing was hidden yet — leaving it unfiltered now would leak exactly what the two tickets above just spent effort protecting in the HTTP
    response, just through a different channel.
  - *Read first:* none additional — this is the direct payoff of the two tickets above.

- [ ] **[BLOCKED] Threat-model the hidden-information boundary using STRIDE.** Apply STRIDE's six threat categories — particularly Information Disclosure — to the BFF ↔ game-engine boundary, to
  identify how the design prevents an opponent's hidden rank from leaking into any API response, event, or log. Acceptance criteria can't be written until the `bff` repo (and its side of that
  boundary) exists.
  - *Why:* the three enforcement tickets above prove the payload is correct *today* — a structured threat model is what catches the ways a future change (a new field, a debug log, a new event type)
    could reopen the leak later without anyone noticing during code review.
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
  - *Why:* without this, a player who refreshes or drops mid-game has no way back into a correctly-filtered view except waiting for the next event to arrive — which might never happen if nothing
    changes while they're gone.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the section on reconnection and state resynchronization.

- [ ] **Deploy.** Containerize and deploy this service to GKE via the `platform` repo's ArgoCD-managed manifests. Acceptance criteria can't be finalized until the `platform` repo exists.
  - *Why:* a game that only runs on one laptop isn't actually shareable — this is what turns the project from "works on my machine" into something a second real person can connect to.
  - *Read first:* **Kubernetes Up & Running** for the GKE/orchestration side, and **Google Cloud Certified Associate Cloud Engineer Study Guide** for the GCP-specific pieces (IAM, Cloud SQL, VPC)
    Kubernetes' own docs won't cover — once this ticket actually starts, not before.
  - *Blocked on:* the `platform` repo being created.

## Phase 4 — Post-MVP Features

- [ ] **Player-driven setup & army selection.** Each player chooses their army composition and places their units in a formation of their choosing before the game starts, replacing Phase 1's
  hard-coded fixed army. Acceptance: a player cannot see the opponent's placement during setup; the game only moves to `in_progress` once both players have finished placing.
  - *Why:* Phase 1's hard-coded army was a deliberate MVP simplification, not the target design — army composition and placement choices are a core part of what makes a Stratego-like actually
    interesting strategically, so this is where the game becomes the game it's meant to be.
  - *Read first:* **Game Programming Patterns** — the State chapter. "Setup" vs "in progress" vs "finished" is exactly the state-machine problem that chapter is about.
  - *Note:* how a player's army composition/roster is chosen is still an open design question (see `docs/architecture.md`) — this ticket only covers placing a given army, not assembling one.

- [ ] **Matchmaking queue.** Players can join a queue and be auto-paired instead of needing a manually shared game ID. Folded into this repo as an internal module for now — split into its own service
  later only if it earns that separation (see `docs/architecture.md`).
  - *Why:* without it, playing a game requires already knowing a specific other person and manually sharing a link/code — this removes that requirement.
  - *Read first:* **Patterns of Enterprise Application Architecture** — general data-modeling patterns apply here (a queue is just state + a matching query). If the queue moves to Redis for speed,
    **Redis in Action** is the natural follow-up.

- [ ] **Spectator mode.** A third party can watch a game in progress without being able to see hidden information belonging to either player.
  - *Why:* extends the exact per-viewer filtering logic Phase 2 already built to a third kind of viewer, rather than needing new infrastructure — a good test of whether that filtering was actually
    built generically or accidentally hard-coded to "exactly two players."
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — a spectator is a third "view" of the same authoritative state.

- [ ] **Move history / replay.** A finished game can be replayed move-by-move after the fact.
  - *Why:* this is the payoff (or the bill coming due) for whether moves got modeled as first-class command objects back in Phase 1 — cheap here if that was done, expensive if it wasn't.
  - *Read first:* **Game Programming Patterns** — the Command chapter, revisited.

## Phase 5 — Stretch / Scale

- [ ] **Simple AI opponent.** A heuristic (non-learning) bot a player can practice against.
  - *Why:* lets a player exercise the game loop without needing a second human present — useful for testing the core loop itself, too, not just for solo play.
  - *Read first:* **AI for Games** (Ian Millington) — the Board Games chapter, covering minimax, negamax, and alpha-beta pruning directly.

- [ ] **Ranking system.** Track win/loss record and a simple rating (e.g. Elo) across games.
  - *Why:* gives repeat play a reason to matter beyond the outcome of a single match.
  - *Read first:* **Patterns of Enterprise Application Architecture** — for modeling the rating/history data cleanly. **Domain-Driven Design** is a possible deeper follow-up if the rating rules grow
    complex enough to need a dedicated domain model.

- [ ] **Redis-backed presence/pub-sub.** Only needed once this service (or matchmaking) runs more than one instance, or needs shared presence state.
  - *Why:* a single running process's in-memory state is sufficient before that point — adding Redis earlier means solving a scaling problem that doesn't exist yet, at the cost of real operational
    complexity (see `docs/architecture.md`).
  - *Read first:* **Redis in Action** — exactly why this book is on the list.
