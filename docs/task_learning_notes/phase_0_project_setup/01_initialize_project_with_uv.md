# Ticket 1 — Initialize the project with uv: Learning Notes

Companion to this ticket's structured breakdown in `TASKS.md` (What it is / Why we use it / How it works / What breaks without it / Industry context / Common pitfalls) — that file has the
canonical reference version. This file captures the actual discussion, debugging, and side-questions that came up while doing the work, in the order they happened.

## Poetry vs. uv — why uv won

Poetry was the original stack choice, revisited before this ticket started. uv's case: a Rust-based resolver that's dramatically faster than Poetry's, from the same team (Astral) as Ruff (already
the project's linter — real ecosystem-consistency argument), and it can manage the Python interpreter itself (no separate pyenv). Poetry's case: longer production track record, a more mature
plugin ecosystem, more existing prior art/tutorials. Given this repo had zero dependencies locked in yet, the switching cost was free, and the Ruff overlap plus current momentum tipped it to uv.
All `Read first`/command references across `CLAUDE.md` and `TASKS.md` were updated from `poetry run`/`poetry init` to `uv run`/`uv init` accordingly.

## The `uv add --dev` scoping mistake

Ran only `uv add --dev pytest pytest-asyncio httpx factory_boy ruff` and assumed the project was set up — but `pyproject.toml`'s `dependencies` list stayed empty; only the `dev` group got
populated. Running `uv run uvicorn main:app --reload` then failed with `Failed to spawn: uvicorn — No such file or directory`, because uvicorn was never actually installed anywhere. The fix was
running the separate, plain `uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic pydantic` command for the runtime dependencies — the two commands are genuinely separate, one
doesn't imply the other.

**Why the split exists at all**, once both were in place: it's the same idea as Rails' Gemfile `group :test do ... end` blocks — a production Docker image can install only the main group
(skipping pytest/ruff entirely), which means a smaller, faster-to-pull image and a smaller attack surface (fewer third-party packages sitting in a container that never uses them).

## Booting uvicorn — the `module:variable` convention

`uv run uvicorn main:app --reload` — `main:app` means "import the `main` module, then find the attribute named `app` on it." uvicorn doesn't run `main.py` as a script; it imports it as a module
purely to get hold of the `app` object, then serves requests by calling into that object itself. `--reload` additionally watches source files and restarts the whole uvicorn process on a change.
Confirming it worked meant checking `http://127.0.0.1:8000/docs` actually rendered (proof a request round-tripped through uvicorn into the app and back), not just that the process didn't crash.

## The module-scope bug: `app = FastAPI()` trapped inside a function

First version of `main.py` had:
```python
def main():
    app = FastAPI()

if __name__ == "__main__":
    main()
```
This failed with `Attribute "app" not found in module "main"`.

**The mechanism, not just the fix:** when Python *imports* a module (what uvicorn does), it runs every top-level statement once, and each becomes an attribute of the module object. A statement
inside a function body is not top-level — it only runs if and when something calls that function, and even then, it's a local variable, gone the instant the function returns; it never becomes a
module attribute. uvicorn never calls `main()` — it only imports the module and looks for `app` already sitting there. The `if __name__ == "__main__":` guard doesn't help either: that condition
is only true when the file is *run directly* (`python main.py`); when a file is *imported* instead, `__name__` is set to the module's own name (`"main"`), not `"__main__"`, so the guard never
fires under uvicorn.

**The transferable pattern:** this is a difference from Ruby worth naming explicitly. Ruby uses `end` keywords to close a block — indentation there is just style. Python has no `end` keyword at
all; indentation *is* the syntax that defines what's inside a block. A statement is only "inside" something because a `def`/`if`/`for` above it explicitly opened a block it belongs to.

**Second attempt** removed the `def main():` wrapper but left a stray indent on the `app = FastAPI()` line with nothing above it opening a block — this produced (or would produce) an
`IndentationError`, since an indented line needs something above it demanding that indent. Fix: `app = FastAPI()` flush at column 0, matching the `from fastapi import FastAPI` line above it.
Confirmed working afterward — booted cleanly, `/docs` rendered.

## The stale-PATH issue after installing uv

Before any of the above, `uv init` itself failed with `command -v uv` not found, alongside a "Safe-chain" warning about overwriting `SSL_CERT_FILE`/`REQUESTS_CA_BUNDLE`/`PIP_CERT`.

**Safe-chain**, identified separately: a supply-chain security tool (Aikido Security's `safe-chain`) that wraps package-manager commands (`npm`, `pip`, `uv`) to scan packages for known malware
*before* installation — it swaps in its own CA certificate to sit in the middle of the HTTPS traffic to package registries, which is exactly what that warning describes. Normal behavior for this
category of tool, not a sign of anything broken, and unrelated to the actual PATH failure.

**The actual failure:** `which -a uv` found the real binary at `~/.local/bin/uv`, fully installed and working (`uv --version` succeeded) — in a *fresh* shell. The terminal tab where `uv init` had
failed was opened *before* `~/.local/bin` was added to `PATH` by the installer. A shell reads its `PATH` once, at startup; installing something afterward doesn't retroactively update a session
that's already running. Fix: open a new terminal (or `source ~/.zshrc`), no different than restarting anything else whose config changed while it was already running.

## FastAPI's dependency injection — why the Industry Context "more magic, less obvious" tradeoff means what it means

Came up when reviewing `TASKS.md`'s FastAPI entry. **Dependency injection, concretely:** a route function declares something it needs as a parameter (e.g. a database session) via `db: Session =
Depends(get_db)`, and FastAPI calls `get_db()` and hands over the result automatically before the function runs — you never write the line that actually creates `db` yourself. Contrast with
Flask-style, where `db = get_db_connection()` is written explicitly inside the function body, so the source of `db` is visible just by reading the function. Reading the FastAPI version alone
doesn't tell you where `db` came from — you have to already know the `Depends(...)` convention to trace it. That's the actual, concrete shape of "more magic, less obvious" — not just a label.

## Status

Complete — `pyproject.toml` has FastAPI, uvicorn, SQLAlchemy (async), asyncpg, Alembic, and Pydantic as runtime dependencies (plus the dev-only test/lint tools in their own group); `main.py` has a
module-level `app = FastAPI()`; confirmed booting via `uv run uvicorn main:app --reload` and `/docs` rendering correctly.
