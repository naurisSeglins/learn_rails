# Ticket 1 — Create a game with a fixed starting army: Theoretical Basis

Written *before* starting this ticket — like a physics lab's theoretical basis, prepared ahead of the work, not a report of what happened during it. Goes deeper than `TASKS.md`'s own Industry
Context/How-it-works bullets. Once implemented, real debugging/discussion notes get added here too, alongside this prep material, not replacing it.

## What "create a resource" means mechanically in FastAPI

A route like `@app.post("/games")` receives an HTTP POST; FastAPI parses/validates the body against a Pydantic request-schema class, calls the route function with that already-validated object,
and whatever the function returns gets serialized through a `response_model` if one's declared. FastAPI won't infer "this created something" on its own — the conventionally correct status for a
successful creation is `201 Created`, not the default `200`, set explicitly via the route decorator's `status_code=201`.

## The identifier — a real design decision, not a detail

This ticket only needs one thing decided at creation: what identifies a `Game` to future requests. Two real options:
- An auto-incrementing integer primary key (Postgres `SERIAL`) — simple, but *enumerable*: someone could try `/games/1`, `/games/2`, `/games/3`... and discover other players' in-progress games,
  since sequential integers reveal how many games exist and let anyone guess a valid one.
- A random, non-sequential identifier (a UUID, or a shorter random alphanumeric code) — can't be guessed by incrementing, doesn't reveal how many games exist.

Given this whole project's premise is a hidden-information game, exposing *which games exist* to anyone who can count is a small information leak worth avoiding from the start, not retrofitting
later. Worth deciding this — a UUID or short random code, not a bare auto-incrementing integer — before writing the `Game` model's primary key, not after.

## Testing this with a clean database each time

`httpx.AsyncClient` drives a real request through the app, but each test needs the database in a known, clean state beforehand — otherwise a test asserting "there are 0 games" fails on the
second run because the first test's game is still sitting in the table. The usual pattern: a pytest fixture that creates a fresh schema (or wraps each test in a transaction rolled back
afterward) before every test function — worth setting up as its own small piece of test infrastructure before writing the first real test, not improvised mid-test.
