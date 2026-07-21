# Exercises

Deliberate practice, separate from the real work tracked in `TASKS.md` — a lower-stakes place to build a skill before (or instead of) hitting it cold in the middle of real ticket work. Not part of the `game-engine` service itself; the `exercises/` folder gets excluded from the Docker image once that ticket lands.

## How this works

- I write the prompt — goal, constraints, what "done" looks like — and never the solution, same rule as everywhere else in this project.
- Where it's feasible, I also write a small pytest self-check (`test_exercise.py`) so you get instant, objective feedback before showing me anything.
- You write your solution in the exercise's own folder under `exercises/`.
- Paste the code or point me at the file when ready — I review it properly: what's right and why, what's wrong and why, not just "looks good."
- When an exercise actually closes a real gap, the matching entry in `~/.claude/CLAUDE.md`'s Skill Level & Focus Areas section gets updated to reflect it — that section only means something if it stays current.
- New exercises get proposed proactively when a real gap surfaces during normal ticket work (I'll ask before assigning one, never spring it mid-task unannounced), or whenever you ask for one directly.

## Log

Newest first, same convention as `TASKS.md`'s Current Status — add a new entry when an exercise is assigned, and update its own status in place as it moves from assigned → reviewed, rather than duplicating entries.

No exercises assigned yet.
