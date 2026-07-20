# Tasks

Single source of truth for status and what to work on next. Update this file in the same session as any work that completes, starts, or gets rescoped.

This repo is the `game-engine` service (see `docs/architecture.md`'s System architecture table). Tickets below are scoped to this repo; companion repos (`bff`, `frontend`, `market`, `platform`) get their own `TASKS.md` once they're created, and a ticket here notes when it depends on one of them existing.

Each task below has:
- a ***Why:*** line — the reason this ticket exists at all, not just what it asks for. If the reason isn't obvious, it's written out; if it's a deeper architectural rationale, it points at the specific line in `docs/architecture.md` rather than repeating it.
- a **Read first** line pointing at the book(s) in `books.md` most relevant to that task's context — not the whole book, just go in with that lens. Some tasks are pure setup/administration with no useful reading; those say so rather than forcing a fit.

**Practical Object-Oriented Design in Ruby (POODR)** isn't tied to one ticket — read it before starting Phase 1. CLAUDE.md's "Minimal & Readable Code (Sandi Metz Philosophy)" rule comes straight from this book and governs every class written from the first model onward, not just the service-object extraction in "Resolve combat" below.

## Current Status

The project has pivoted from Rails to Python/FastAPI/asyncio, deployed as a multi-repo microservices system (see `docs/architecture.md`). All Rails scaffolding has been removed. `uv init` has been run; `pyproject.toml` currently has an empty `dependencies` list and only the dev group populated — the runtime dependencies in Phase 0's first ticket still need to be added. No FastAPI app, no models exist yet.

Game design is unchanged by the stack pivot: a simultaneous-turn, fog-of-war game inspired by both Stratego and Kriegsspiel (see `docs/architecture.md`). Several core mechanics — combat-resolution math, win condition, army selection, timer-expiry behavior — are still open design questions. Tickets that depend on an unresolved question are marked **[BLOCKED]** and shouldn't be started until `docs/architecture.md`'s Open design questions section is resolved.

**MVP scope is deliberately layered, not flat.** Phase 1 builds the simplest possible playable vertical slice — full visibility both ways, fixed identical armies, no setup phase — so there's a working move → combat → winner loop before tackling the project's actual hard problem. Hidden information and fog of war are Phase 2, not Phase 1, by design.

## MVP Definition (Phase 1)

Two players can play a full game against each other, from a fixed starting position through move submission and combat resolution to a declared winner. Both players see the entire board and every opponent unit's full stats at all times — no hidden information, no fog of war. Both start with an identical, hard-coded army already placed in a fixed formation; there is no setup phase — the game begins `in_progress` the moment both players have joined. No matchmaking, no accounts, no polish beyond that. This is intentionally not the finished game — it's the smallest slice that's actually playable end to end, with hidden info and fog of war layered on in Phase 2.

---

## Phase 0 — Project Setup

- [ ] **Initialize the project with uv.** `uv init`, add FastAPI, uvicorn, SQLAlchemy (async) + asyncpg, Alembic, and Pydantic as dependencies via `uv add`. Confirm a minimal FastAPI app boots locally via `uvicorn`.
  - *Why:* each package here has a distinct, non-overlapping job in the request lifecycle — leaving any one out breaks a specific thing, not "the setup" in general.
    - **FastAPI**
      - *What it is:* a Python library for building web APIs — you write a function per route (e.g. "create a game"), tell FastAPI which URL/HTTP method triggers it, and it handles turning an incoming request into a call to your function and your function's return value into an HTTP response. This is the same job Rails' `routes.rb` + controllers did together, just one library instead of two.
      - *Why we use it:* it's the framework every endpoint in this service is built on.
      - *What breaks without it:* you'd be hand-writing HTTP parsing, routing, and response formatting from scratch — solved problems FastAPI gives you for free.
    - **uvicorn**
      - *What it is:* FastAPI only knows *what to do* once a request arrives — it has no idea how to open a network socket or listen on a port. uvicorn is the separate program that does that networking work, and for every request it receives, calls into your FastAPI app to ask "what's the response?" This is Python's equivalent of Puma in Rails: Rails defines your app, Puma is what's actually bound to a port listening for connections.
      - *Why we use it:* FastAPI needs an actual running process serving it — `app = FastAPI()` alone doesn't listen for anything.
      - *What breaks without it:* nothing is listening on any port, so no request can ever reach your app, no matter how correct the code is.
    - **SQLAlchemy (async)**
      - *What it is:* a library that lets you describe database tables as Python classes (a `Game` class instead of a `games` SQL table) and query/save data with Python instead of writing SQL by hand — SQLAlchemy translates your Python into SQL behind the scenes. This is Python's closest equivalent to Rails' ActiveRecord, minus most of Rails' extra "magic" conventions.
      - *Why we use it:* every read/write of a `Game`/`Player`/`Piece` goes through this instead of raw SQL scattered through route handlers.
      - *What breaks without it:* every database interaction becomes a hand-written SQL string, a manually-managed connection, and manual row-to-object conversion — slow to write and an easy way to introduce a SQL injection bug under deadline pressure.
    - **asyncpg**
      - *What it is:* SQLAlchemy doesn't actually know how to speak to Postgres over the network by itself — it needs a lower-level library ("driver") that knows Postgres's specific message format and handles the raw bytes going back and forth. asyncpg is that driver, built specifically to work with Python's `async`/`await` instead of waiting around blocked.
      - *Why we use it:* while one request is waiting on a slow database query, an async driver lets the server go handle a *different* request in the meantime instead of sitting idle doing nothing.
      - *What breaks without it:* using an ordinary (synchronous) driver like `psycopg2` instead would mean that while any one request waits on the database, the entire server process freezes and can't handle any other request at all — which defeats the reason this stack is async in the first place.
    - **Alembic**
      - *What it is:* a tool that records changes to your database's structure (adding a table, adding a column) as small, numbered script files, each one saying how to apply the change and how to undo it. This is the direct equivalent of Rails' `db/migrate` files and `rails db:migrate` — Alembic pairs with SQLAlchemy the way ActiveRecord migrations pair with Rails.
      - *Why we use it:* as the data model changes (a new field on `Piece`, say), you need one repeatable way to apply that change everywhere — your laptop, CI, production.
      - *What breaks without it:* schema changes happen by hand, aren't tracked anywhere, and can't be reliably reproduced across environments or by a second person.
    - **Pydantic**
      - *What it is:* a library for describing the *shape* data should have (e.g. "a Move has a unit ID and a destination, nothing else") as a Python class, which then automatically checks incoming data against that shape and rejects anything that doesn't match. FastAPI uses these same classes to control exactly what fields go out in a response, too.
      - *Why we use it:* it's what makes "reject an illegal move with a generic error" and, later, "the opponent's response never contains a hidden field" actually enforced by the framework rather than something you have to remember to check by hand in every route.
      - *What breaks without it:* you'd be manually validating incoming JSON and manually building outgoing JSON everywhere — and a forgotten manual check is exactly how a hidden rank would accidentally leak later (see Phase 2).
  - *Read first:* **Python Concurrency with asyncio** — enough to understand why the app and its dependencies are async-first, before writing the first route.

- [ ] **Set up Postgres via SQLAlchemy (async) + Alembic.** Configure an async database connection and confirm a first (empty) Alembic migration runs against a local Postgres instance. This service owns its own database — see `docs/architecture.md`'s data-ownership rule.
  - *Why:*
    - **Postgres, not SQLite** — SQLite locks the whole file under concurrent writes, a problem the moment two games are being played at once (see `docs/architecture.md`'s "Postgres, not SQLite" bullet for the full rationale).
    - **This service owning its own database** — rather than sharing one with a future `market` service, is what makes the multi-repo split actually mean something instead of being a monolith with extra network hops (see `docs/architecture.md`'s "One database per service" bullet).
  - *Read first:* none of the current reading list covers SQLAlchemy/Alembic directly — worth a dedicated lookup rather than a full book for this one.

- [ ] **Set up pytest + httpx for request-style specs.** Add `pytest`, `pytest-asyncio`, `httpx` (for `AsyncClient` against the FastAPI app), and `factory_boy` (per CLAUDE.md's Testing Conventions). Confirm `pytest` runs (even with zero tests).
  - *Why:*
    - **pytest-asyncio**
      - *What it is:* a plugin that teaches pytest (the test runner) how to run `async def` test functions. A normal Python function runs straight through top to bottom; an `async def` function is written to pause and resume (e.g. while waiting on a database call), and pytest has no built-in idea how to drive that pause/resume cycle on its own — this plugin adds it.
      - *Why we use it:* your FastAPI routes are `async def` functions, so testing them properly means calling them the same way.
      - *What breaks without it:* an `async def test_...()` either errors outright or silently doesn't run its body the way you'd expect, since plain pytest can't execute it correctly.
    - **httpx's `AsyncClient`**
      - *What it is:* a library for making HTTP requests from Python. Its `AsyncClient` can talk directly to your FastAPI app object in memory — simulating a real request without opening an actual network port or starting a real server — while still exercising your app the same async way a real server would call it.
      - *Why we use it:* this is what CLAUDE.md's "Test Against the Endpoint" actually means in practice — sending a simulated request into the app and checking the real response, the same way Rails' request specs hit routes rather than calling model methods directly.
      - *What breaks without it:* you'd be left testing individual functions in isolation, which CLAUDE.md explicitly says is *not* the primary test layer here — a passing unit test doesn't prove the actual HTTP behavior works end to end.
    - **factory_boy**
      - *What it is:* a library for defining, once, "how to build a valid test `Game`/`Player`/`Piece`" as a reusable factory, instead of constructing the full object by hand inside every test. It's the direct Python equivalent of Rails' FactoryBot — same idea, same lineage (FactoryBot was itself ported from factory_boy).
      - *Why we use it:* CLAUDE.md's Testing Conventions call for factories with traits for meaningful states (e.g. "a game already in progress," "a piece that's already revealed") — this is the tool that provides that.
      - *What breaks without it:* every test needing a database record hand-rolls its own setup code, which duplicates across the suite and quietly drifts out of sync as the model changes.
  - *Read first:* **Python Testing with pytest** — the fixtures/async-test chapter, so config choices here are deliberate.

- [ ] **Add a Dockerfile for local containerization.** A minimal image that runs the FastAPI app via uvicorn — the basis for both local docker-compose use and the eventual GKE deploy.
  - *Why:* building this now, rather than waiting for the Phase 3 deploy ticket, means every ticket from here on can be sanity-checked in the same environment that will eventually run in production. A container-specific bug (a missing system library, a path assumption that only holds on your laptop) is cheap to catch here and expensive to discover for the first time during an actual deploy.
  - *Read first:* **Docker Deep Dive** — image-building fundamentals chapter.

- [ ] **Add the `LICENSE` file.** All Rights Reserved text, per the decision noted in `CLAUDE.md`'s Document Map.
  - *Why:* this is a public repo. Without an explicit license, whether the code can legally be reused by anyone who finds it is ambiguous — "All Rights Reserved" just makes explicit what's already the default, removing that ambiguity.
  - *Read first:* none — this is administrative, not technical.

## Phase 1 — MVP: Core Game Loop

Full visibility both ways, fixed identical armies, no setup phase. See MVP Definition above.

- [ ] **Create a game with a fixed starting army.** A player starts a new game and receives a shareable code/ID for the second player to join; both players are assigned an identical, hard-coded army in a fixed starting formation, and the game begins `in_progress` immediately — no setup phase, no player-driven placement or army selection (see Phase 4 for those, once designed). Acceptance: two players can both be attached to the same `Game` record via that code, with no third player able to join, and both start with the same fixed roster already placed on the board.
  - *Why:* this is the smallest slice that produces a real, shared object two players are actually attached to — every later ticket (moves, combat, win detection) needs a `Game` to operate on, so it has to exist first regardless of what game rules end up being decided.
  - *Read first:* none specific — a straightforward FastAPI router + Pydantic schema exercise.

- [ ] **Submit move orders for a round, with a round timer.** A player can queue movement orders for any subset of their own units during the round's countdown timer (each unit capped by its own movement allowance), then submit the batch. Acceptance: illegal orders (insufficient movement allowance remaining, moving an immobile unit) are rejected with a generic error; a submitted batch stays invisible to the opponent until the round resolves.
  - *Why:* modeling a queued move as a first-class object (rather than a bag of params) up front is what makes both this ticket's own validation and Phase 4's replay ticket tractable later — retrofitting that structure after moves are already scattered through ad-hoc code is much more expensive than starting with it.
  - *Read first:* **Game Programming Patterns** — the Command chapter.
  - *Blocked on:* timer-expiry behavior (auto-submit the queued-so-far batch vs. forced no-op) — see Open design questions in `docs/architecture.md`.

- [ ] **[BLOCKED] Resolve combat.** Moving into conflict with an opponent's unit — via a direct attack order, a crossed path, or both units arriving on the same square (resolved via the bounce-back rule) — triggers a battle. Acceptance criteria can't be written until the combat-resolution math (HP/Attack/Defence formula) is decided — see Open design questions in `docs/architecture.md`. Do not start implementation until that's resolved.
  - *Why:* combat is where two players' independent, simultaneous move batches actually collide — without it, "submit moves" and "declare a winner" have nothing connecting them.
  - *Read first:* **Dive Into Design Patterns** and **Practical Object-Oriented Design in Ruby (POODR)** — on extracting a focused service-layer object. Battle resolution is business logic that doesn't belong in a route handler or model.

- [ ] **[BLOCKED] Detect win conditions.** The win condition itself is an open design question (Flag-capture equivalent vs. something else) — see Open design questions in `docs/architecture.md`. Do not start implementation until that's resolved.
  - *Why:* without an explicit terminal state, a finished game would keep silently accepting moves — this is what turns "the game is over" into an enforced guarantee instead of something the UI just happens to assume.
  - *Read first:* **Game Programming Patterns** — the State chapter, specifically the "terminal state" framing (a state-machine guard, not an ad-hoc `if`).

- [ ] **Publish a round-resolution event.** When a round resolves, this service publishes an event (Pub/Sub) with the outcome. Since MVP has no hidden information yet, one event body is fine for both players — this gets split into per-player-filtered events in Phase 2. Acceptance: a test confirms an event is published containing the resolved round's outcome.
  - *Why:* this is the seam the future `bff` repo will consume to push live updates to a browser connection. Building the publishing mechanism now, even in its simplest unfiltered form, means Phase 2 only has to change *what's in* the event, not invent how events get published from scratch.
  - *Read first:* none of the current list covers Pub/Sub message design directly — a dedicated lookup once this ticket starts.

## Phase 2 — Hidden Information & Fog of War

This is the project's actual core problem (see `CLAUDE.md`) — deliberately tackled only once Phase 1's game loop already works end to end with full visibility, so this phase changes *what's visible*, not the underlying move/combat logic.

- [ ] **Enforce hidden rank in every payload.** Opponent units show position and unit type always; quality tier and full stats stay omitted from the response entirely unless `revealed` is `true`. Acceptance: a test asserts the literal serialized response body never contains an unrevealed opponent unit's quality tier or stats — not just that a UI doesn't render them.
  - *Why:* this is the project's actual reason for existing (see `CLAUDE.md`'s "Core technical challenge") — a client that can inspect network traffic and find an opponent's hidden rank has broken the one guarantee the whole system is built around, no matter what the UI chooses to render.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the chapter on client-server authority and hiding information from clients.

- [ ] **Enforce fog of war in every payload.** Opponent units outside your own units' sight radius are structurally absent from your payload — not present-but-unrevealed, genuinely missing. Acceptance: a test asserts an out-of-range opponent unit is absent from the response body.
  - *Why:* same guarantee as the ticket above, different axis — this one is about *position* leaking rather than *rank* leaking, which is why it's a separate single-purpose ticket instead of folded into the one above.
  - *Read first:* same chapter as above — sight radius is the other half of "client-server authority over what's visible."

- [ ] **Upgrade round-resolution events to per-player filtering.** Now that hidden rank and fog of war exist, the single event from Phase 1 must become a separate, differently-filtered event per affected player — same filtering rule as the HTTP payload above applies to the event body. Acceptance: a test confirms the two players' published events are never identical when hidden information differs between them.
  - *Why:* Phase 1's single shared event was only safe because nothing was hidden yet — leaving it unfiltered now would leak exactly what the two tickets above just spent effort protecting in the HTTP response, just through a different channel.
  - *Read first:* none additional — this is the direct payoff of the two tickets above.

- [ ] **[BLOCKED] Threat-model the hidden-information boundary using STRIDE.** Apply STRIDE's six threat categories — particularly Information Disclosure — to the BFF ↔ game-engine boundary, to identify how the design prevents an opponent's hidden rank from leaking into any API response, event, or log. Acceptance criteria can't be written until the `bff` repo (and its side of that boundary) exists.
  - *Why:* the three enforcement tickets above prove the payload is correct *today* — a structured threat model is what catches the ways a future change (a new field, a debug log, a new event type) could reopen the leak later without anyone noticing during code review.
  - *Read first:* **Alice and Bob Learn Application Security** — the threat-modeling/STRIDE chapters.
  - *Blocked on:* the `bff` repo being created.

## Phase 3 — Hardening

- [ ] **Expose a full-current-state endpoint for reconnection.** A rejoining player's client needs to fetch their own complete, correctly-filtered current view of the game in one call, rather than relying on missed events. Acceptance: the response is identical in shape and filtering to what a live round-resolution event would have contained.
  - *Why:* without this, a player who refreshes or drops mid-game has no way back into a correctly-filtered view except waiting for the next event to arrive — which might never happen if nothing changes while they're gone.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the section on reconnection and state resynchronization.

- [ ] **Deploy.** Containerize and deploy this service to GKE via the `platform` repo's ArgoCD-managed manifests. Acceptance criteria can't be finalized until the `platform` repo exists.
  - *Why:* a game that only runs on one laptop isn't actually shareable — this is what turns the project from "works on my machine" into something a second real person can connect to.
  - *Read first:* **Kubernetes Up & Running** — once this ticket actually starts, not before.
  - *Blocked on:* the `platform` repo being created.

## Phase 4 — Post-MVP Features

- [ ] **Player-driven setup & army selection.** Each player chooses their army composition and places their units in a formation of their choosing before the game starts, replacing Phase 1's hard-coded fixed army. Acceptance: a player cannot see the opponent's placement during setup; the game only moves to `in_progress` once both players have finished placing.
  - *Why:* Phase 1's hard-coded army was a deliberate MVP simplification, not the target design — army composition and placement choices are a core part of what makes a Stratego-like actually interesting strategically, so this is where the game becomes the game it's meant to be.
  - *Read first:* **Game Programming Patterns** — the State chapter. "Setup" vs "in progress" vs "finished" is exactly the state-machine problem that chapter is about.
  - *Note:* how a player's army composition/roster is chosen is still an open design question (see `docs/architecture.md`) — this ticket only covers placing a given army, not assembling one.

- [ ] **Matchmaking queue.** Players can join a queue and be auto-paired instead of needing a manually shared game ID. Folded into this repo as an internal module for now — split into its own service later only if it earns that separation (see `docs/architecture.md`).
  - *Why:* without it, playing a game requires already knowing a specific other person and manually sharing a link/code — this removes that requirement.
  - *Read first:* **Patterns of Enterprise Application Architecture** — general data-modeling patterns apply here (a queue is just state + a matching query). If the queue moves to Redis for speed, **Redis in Action** is the natural follow-up.

- [ ] **Spectator mode.** A third party can watch a game in progress without being able to see hidden information belonging to either player.
  - *Why:* extends the exact per-viewer filtering logic Phase 2 already built to a third kind of viewer, rather than needing new infrastructure — a good test of whether that filtering was actually built generically or accidentally hard-coded to "exactly two players."
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
  - *Read first:* **Patterns of Enterprise Application Architecture** — for modeling the rating/history data cleanly. **Domain-Driven Design** is a possible deeper follow-up if the rating rules grow complex enough to need a dedicated domain model.

- [ ] **Redis-backed presence/pub-sub.** Only needed once this service (or matchmaking) runs more than one instance, or needs shared presence state.
  - *Why:* a single running process's in-memory state is sufficient before that point — adding Redis earlier means solving a scaling problem that doesn't exist yet, at the cost of real operational complexity (see `docs/architecture.md`).
  - *Read first:* **Redis in Action** — exactly why this book is on the list.
