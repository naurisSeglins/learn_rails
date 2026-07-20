# Architecture

## What this project is

A two-player tactical strategy game playable in the browser, inspired by Stratego's hidden-information combat and Kriegsspiel's simultaneous, umpire-adjudicated turns — fog of war and blind orders resolved each round, rather than classic alternating single-piece moves. Each round, both players privately queue movement orders for their units, submit them blind to each other, and the round resolves at once, with the server acting as Kriegsspiel's umpire: revealing to each side only what their own units could plausibly see. Built to learn a Python/FastAPI, cloud-native microservices stack hands-on rather than follow a course passively — previously built on Rails; the game design carries over unchanged, only the implementation stack has changed.

This project borrows Stratego's hidden-rank idea and Kriegsspiel's simultaneous, fog-of-war turn structure as starting points, not a spec to replicate — BoardGameArena and DeepMind's "DeepNash" research already cover classic Stratego well. This is a learning/portfolio project with its own evolving rules, described below.

## System architecture

The system is split across multiple repositories, each independently deployable, rather than a single monolith. **This repo (`learn_rails`) is the `game-engine` service** — it owns the board, the game rules, and the hidden-information boundary described below. It does not serve a web page or hold player-facing auth; that's the BFF's job.

| Repo | Role | Status |
|---|---|---|
| `game-engine` (this repo) | Board state, turn/round resolution, combat, hidden-info enforcement. Owns its own Postgres database. | In progress |
| `bff` | Backend-for-Frontend: verifies the player's JWT, aggregates calls to game-engine/market, terminates player WebSocket connections and fans out per-player filtered updates. | Not yet created — created when its phase starts |
| `frontend` | The SPA the player's browser actually loads. Talks only to the BFF, never directly to game-engine. | Not yet created |
| `market` | Post-MVP: item trading/economy. Different bounded context (inventory, transactions) from live match state — its own service, own database. | Not yet created |
| `platform` (a GoCardless-`anu`-style repo) | Kubernetes manifests, Terraform, alerting, and the ArgoCD "app-of-apps" root — the GitOps source of truth for how every service gets deployed. Contains no application logic. | Not yet created |

Each service owns its own Postgres database; no service queries another's tables directly. A service that needs data it doesn't own calls that service's API (synchronous, when the answer is needed immediately) or consumes an event it published (when the caller only needs to know something happened, not to block on the answer).

Local development across multiple repos assumes they're checked out as sibling directories on disk; the compose/orchestration file describing how to run them together lives in the `platform` repo once it exists, not in any one service's repo.

## Game rules (reference)

Rules are still being finalized — anything not covered here, or flagged below as an open question, shouldn't be assumed when implementing.

- **Board and setup.** 10x10 square grid. Players choose their army, then place their units in a formation of their choosing on their own territory before play starts. How army composition is chosen is still open — see Open design questions.
- **Simultaneous rounds.** Turns are not alternating. Each round has a countdown timer; during it, both players privately queue movement orders for any subset of their units, each moving up to its own movement allowance (a fixed number of squares per round, set by unit class — e.g. heavy infantry 1 square, light infantry 2, horseman 3–4). Movement isn't restricted to a straight line: a unit can change direction between squares as long as it still has moves remaining. Neither player sees the other's queued orders before submitting. Once both submit, the round resolves ("rolling phase") and both batches are applied together.
- **Fog of war.** Each unit type has a fixed sight radius in squares. An enemy unit is visible only while within range of at least one of your own units. Once spotted, its position and unit type (e.g. infantry, horseman, archer) are shown — but not its quality tier (e.g. veteran vs regular, heavy vs light), which stays hidden until combat reveals full stats.
- **Combat triggers**, during round resolution, in any of three ways:
  1. A player deliberately orders a unit to attack an enemy unit's current visible position (only the position needs to be visible — its quality tier doesn't).
  2. Two opposing units' paths cross while moving (e.g. they'd swap squares or pass through each other).
  3. Two opposing units would end the round on the same square.

  For (2) and (3), the resolution rule is **bounce-back**: the conflicting units each stop one square short of completing that step, ending adjacent to each other, and combat triggers there instead. This keeps "at most one unit per square" as an invariant — no stacking.
- **Combat resolution mechanics** — units have HP, Attack, and Defence stats rather than a single rank, and fights may take more than one exchange to resolve. Not yet finalized — see Open design questions.
- **Win condition** — not yet finalized. The roster is moving away from classic Stratego pieces (no confirmed Flag/Bomb/Spy/Marshal equivalents), so "capture the Flag" may not carry over. See Open design questions.

## Open design questions

Known-unresolved as of this writing. Don't assume an answer when implementing — check back here or ask first.

