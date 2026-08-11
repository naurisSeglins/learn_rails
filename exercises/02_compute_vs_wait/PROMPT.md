# Exercise 02 — Compute vs. Wait

## Goal

Exercise 01 proved a *fixable* mistake: `blocking_task` monopolizes the thread because it uses the wrong tool (`time.sleep` instead of `asyncio.sleep`) — swap the tool and it's fixed. This
exercise proves something that looks identical in symptom but has no such fix, from ticket 2's notes (`docs/task_learning_notes/phase_0_project_setup/02_setup_postgres_sqlalchemy_alembic.md`,
§6.6.3's premise and "the wall"): waiting can sometimes be delegated, but computation never can, no matter which tool you reach for. Prove it with a task that does genuine CPU-bound work — no
sleep anywhere, nothing to delegate in the first place — and watch it monopolize the thread exactly like `blocking_task` did, for a completely different reason.

## Read first

- Official Python docs, ["Running Blocking Code"](https://docs.python.org/3/library/asyncio-dev.html#running-blocking-code) — the asyncio developer guide's own section on why CPU-bound or
  blocking work freezes the event loop, and what running it in an executor (a separate thread/process) actually means. Read for the *why*, not to implement an executor here — this exercise
  stops at proving the wall exists.
- **Python Concurrency with asyncio** (Matthew Fowler) — its executor / running-CPU-bound-work chapter, once you've confirmed the serialization yourself first. Same book as exercise 01, later
  chapter.

## What to build

A single Python file, `exercise.py`, in this folder. Standard library only — nothing from `pyproject.toml`'s real dependencies.

Expose exactly this function (the self-check imports it by this exact name):

```python
async def cpu_bound_task(name: str, seconds: float) -> None: ...
```

- It must perform real, continuous computation — actual CPU cycles being spent, the whole time — for approximately `seconds`. **No call to `time.sleep` or `asyncio.sleep` anywhere inside it,
  and no `await` of anything either** — there's nothing to `await`, and that absence is the point. One way to structure it: loop doing real arithmetic (counting, hashing, summing — whatever),
  checking elapsed wall-clock time as your stopping condition, rather than telling the OS or runtime to wait on your behalf.
- Print when it starts and when it finishes, same convention as exercise 01's tasks.

Then, in the same file (or an `if __name__ == "__main__":` block), a driver that runs three `cpu_bound_task` calls concurrently via `asyncio.gather` — human-watchable durations like 3s/2s/1s
for your own manual run — and prints the batch's total wall-clock time.

## What "done" looks like

- The batch's total time comes out close to the *sum* of the three durations — the same serialized signature exercise 01's `blocking_task` batch produced.
- Before considering this done, explain in your own words: this serializes exactly like `blocking_task` did — so why doesn't the same fix apply? `blocking_task`'s problem was solved with a
  one-line swap (`asyncio.sleep` instead of `time.sleep`). What would an actual fix for `cpu_bound_task` require instead? (You don't need to implement it — just say what *kind* of tool it would
  take, and why "await it correctly" isn't an option here the way it was for `blocking_task`.)

## Constraints

- Standard library only.
- No `time.sleep`, no `asyncio.sleep`, no `await` inside `cpu_bound_task` — the self-check enforces this directly, not just by convention.
- Don't guess at the timing numbers — run it and read the real output.

## Self-check

`test_exercise.py` in this same folder asserts both the serialization behavior and that no sleep call is hiding inside your implementation, using short synthetic durations (for speed, not
because the mechanism differs). Run it with:

```
uv run pytest exercises/02_compute_vs_wait/
```

Get it green before showing me anything — then walk me through the explanation from "What done looks like" above; I'll review the code alongside that explanation, not instead of it.
