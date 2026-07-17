# Tasks

Single source of truth for status and what to work on next. Update this file in the same session as any work that completes, starts, or gets rescoped.

This repo is the `game-engine` service (see `docs/architecture.md`'s System architecture table). Tickets below are scoped to this repo; companion repos (`bff`, `frontend`, `market`, `platform`) get their own `TASKS.md` once they're created, and a ticket here notes when it depends on one of them existing.

Each task below has a **Read first** line pointing at the book(s) in `books.md` most relevant to that task's context — not the whole book, just go in with that lens. Some tasks are pure setup/administration with no useful reading; those say so rather than forcing a fit.

**Practical Object-Oriented Design in Ruby (POODR)** isn't tied to one ticket — read it before starting Phase 1. CLAUDE.md's "Minimal & Readable Code (Sandi Metz Philosophy)" rule comes straight from this book and governs every class written from the first model onward, not just the service-object extraction in "Resolve combat" below.

## Current Status

The project has pivoted from Rails to Python/FastAPI/asyncio, deployed as a multi-repo microservices system (see `docs/architecture.md`). All Rails scaffolding has been removed. This repo is currently empty except for docs — no Poetry project, no FastAPI app, no models exist yet. Phase 0 below sets up the Python project from scratch.

Game design is unchanged by the stack pivot: a simultaneous-turn, fog-of-war game inspired by both Stratego and Kriegsspiel (see `docs/architecture.md`). Several core mechanics — combat-resolution math, win condition, army selection, timer-expiry behavior — are still open design questions. Phase 1 tickets below reflect what's already decided; tickets that depend on an unresolved question are marked **[BLOCKED]** and shouldn't be started until `docs/architecture.md`'s Open design questions section is resolved.

## MVP Definition

Two players can play a full game against each other, from setup to a declared winner, with hidden information and fog of war correctly enforced. This repo (`game-engine`) covers the full authoritative game logic and hidden-info boundary; an actual browser-playable MVP additionally requires the `bff` and `frontend` repos to exist (not yet created) — until then, "playable" means exercised through request specs and/or a thin HTTP client, not a real UI. No matchmaking, no accounts, no polish beyond that.

---

## Phase 0 — Project Setup

- [ ] **Initialize the Poetry project.** `poetry init`, add FastAPI, uvicorn, SQLAlchemy (async) + asyncpg, Alembic, and Pydantic as dependencies. Confirm a minimal FastAPI app boots locally via `uvicorn`.
  - *Read first:* **Python Concurrency with asyncio** — enough to understand why the app and its dependencies are async-first, before writing the first route.

- [ ] **Set up Postgres via SQLAlchemy (async) + Alembic.** Configure an async database connection and confirm a first (empty) Alembic migration runs against a local Postgres instance. This service owns its own database — see `docs/architecture.md`'s data-ownership rule.
  - *Read first:* none of the current reading list covers SQLAlchemy/Alembic directly — worth a dedicated lookup rather than a full book for this one.

- [ ] **Set up pytest + httpx for request-style specs.** Add `pytest`, `pytest-asyncio`, and `httpx` (for `AsyncClient` against the FastAPI app). Confirm `pytest` runs (even with zero tests).
  - *Read first:* **Python Testing with pytest** — the fixtures/async-test chapter, so config choices here are deliberate.

- [ ] **Add a Dockerfile for local containerization.** A minimal image that runs the FastAPI app via uvicorn — the basis for both local docker-compose use and the eventual GKE deploy.
  - *Read first:* **Docker Deep Dive** — image-building fundamentals chapter.

- [ ] **Add the `LICENSE` file.** All Rights Reserved text, per the decision in `docs/architecture.md`.
  - *Read first:* none — this is administrative, not technical.

## Phase 1 — MVP: Core Game Loop

- [ ] **Create a game.** A player can start a new game and receive a shareable code/ID for the second player to join. Acceptance: two players can both be attached to the same `Game` record via that ID, with no third player able to join.
  - *Read first:* none specific — a straightforward FastAPI router + Pydantic schema exercise.

- [ ] **Unit setup phase.** Each player places their full army on their own half of the board, in whatever formation they choose, before the game starts. Acceptance: a player cannot see the opponent's placement during setup; the game only moves to "in progress" once both players have finished placing.
  - *Read first:* **Game Programming Patterns** — the State chapter. "Setup" vs "in progress" vs "finished" is exactly the state-machine problem that chapter is about, and getting the states explicit now avoids scattered boolean flags later.
  - *Note:* how a player's army composition/roster is chosen is still an open design question (see `docs/architecture.md`) — this ticket only covers placing a given army, not assembling one.

- [ ] **Submit move orders for a round, with a round timer.** A player can queue movement orders for any subset of their own units during the round's countdown timer (each unit capped by its own movement allowance), then submit the batch. Acceptance: illegal orders (insufficient movement allowance remaining, moving an immobile unit) are rejected with a generic error that reveals no hidden state; a submitted batch stays invisible to the opponent until the round resolves.
  - *Read first:* **Game Programming Patterns** — the Command chapter. Modeling a queued move as a first-class object (rather than a bag of params) is what makes validation, and later replay, tractable.
  - *Blocked on:* timer-expiry behavior (auto-submit the queued-so-far batch vs. forced no-op) — see Open design questions in `docs/architecture.md`.

- [ ] **[BLOCKED] Resolve combat.** Moving into conflict with an opponent's unit — via a direct attack order, a crossed path, or both units arriving on the same square (resolved via the bounce-back rule) — triggers a battle. Acceptance criteria can't be written until the combat-resolution math (HP/Attack/Defence formula) is decided — see Open design questions in `docs/architecture.md`. Do not start implementation until that's resolved.
  - *Read first:* **Dive Into Design Patterns** and **Practical Object-Oriented Design in Ruby (POODR)** — on extracting a focused service-layer object. Battle resolution is business logic that doesn't belong in a route handler or model; this is the point where that extraction should happen, not later.

- [ ] **Enforce hidden information and fog of war in every payload.** Opponent units outside your sight radius are structurally absent from your payload. Opponent units within radius show position and unit type only — quality tier and full stats stay omitted unless `revealed` is `true`. Acceptance: a test asserts the literal serialized response body for one player never contains an out-of-range opponent unit, and never contains an in-range-but-unrevealed opponent unit's quality tier or stats — not just that a UI doesn't render them.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the chapter on client-server authority and hiding information from clients. This is the single most directly relevant chapter in the whole reading list to a single task.

- [ ] **Publish per-player-filtered round-resolution events.** When a round resolves, this service publishes an event (Pub/Sub) per affected player, containing only what that player is entitled to see — the same filtering rule as the HTTP payload above applies to the event body. Acceptance: a test confirms the two players' published events are never identical when hidden information differs between them. (Actually pushing this to a browser over a live connection is the `bff` repo's job, once it exists — this ticket only covers correct publication.)
  - *Read first:* none of the current list covers Pub/Sub message design directly — a dedicated lookup once this ticket starts.