- **Combat math.** How do HP/Attack/Defence combine to resolve a fight? Single-exchange with one instant winner (as in classic Stratego), or can a fight span multiple resolution rounds while a unit's HP depletes?
- **Timer expiry.** If a player doesn't submit their move batch before the round timer runs out, do their queued-so-far orders auto-submit, or is it treated as a forced no-op (units stay put)?
- **Army selection.** Do both players start from an identical fixed roster (like Stratego's fixed 40 pieces), or do they draft their own mix from a shared point budget?
- **Win condition & special rules.** Does a Flag-capture (or equivalent) objective still exist? Do any Spy/Marshal/Miner/Bomb-style asymmetric matchups carry over, given the roster is now infantry/horseman/archer-style units with quality tiers instead of fixed ranks?

## Tech stack decisions

- **Python, FastAPI, asyncio, uv.** FastAPI's async request handling and Pydantic models are the core of every service. uv manages dependencies and the Python interpreter itself, per repo.
- **Postgres, not SQLite.** SQLite serializes every write across the whole database file — with multiple concurrent games all writing moves at once, this leads to "database is locked" errors under real load. Postgres handles concurrent writes properly.
- **One database per service.** Each service (game-engine, later market) owns its own Postgres database — no cross-service joins, no shared schema. At this project's scale, that's one Cloud SQL instance with a separate database and credentials per service, not a separate instance per service (a full separate instance per service is the more realistic production pattern, but billed continuously regardless of load — not worth it yet at two players).
- **REST for actions, WebSocket + Pub/Sub for push — through the BFF, not directly to game-engine.** A move is naturally "create a move resource" — the client `POST`s it to the BFF, which forwards it to game-engine for validation and persistence. The BFF terminates the player's WebSocket connection and subscribes to Pub/Sub events published by game-engine (e.g. "round resolved"), then pushes a per-player-filtered update down that player's socket. This is the same request/action-vs-push split the original Rails design used (there, ActionCable played the push role); the BFF is now where that push logic lives, since it's the service the frontend actually talks to.
- **Redis for ephemeral state, Pub/Sub for durable events — different jobs, not interchangeable.** Redis holds fast, disposable state: which players are currently connected, WebSocket presence, matchmaking queue. GCP Pub/Sub carries events that must not be silently dropped if a consumer was briefly offline (e.g. a market trade completing while a player was disconnected). Reconnecting into a live game doesn't need event replay — the client re-fetches current authoritative state from game-engine (via the BFF) and resubscribes for future deltas; durability matters for cross-service notifications, not for the live board itself.
- **Kubernetes (GKE) + ArgoCD (GitOps).** Each service is deployed independently; the `platform` repo holds the manifests ArgoCD syncs into the cluster. Local dev uses docker-compose (or Tilt/Skaffold) against locally built images, not a live cluster, so the day-to-day inner loop doesn't require Kubernetes at all.
- **JWT-based auth, verified independently by each service.** The BFF (or a dedicated auth service / GCP Identity Platform, TBD) issues a short-lived signed JWT; game-engine and market verify the signature locally rather than querying a central session store per request — the standard pattern once more than one service needs to recognize the same user.

## Data model (conceptual)

Owned entirely by game-engine's own Postgres database — no other service reads or writes these tables directly.

- `Game` — the match: board dimensions, current turn, status (setup / in_progress / finished), winner. MVP skips `setup` entirely — games start directly `in_progress` with a fixed army (see `TASKS.md` Phase 1); `setup` comes back once player-driven placement lands (Phase 4).
- `Player` — one of the two participants in a `Game`.
- `Piece` — belongs to a `Player` and a `Game`; has a rank, a position, and a `revealed` flag.

The `revealed` flag is the core of the hidden-information design (below): it starts `false` for every piece and flips to `true` only when that piece is involved in combat — the moment the game's actual rules say both ranks become visible.

## Hidden information handling

This is the hardest and most important part of the system, and it now spans a service boundary rather than living inside one Rails app — the guiding principle hasn't changed: **the client should never possess a secret it isn't entitled to — not "possess it but hide it with CSS."** See the STRIDE threat-modeling ticket in `TASKS.md` for a structured pass over this boundary once it exists.

### Server-authoritative state, per-player filtered views

The full board — every piece, every rank, both players' armies — exists only in game-engine's database. It is never returned as-is, not even to the BFF. Every time state changes (a move, a battle), game-engine computes a *separate JSON payload for each player*:
- Your own pieces: full rank, always.
- Opponent's pieces: position only. Rank is omitted from the payload entirely wherever `revealed` is `false` — not sent as `null`, not sent and hidden client-side. If the field isn't in the JSON, there's nothing to find by inspecting network traffic. This applies equally to the API response game-engine gives the BFF and the event it publishes to Pub/Sub — an event payload is just as much "the wire" as an HTTP response.

### The `revealed` flag drives the view

A piece's rank enters the opponent's payload only once `revealed` flips to `true`, which happens only at the moment two pieces collide in combat (the actual game-rule moment where both ranks become visible). Everything else about the data model can be inferred from this one flag plus "who is asking."

### Per-player WebSocket streams, not a shared game channel

The most important structural decision, and the easiest one to get wrong: if both players' connections subscribed to one shared Pub/Sub topic or WebSocket room and the BFF broadcast one message into it, both players would receive the *identical* payload — meaning anything in that message is visible to both, no matter how carefully the JSON was built for one of them. Each player needs their **own private stream** (their own WebSocket connection, filtered before it's written to that socket), with game-engine's published event carrying enough information for the BFF to compute — and send — a differently-filtered payload per player.

### Secondary leak vectors

- **Move rejection messages** must not hint at *why* a move failed in a way that reveals hidden state. A "no" response should carry no more information than a "yes" response would.
- **Accidental full serialization** — never take a raw database record and dump it to JSON directly instead of routing it through the per-player filtered view. This is the kind of thing that happens by accident later (a debug log, a "just send the whole object" shortcut under time pressure, a Pub/Sub event published from the wrong layer), so the serialization boundary is worth being deliberate about — now in two places (game-engine's API responses *and* its published events) instead of one.

### How to verify it

Test the literal payload sent to a given player — the HTTP response game-engine returns, and the event it publishes — and assert the opponent's unrevealed piece ranks are structurally absent from it, not that the rendered page doesn't display them. The DOM not showing something and the payload not containing it are different guarantees; only the second one is real security.
