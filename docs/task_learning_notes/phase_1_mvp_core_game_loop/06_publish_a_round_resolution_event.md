# Ticket 5 — Publish a round-resolution event: Theoretical Basis

Written *before* starting this ticket — see `01_create_a_game_with_a_fixed_starting_army.md` for what this format means and why.

## The Pub/Sub client isn't async-native — a direct callback to the coloring problem

Worth reading before touching any code, since it's a real, concrete instance of the exact problem already studied
(`../phase_0_project_setup/02_setup_postgres_sqlalchemy_alembic.md`'s detour). The standard `google-cloud-pubsub` Python client's `publisher.publish(...)` call returns a
`concurrent.futures.Future`, not an `asyncio` awaitable — it's built on gRPC's own threading model, not asyncio's. Calling `.result()` on that future to wait for confirmation would **block the
event loop** — the exact failure mode already studied in the `buy_coins.js` detour, except here it would happen inside this project's own FastAPI route, freezing the one thread serving every
other request while waiting for GCP to acknowledge one message.

## Two real ways to handle this, worth deciding before writing the route

- **Fire-and-forget** — call `publish(...)` and don't wait for the future to resolve at all. Simplest, but loses inline error visibility.
- **Bridge the blocking call properly** — run the blocking `.result()` call in a separate thread via `asyncio.get_event_loop().run_in_executor(...)`, so the *waiting* happens off the main thread
  (the same background-thread-pool idea already covered for Node's disk reads) while the route itself stays non-blocking.

Given this project's stated care about correctness, the second option is worth doing properly from the start rather than defaulting to fire-and-forget and revisiting it later.