- [ ] **[BLOCKED] Detect win conditions.** The win condition itself is an open design question (Flag-capture equivalent vs. something else) — see Open design questions in `docs/architecture.md`. Do not start implementation until that's resolved.
  - *Read first:* **Game Programming Patterns** — the State chapter again, specifically the "terminal state" framing (a finished game shouldn't accept further moves, which is a state-machine guard, not an ad-hoc `if`).

## Phase 2 — Hardening

- [ ] **Expose a full-current-state endpoint for reconnection.** A rejoining player's client needs to fetch their own complete, correctly-filtered current view of the game in one call, rather than relying on missed events. Acceptance: the response is identical in shape and filtering to what a live round-resolution event would have contained.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — the section on reconnection and state resynchronization; this is a well-known hard problem in networked games generally, not specific to this project.

- [ ] **[BLOCKED] Threat-model the hidden-information boundary using STRIDE.** Apply STRIDE's six threat categories — particularly Information Disclosure — to the BFF ↔ game-engine boundary, to identify how the design prevents an opponent's hidden rank from leaking into any API response, event, or log. Acceptance criteria can't be written until the `bff` repo (and its side of that boundary) exists.
  - *Read first:* **Alice and Bob Learn Application Security** — the threat-modeling/STRIDE chapters.
  - *Blocked on:* the `bff` repo being created.

- [ ] **Deploy.** Containerize and deploy this service to GKE via the `platform` repo's ArgoCD-managed manifests. Acceptance criteria can't be finalized until the `platform` repo exists.
  - *Read first:* **Kubernetes Up & Running** — once this ticket actually starts, not before.
  - *Blocked on:* the `platform` repo being created.

## Phase 3 — Post-MVP Features

- [ ] **Matchmaking queue.** Players can join a queue and be auto-paired instead of needing a manually shared game ID. Folded into this repo as an internal module for now — split into its own service later only if it earns that separation (see `docs/architecture.md`).
  - *Read first:* **Patterns of Enterprise Application Architecture** — general data-modeling patterns apply here (a queue is just state + a matching query). If the queue moves to Redis for speed, **Redis in Action** is the natural follow-up.

- [ ] **Spectator mode.** A third party can watch a game in progress without being able to see hidden information belonging to either player.
  - *Read first:* **Multiplayer Game Programming: Architecting Networked Games** — a spectator is a third "view" of the same authoritative state, which is the same per-viewer filtering problem as the two players, just with an even more restricted view.

- [ ] **Move history / replay.** A finished game can be replayed move-by-move after the fact.
  - *Read first:* **Game Programming Patterns** — the Command chapter, revisited. If moves were modeled as first-class command objects back in Phase 1, replay is close to free; this task is really where that earlier decision pays off or doesn't.

## Phase 4 — Stretch / Scale

- [ ] **Simple AI opponent.** A heuristic (non-learning) bot a player can practice against.
  - *Read first:* none of the current reading list covers game AI algorithms in depth — worth adding a dedicated book (e.g. on minimax/heuristic search) if this task gets picked up.

- [ ] **Ranking system.** Track win/loss record and a simple rating (e.g. Elo) across games.
  - *Read first:* **Patterns of Enterprise Application Architecture** — for modeling the rating/history data cleanly. **Domain-Driven Design** is a possible deeper follow-up if the rules around rating calculation grow complex enough to need a dedicated domain model.

- [ ] **Redis-backed presence/pub-sub.** Only needed once this service (or matchmaking) runs more than one instance, or needs shared presence state — see `docs/architecture.md` for why this is deferred rather than done up front.
  - *Read first:* **Redis in Action** — exactly why this book is on the list.
