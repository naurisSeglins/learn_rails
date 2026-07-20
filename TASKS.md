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
- a **Read first** line pointing at the book(s) in `books.md` most relevant to that task's context — not the whole book, just go in with that lens. Some tasks are pure setup/administration with no
  useful reading; those say so rather than forcing a fit.

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
      - *What breaks without it:* you'd be hand-writing HTTP parsing, routing, and response formatting from scratch — solved problems FastAPI gives you for free.
      - *Industry context:*
        - *Origin:* created 2018 by Sebastián Ramírez, built *on top of* two existing libraries (Starlette for the async web layer, Pydantic for validation) rather than reinventing them. Its breakout
          feature was auto-generating interactive API docs (the `/docs` page) straight from your type hints — most competitors don't do this out of the box.
        - *Alternatives:* Flask (older, sync-first, far larger ecosystem, much more manual/explicit — nothing happens unless you write it), Django REST Framework (batteries-included, but tied to
          Django's ORM/admin — heavier than needed for a small service like this one).
        - *Tradeoffs:* versus Flask, FastAPI's type-hint-driven validation and dependency injection are powerful but more implicit — more "magic" to learn, less obvious what's happening just from
          reading a route function.
    - **uvicorn**
      - *What it is:* FastAPI only knows *what to do* once a request arrives — it has no idea how to open a network socket or listen on a port. uvicorn is the separate program that does that
        networking work, and for every request it receives, calls into your FastAPI app to ask "what's the response?" This is Python's equivalent of Puma in Rails: Rails defines your app, Puma is
        what's actually bound to a port listening for connections.
      - *Why we use it:* FastAPI needs an actual running process serving it — `app = FastAPI()` alone doesn't listen for anything.
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
      - *Industry context:*
        - *Origin:* written in large part by Yury Selivanov, who also worked on asyncio's own internals — known for being unusually fast.
        - *Alternatives:* psycopg2 (the long-standing standard Postgres driver, sync-only), psycopg3 (its modern successor, which does support async and is a closer competitor to asyncpg than psycopg2
          is).
        - *Tradeoffs:* asyncpg's speed comes partly from skipping PEP 249 (Python's standard "DB-API" interface most drivers implement for interchangeability) — so it isn't a drop-in swap for other
          PEP 249-compliant tools, and you're relying on SQLAlchemy to abstract that difference away rather than talking to asyncpg directly.
      - *What breaks without it:* using an ordinary (synchronous) driver like `psycopg2` instead would mean that while any one request waits on the database, the entire server process freezes and
        can't handle any other request at all — which defeats the reason this stack is async in the first place.
    - **Alembic**
      - *What it is:* a tool that records changes to your database's structure (adding a table, adding a column) as small, numbered script files, each one saying how to apply the change and how to
        undo it. This is the direct equivalent of Rails' `db/migrate` files and `rails db:migrate` — Alembic pairs with SQLAlchemy the way ActiveRecord migrations pair with Rails.
      - *Why we use it:* as the data model changes (a new field on `Piece`, say), you need one repeatable way to apply that change everywhere — your laptop, CI, production.
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
      - *What breaks without it:* you'd be manually validating incoming JSON and manually building outgoing JSON everywhere — and a forgotten manual check is exactly how a hidden rank would
        accidentally leak later (see Phase 2).
      - *Industry context:*
        - *Origin:* built on Python's type hints (a language feature that matured over many releases) — Pydantic's core idea is using those hints not just for editor autocomplete, but to actually
          validate data at runtime. Version 2 (2023) rewrote its core validation engine in Rust for a major speed jump.
        - *Alternatives:* stdlib `dataclasses` (structure only, no validation), `marshmallow` (an older, more manual validation/serialization library that predates Pydantic's type-hint-driven
          approach).
        - *Tradeoffs:* Pydantic is used widely outside FastAPI too — a general data-validation library, not FastAPI-specific. The Rust rewrite is itself a recognizable pattern: a Python library
          reaching for a compiled language once pure-Python performance becomes the bottleneck, the same story behind pandas' C internals or Ruff being written in Rust.
  - *Read first:* **Python Concurrency with asyncio** — enough to understand why the app and its dependencies are async-first, before writing the first route.

