# Ticket 3 — [BLOCKED] Resolve combat: Theoretical Basis

Written *before* starting this ticket — see `01_create_a_game_with_a_fixed_starting_army.md` for what this format means and why. Combat math itself is still an open design question (see
`docs/architecture.md`), so the useful theory to have ready *now* is the shape of the extraction, not the actual formula.

## The service-object shape, illustrative — not this project's actual combat math

```python
class CombatResolver:
    def __init__(self, attacker: Piece, defender: Piece):
        self.attacker = attacker
        self.defender = defender

    def resolve(self) -> CombatResult:
        # combat math goes here once decided — this method's only job
        # is to take two pieces in and produce one outcome out
        ...
```
The class takes exactly what it needs in `__init__` (the two pieces involved), and its one public method does exactly one thing. A route handler's job becomes: find the two pieces, build a
`CombatResolver`, call `.resolve()`, persist the result — it never contains the combat logic itself.

## Why this matters before the math is even decided

This is directly testable with two plain `Piece` objects and no HTTP request at all — once the math is decided, per this project's TDD default, the test for it can be written first, against
this class directly, before any route touches it. Having the shape ready now means the actual work, once unblocked, is "write the math and its test," not "also figure out where this logic should
live."
