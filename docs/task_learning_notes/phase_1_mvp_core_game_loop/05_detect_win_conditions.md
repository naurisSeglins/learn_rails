# Ticket 4 — [BLOCKED] Detect win conditions: Theoretical Basis

Written *before* starting this ticket — see `01_create_a_game_with_a_fixed_starting_army.md` for what this format means and why. The win condition itself is still an open design question (see
`docs/architecture.md`), so the useful theory to have ready *now* is the state-representation pattern, not the actual condition.

## Representing state as data, not scattered flags

`Game.status` needs constraining to a small, known set of values (`in_progress`, `finished` for now) — not a free-text string that could silently hold a typo'd value no code checks for.
SQLAlchemy supports this directly via a Python `Enum` (illustrative):
```python
import enum

class GameStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
```
mapped to the `status` column — the database itself (and a type checker) then rejects any value outside this set, rather than trusting every piece of code that writes to `status` to only use
the right strings.

## How the check and the guard fit together

The win-condition check (once decided) reads game state and returns whether/who won — called once per round resolution, same timing as combat resolution — and is the only thing allowed to
transition `status` to `FINISHED`. Every other route that could accept a move should check `status == IN_PROGRESS` first, as a guard clause, before doing anything else — not something to add
after the fact once a bug reveals a finished game silently accepting a move.
