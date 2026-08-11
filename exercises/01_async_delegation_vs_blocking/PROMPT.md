# Exercise 01 — Async Delegation vs. Blocking

## Goal

Prove for yourself, with a real running script, the exact distinction from ticket 2's notes (`docs/task_learning_notes/phase_0_project_setup/02_setup_postgres_sqlalchemy_alembic.md`, sections
6.6.1–6.6.3 and 6.7): `await`ing something delegates the wait to the runtime and frees the event loop; genuinely blocking code monopolizes the one thread instead. Don't take that on faith from
an explanation — watch it happen, in your own stack (`asyncio`), not the JS examples in the notes.

## Read first

- Official Python docs, ["Coroutines and Tasks"](https://docs.python.org/3/library/asyncio-task.html) — the exact API this exercise needs (`async def`/`await`, `asyncio.sleep`,
  `asyncio.gather`, `asyncio.run`), plus its own warning against calling blocking code from inside a coroutine, which is exactly the mistake `blocking_task` is built to demonstrate.
- **Python Concurrency with asyncio** (Matthew Fowler) — the event-loop/coroutines chapters, already queued in `books.md` for this exact moment; the deeper "why" behind the timing numbers,
  once the syntax itself is working.

## What to build

A single Python file, `exercise.py`, in this folder. Standard library only (`asyncio`, `time`) — nothing from `pyproject.toml`'s real dependencies, no FastAPI, no database.

Expose exactly these two functions (the self-check imports them by these exact names):

```python
async def waiting_task(name: str, seconds: float) -> None: ...
async def blocking_task(name: str, seconds: float) -> None: ...
```

- `waiting_task` should "wait" using the delegated mechanism from 6.6.1 — the one where the countdown never occupies the thread.
- `blocking_task` should "wait" using the opposite mechanism from 6.6.1 — the one that runs directly on the thread's own call stack, monopolizing it for the full duration — while still being declared `async def` (i.e. the mistake is using the wrong *tool* internally, not skipping `async def` on the function itself).
- Both should print when they start and when they finish, so a human watching stdout can see the difference in real time — not just infer it from a final number.

Then, in the same file (or a `if __name__ == "__main__":` block), write your own small driver that:
1. Runs three `waiting_task` calls concurrently (e.g. via `asyncio.gather`) with different durations (something human-watchable, like 3s / 2s / 1s), and prints the total wall-clock time the batch took.
2. Runs three `blocking_task` calls the same way, with the same durations, and prints that batch's total wall-clock time too.
3. Prints both totals side by side.

## What "done" looks like

- The `waiting_task` batch's total time is close to the *longest* individual duration (~3s for a 3/2/1 batch) — not the sum.
- The `blocking_task` batch's total time is close to the *sum* of all three (~6s for a 3/2/1 batch).
- You can explain, in your own words, exactly why those two numbers differ — which one is actually delegated off the single thread, and which one is occupying it — before considering this done. That explanation is the actual point; the code is just how you generate the evidence for it.

## Constraints

- Standard library only.
- One file is enough — no classes needed, no need to touch this project's real app or database.
- Don't guess at the timing numbers — run it and read the real output.

## Self-check

`test_exercise.py` in this same folder asserts the timing behavior automatically, using much shorter synthetic durations than your own manual demo (for speed, not because the mechanism differs).
Run it with:

```
uv run pytest exercises/01_async_delegation_vs_blocking/
```

Get it green before showing me anything — then walk me through your explanation from "What done looks like" above; I'll review the code alongside that explanation, not instead of it.