- [ ] **Set up Postgres via SQLAlchemy (async) + Alembic.** Configure an async database connection and confirm a first (empty) Alembic migration runs against a local Postgres instance. This service
  owns its own database — see `docs/architecture.md`'s data-ownership rule.
  - *Why:*
    - **Postgres, not SQLite** — SQLite locks the whole file under concurrent writes, a problem the moment two games are being played at once (see `docs/architecture.md`'s "Postgres, not SQLite"
      bullet for the full rationale).
    - **This service owning its own database** — rather than sharing one with a future `market` service, is what makes the multi-repo split actually mean something instead of being a monolith with
      extra network hops (see `docs/architecture.md`'s "One database per service" bullet).
  - *Industry context:*
    - *Origin:* PostgreSQL, first released in 1996 — one of the oldest actively-developed open-source relational databases, known for strict SQL-standards compliance and a reputation for extensibility
      (custom types, extensions like PostGIS for geodata).
    - *Alternatives:* MySQL/MariaDB (historically more common for simple web apps, weaker at complex queries and JSON handling for most of its history, though it's closed much of that gap),
      CockroachDB (Postgres-wire-compatible but built for horizontal scaling across multiple machines).
    - *Tradeoffs:* Postgres is a full client-server database requiring its own running process to manage — SQLite's biggest advantage (zero setup, just a file) is exactly what you give up by choosing
      Postgres. Worth it here because concurrent games writing moves is precisely the case SQLite handles badly (see the Why above).
  - *Read first:* none of the current reading list covers SQLAlchemy/Alembic directly — worth a dedicated lookup rather than a full book for this one.

- [ ] **Set up pytest + httpx for request-style specs.** Add `pytest`, `pytest-asyncio`, `httpx` (for `AsyncClient` against the FastAPI app), and `factory_boy` (per CLAUDE.md's Testing Conventions).
  Confirm `pytest` runs (even with zero tests).
  - *Why:*
    - **pytest-asyncio**
      - *What it is:* a plugin that teaches pytest (the test runner) how to run `async def` test functions. A normal Python function runs straight through top to bottom; an `async def` function is
        written to pause and resume (e.g. while waiting on a database call), and pytest has no built-in idea how to drive that pause/resume cycle on its own — this plugin adds it.
      - *Why we use it:* your FastAPI routes are `async def` functions, so testing them properly means calling them the same way.
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
      - *What breaks without it:* every test needing a database record hand-rolls its own setup code, which duplicates across the suite and quietly drifts out of sync as the model changes.
      - *Industry context:*
        - *Origin:* the Python port of Ruby's `factory_girl` (thoughtbot's gem, later renamed FactoryBot in 2017) — factory_boy's name is a deliberate pun on the original Ruby name, not a coincidence.
          Worth knowing the ancestry runs Ruby → Python here, unlike SQLAlchemy/Alembic/pytest above, which have no Rails lineage at all.
        - *Alternatives:* plain pytest fixtures (hand-rolled, no shared "recipe" concept), `model_bakery` (a similar factory library, but specific to Django's ORM).
        - *Tradeoffs:* factory_boy adds a small amount of setup/learning overhead versus just hand-writing objects in each test — it only pays off once the suite is big enough that the duplication it
          avoids actually starts to hurt.
  - *Read first:* **Python Testing with pytest** — the fixtures/async-test chapter, so config choices here are deliberate.

- [ ] **Add a Dockerfile for local containerization.** A minimal image that runs the FastAPI app via uvicorn — the basis for both local docker-compose use and the eventual GKE deploy.
  - *Why:* building this now, rather than waiting for the Phase 3 deploy ticket, means every ticket from here on can be sanity-checked in the same environment that will eventually run in production. A
    container-specific bug (a missing system library, a path assumption that only holds on your laptop) is cheap to catch here and expensive to discover for the first time during an actual deploy.
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
  - *Why:* this is the smallest slice that produces a real, shared object two players are actually attached to — every later ticket (moves, combat, win detection) needs a `Game` to operate on, so it
    has to exist first regardless of what game rules end up being decided.
  - *Industry context:*
    - *Origin:* `POST`-to-create-a-resource, returning an identifier the client uses for everything after, is the core idea of **REST** (Representational State Transfer) — a style described in Roy
      Fielding's 2000 PhD dissertation, not a FastAPI feature. FastAPI doesn't enforce RESTfulness; it just makes it convenient to follow.
    - *Alternatives:* RPC-style APIs (verbs in the URL, e.g. `POST /createGame`, `POST /submitMove`, instead of resources), or GraphQL (one endpoint, the client specifies exactly what data shape it
      wants back).
    - *Tradeoffs:* REST's resource-oriented style tends to age well and map cleanly onto CRUD-shaped operations like this one, but doesn't always fit an action like "submit move orders" as naturally
      as a pure RPC verb would — worth noticing that friction when it comes up rather than forcing every action into REST dogma.
  - *Read first:* none specific — a straightforward FastAPI router + Pydantic schema exercise.

- [ ] **Submit move orders for a round, with a round timer.** A player can queue movement orders for any subset of their own units during the round's countdown timer (each unit capped by its own
  movement allowance), then submit the batch. Acceptance: illegal orders (insufficient movement allowance remaining, moving an immobile unit) are rejected with a generic error; a submitted batch stays
  invisible to the opponent until the round resolves.
  - *Why:* modeling a queued move as a first-class object (rather than a bag of params) up front is what makes both this ticket's own validation and Phase 4's replay ticket tractable later —
    retrofitting that structure after moves are already scattered through ad-hoc code is much more expensive than starting with it.
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
  - *Why:* combat is where two players' independent, simultaneous move batches actually collide — without it, "submit moves" and "declare a winner" have nothing connecting them.
  - *Industry context:*
    - *Origin:* pulling business logic out of a route handler or model into its own object is often called a **service object** (Rails world) or **application service** (Domain-Driven Design
      terminology) — the general principle: framework entry points should stay thin, and logic complex enough to need its own tests deserves its own class.
    - *Alternatives:* a "fat controller" (all logic in the route handler) or a "fat model" (all logic on the `Game`/`Piece` classes) — both common, real anti-patterns, not hypothetical ones.
    - *Tradeoffs:* an extra class for logic that could technically fit in fewer lines elsewhere — the payoff is testability and CLAUDE.md's "one thing" rule, not raw line count.
  - *Read first:* **Dive Into Design Patterns** and **Practical Object-Oriented Design in Ruby (POODR)** — on extracting a focused service-layer object. Battle resolution is business logic that
    doesn't belong in a route handler or model.

- [ ] **[BLOCKED] Detect win conditions.** The win condition itself is an open design question (Flag-capture equivalent vs. something else) — see Open design questions in `docs/architecture.md`. Do
  not start implementation until that's resolved.
  - *Why:* without an explicit terminal state, a finished game would keep silently accepting moves — this is what turns "the game is over" into an enforced guarantee instead of something the UI just
    happens to assume.
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
  - *Why:* this is the seam the future `bff` repo will consume to push live updates to a browser connection. Building the publishing mechanism now, even in its simplest unfiltered form, means Phase 2
    only has to change *what's in* the event, not invent how events get published from scratch.
  - *Industry context:*
    - *Origin:* publishing a fact ("this happened") for other interested parties to react to, without the publisher knowing or caring who's listening, is **event-driven architecture** — GCP Pub/Sub is
      one implementation of a much older, general idea also implemented by Kafka, RabbitMQ, and AWS SNS/SQS.
    - *Alternatives:* the publisher directly calling every interested service's API instead — tighter coupling, since the publisher then needs to know who all its consumers are, and breaks if a
      consumer happens to be down at that moment. That's exactly the problem message brokers exist to avoid.
    - *Tradeoffs:* event-driven systems trade that tight coupling for eventual consistency and a harder-to-trace request flow — a bug can be "somewhere in this chain of events" rather than one obvious
      call stack. A real cost, not just a stylistic preference.
  - *Read first:* none of the current list covers Pub/Sub message design directly — a dedicated lookup once this ticket starts.

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

- [ ] **Expose a full-current-state endpoint for reconnection.** A rejoining player's client needs to fetch their own complete, correctly-filtered current view of the game in one call, rather than
  relying on missed events. Acceptance: the response is identical in shape and filtering to what a live round-resolution event would have contained.
  - *Why:* without this, a player who refreshes or drops mid-game has no way back into a correctly-filtered view except waiting for the next event to arrive — which might never happen if nothing
    changes while they're gone.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the section on reconnection and state resynchronization.

- [ ] **Deploy.** Containerize and deploy this service to GKE via the `platform` repo's ArgoCD-managed manifests. Acceptance criteria can't be finalized until the `platform` repo exists.
  - *Why:* a game that only runs on one laptop isn't actually shareable — this is what turns the project from "works on my machine" into something a second real person can connect to.
  - *Read first:* **Kubernetes Up & Running** — once this ticket actually starts, not before.
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
  - *Read first:* none of the current reading list covers game AI algorithms in depth — worth adding a dedicated book (e.g. on minimax/heuristic search) if this task gets picked up.

- [ ] **Ranking system.** Track win/loss record and a simple rating (e.g. Elo) across games.
  - *Why:* gives repeat play a reason to matter beyond the outcome of a single match.
  - *Read first:* **Patterns of Enterprise Application Architecture** — for modeling the rating/history data cleanly. **Domain-Driven Design** is a possible deeper follow-up if the rating rules grow
    complex enough to need a dedicated domain model.

- [ ] **Redis-backed presence/pub-sub.** Only needed once this service (or matchmaking) runs more than one instance, or needs shared presence state.
  - *Why:* a single running process's in-memory state is sufficient before that point — adding Redis earlier means solving a scaling problem that doesn't exist yet, at the cost of real operational
    complexity (see `docs/architecture.md`).
  - *Read first:* **Redis in Action** — exactly why this book is on the list.
