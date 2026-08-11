# Exercises

Deliberate practice, separate from the real work tracked in `TASKS.md` — a lower-stakes place to build a skill before (or instead of) hitting it cold in the middle of real ticket work. Not part of the `game-engine` service itself; the `exercises/` folder gets excluded from the Docker image once that ticket lands.

## How this works

- I write the prompt — goal, constraints, what "done" looks like — and never the solution, same rule as everywhere else in this project.
- Where it's feasible, I also write a small pytest self-check (`test_exercise.py`) so you get instant, objective feedback before showing me anything.
- **Before writing a new exercise, read this file and the most recently completed exercise's `PROMPT.md`/`test_exercise.py`** — not optional, not "if it seems relevant." Confirmed necessary
  (2026-08-04): exercise 02 was created having actually read exercise 01's files first, but nothing enforced that beyond habit — write it down so it doesn't quietly lapse on some future exercise.
- **Self-checks must be tight enough that a broken or parameter-ignoring implementation cannot accidentally pass.** Confirmed the hard way (2026-08-04, exercise 01): `waiting_task` used
  `asyncio.timeout(seconds)` bare — never awaited, a complete no-op — and the test still went green, because it only asserted an *upper* bound (`elapsed < max(DURATIONS) * 2`); "finished
  instantly because it's broken" and "finished quickly because it's correctly delegated" both satisfy an upper-bound-only check. Two concrete rules that follow:
  - Where a numeric range represents "correct," assert **both** directions (a lower bound catching "did nothing / finished suspiciously fast," an upper bound catching "still wrong the other
    way"), not just whichever direction the obvious failure mode points toward.
  - Test each task's behavior against **its own individual parameter** (e.g. a solo call with one duration, asserting elapsed scales with *that* duration), not only an aggregate batch total —
    a hardcoded, parameter-ignoring implementation tuned to the right ballpark can satisfy a batch-only check.
- You write your solution in the exercise's own folder under `exercises/`.
- Paste the code or point me at the file when ready — I review it properly: what's right and why, what's wrong and why, not just "looks good."
- When an exercise actually closes a real gap, the matching entry in `~/.claude/CLAUDE.md`'s Skill Level & Focus Areas section gets updated to reflect it — that section only means something if it stays current.
- New exercises get proposed proactively when a real gap surfaces during normal ticket work (I'll ask before assigning one, never spring it mid-task unannounced), or whenever you ask for one directly.

## Log

Newest first, same convention as `TASKS.md`'s Current Status — add a new entry when an exercise is assigned, and update its own status in place as it moves from assigned → reviewed, rather than duplicating entries.

### 02 — Compute vs. wait

**Status: assigned.** Follows directly from exercise 01, once §6.6.3 of the same notes file was consolidated and deepened (the "premise" and "the wall" — computation is never delegable, no
matter the tool, unlike a fixable blocking-wait mistake). Proves a CPU-bound task with no sleep anywhere still monopolizes the thread, for a different reason than exercise 01's `blocking_task`.
See `exercises/02_compute_vs_wait/PROMPT.md`.

### 01 — Async delegation vs. blocking

**Status: assigned.** Prompted by ticket 2's own detour (`docs/task_learning_notes/phase_0_project_setup/02_setup_postgres_sqlalchemy_alembic.md`, sections 6.6.1–6.6.3, 6.7) — a real `asyncio` script proving the delegated-wait vs. thread-monopolizing-block distinction with actual timing measurements, in this project's own stack rather than the notes' JS examples. See `exercises/01_async_delegation_vs_blocking/PROMPT.md`.
