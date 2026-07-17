# Technical Reading List

Sequenced by when each becomes useful for this repo (`game-engine`) specifically — not every book applies to every phase, and a few are only relevant once a companion repo (`bff`, `platform`) exists.

## Reading Order for This Project

1. **Python Concurrency with asyncio** (Matthew Fowler) — start here, before writing the first FastAPI endpoint. The event loop, tasks, and coroutines underneath every async `def` in this stack.
2. **Practical Object-Oriented Design in Ruby (POODR)** (Sandi Metz) — read before writing your first real class. The Ruby code examples don't transfer, but CLAUDE.md's "Minimal & Readable Code" rule *is* this book's philosophy — single responsibility, small classes/methods, no premature abstraction — and it governs every class in this repo regardless of language.
3. **Python Testing with pytest** (Brian Okken) — once you write your first test; this project runs on TDD by default, and pytest's fixture/parametrize model is different enough from RSpec to be worth reading deliberately rather than assumed.
4. **Game Programming Patterns** (Robert Nystrom, free at gameprogrammingpatterns.com) — once you start designing the game engine itself (turn/round phases, representing a queued move as a first-class object, broadcasting state changes).
5. **Dive Into Design Patterns** — once you start extracting service-layer logic for game rules (move validation, battle resolution) out of request handlers.
6. **Multiplayer Game Programming: Architecting Networked Games** (Joshua Glazer & Sanjay Madhav) — once you tackle server-authoritative state and hidden-information handling (the fog-of-war problem) — still the closest thing to a direct playbook for this project's core problem.
7. **Alice and Bob Learn Application Security** (Tanya Janca) — the STRIDE/threat-modeling chapters, for the ticket that threat-models the BFF ↔ game-engine hidden-information boundary once that boundary exists.
8. **OAuth 2 in Action** (Justin Richer & Antonio Sanso) — once the BFF's auth boundary is being built (JWT issuance/verification) — not urgent for game-engine alone, but game-engine needs to *verify* the tokens the BFF issues.
9. **High Performance Browser Networking** (Ilya Grigorik, free at hpbn.co) — the WebSockets chapter, once real-time push "works" and you want to understand why/when it won't scale.
10. **Docker Deep Dive** (Nigel Poulton) — once containerizing this service for the first time.
11. **Kubernetes Up & Running** (Brendan Burns, Joe Beda, Kelsey Hightower) — once deploying to GKE for real, not before.
12. **Patterns of Enterprise Application Architecture** (Martin Fowler) — once the data model (games, units, board state) stops being trivial.
13. **Domain-Driven Design: Tackling Complexity in the Heart of Software** (Eric Evans) — once a bounded context needs explicit modeling — the market service's inventory/trading domain, or a later ranking system.
14. **Enterprise Integration Patterns** — once cross-service Pub/Sub eventing needs more rigor than "publish and hope."
15. **Redis in Action** — once presence/matchmaking needs Redis, or multiple service instances need a shared pub/sub backend.
16. **Learning GitHub Actions** — CI half of the pipeline (test → build → push image), before the `platform` repo's ArgoCD side takes over deployment.
17. **Google Cloud Certified Associate Cloud Engineer Study Guide** — once deploying to GCP for real.
18. **Google BigQuery** — once building analytics/leaderboards (Phase 4-equivalent stretch work).

## Why each is relevant

1. **Python Concurrency with asyncio** — Core asyncio patterns (event loop, tasks, coroutines, gather/queues) underneath every service in this stack.
2. **Practical Object-Oriented Design in Ruby (POODR)** — Source of the Sandi Metz Philosophy habits this project already treats as standing law; principles transfer even though the code examples are Ruby.
3. **Python Testing with pytest** — This project runs on TDD by default; pytest's fixtures/parametrize/`httpx.AsyncClient` request-spec style is the Python-world equivalent of this project's RSpec-request-spec convention.
4. **Game Programming Patterns** — Not framework-specific: State pattern for phase/turn logic, Command pattern for a queued move as a first-class object, Observer for broadcasting state changes.
5. **Dive Into Design Patterns** — Language-agnostic refactoring companion to POODR's principles, for extracting focused service-layer objects.
6. **Multiplayer Game Programming: Architecting Networked Games** — Client-server authority models, state synchronization, and specifically how to avoid leaking hidden information to clients — this project's core problem, independent of stack.
7. **Alice and Bob Learn Application Security** — STRIDE's Information Disclosure category is exactly this project's hidden-information problem, now reframed across a service boundary instead of a single Rails payload.
8. **OAuth 2 in Action** — OAuth2/OIDC, token validation, and the auth boundary between a BFF and backend services like this one.
9. **High Performance Browser Networking** — The WebSockets chapter specifically, for understanding real-time push once "it works" isn't the only question.
10. **Docker Deep Dive** — Container mechanics underneath every service's Dockerfile and the local docker-compose dev loop.
11. **Kubernetes Up & Running** — The canonical reference for how GKE actually schedules, exposes, and scales these services in production.
12. **Patterns of Enterprise Application Architecture** — Data modeling and architectural patterns, useful once game-engine's data model stops being trivial.
13. **Domain-Driven Design** — Bounded contexts, aggregate roots — directly useful once the market service's domain (inventory, trades) needs to be modeled distinctly from game-engine's.
14. **Enterprise Integration Patterns** — Messaging/integration patterns, now genuinely applicable given real inter-service Pub/Sub events instead of in-process Rails callbacks.
15. **Redis in Action** — Caching, pub/sub, rate limiting — relevant to presence/matchmaking and once any service runs multiple instances.
16. **Learning GitHub Actions** — CI pipeline design (test → build → push image) that feeds the GitOps loop described in `docs/architecture.md`.
17. **Google Cloud Certified Associate Cloud Engineer Study Guide** — GCP deployment and infrastructure, now the actual target platform rather than a hypothetical option.
18. **Google BigQuery** — Analytics, usage reporting, data warehousing for later leaderboard/stats work.

## Noted gap

No strong existing candidate yet for a dedicated GitOps/ArgoCD reference, or for whichever SPA framework (React/Vue/etc.) the `frontend` repo ends up using — add one here once those decisions are made and a book search has actually been done, rather than guessing a title now.
