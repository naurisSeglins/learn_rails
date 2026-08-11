# Ticket 2 — Submit move orders for a round, with a round timer: Theoretical Basis

Written *before* starting this ticket — see `01_create_a_game_with_a_fixed_starting_army.md` for what this format means and why.

## What "queue an order" looks like concretely

Since orders must be validated and stored, not applied, until the round resolves, this needs a real place to live between "submitted" and "applied." The direct approach: a `Move` (or
`MoveOrder`) table — one row per submitted order, foreign-keyed to the `Game` and to the `Piece` being moved, holding the destination — created the same way a `Game` is, but *not* changing any
`Piece`'s position yet. Round resolution (tickets 3/4, blocked) is what later reads all pending `Move` rows for a round and applies them together.

## The actual hard part: the round timer itself

Worth flagging before starting, since it's a genuinely new mechanism, not just "store a row." Something needs to fire server-side once the countdown expires — nothing is making a request at
that moment, so it can't be "wait inside the request handler." Two real approaches:
- An in-process background task (`asyncio.create_task` scheduling a coroutine after a delay, or a lightweight scheduler) — simplest to start with, but tied to this one process's lifetime; a
  restart loses an in-flight timer.
- A durable scheduler (a row storing "resolve this round at time X," checked periodically, or a dedicated scheduling service) — more robust, more setup.

Given this project's current single-instance scale, the in-process approach is the reasonable starting point — worth knowing explicitly *why* it's the simpler, less durable option, so upgrading
it later (once Phase 5's multi-instance concerns are real) isn't a surprise.

## A race condition worth thinking about ahead of time

What happens if the timer fires at the exact moment a submission is being processed? Round resolution needs to read "all `Move` rows submitted before the deadline" as one atomic operation, not
two separate steps that could interleave with a late arrival. Worth deciding before writing either piece: does a late submission get rejected outright (an explicit lateness check on arrival), or
does resolution itself define the cutoff (only rows that existed when resolution began count)? Same category of question as the already-open "timer-expiry behavior" design question in
`docs/architecture.md` — worth resolving there, not improvised mid-implementation.
