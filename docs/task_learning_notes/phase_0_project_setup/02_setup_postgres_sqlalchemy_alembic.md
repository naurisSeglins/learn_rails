# Ticket 2 — Set up Postgres via SQLAlchemy (async) + Alembic: Learning Notes

Companion to this ticket's structured breakdown in `TASKS.md` — that file has the canonical What it is / Why we use it / How it works / What breaks without it / Industry context reference. This
file captures the actual discussion, debugging, and side-questions that came up while doing the work, in order — including a full detour into the async "function coloring" problem, triggered by
this ticket's own assigned reading.

## Getting a local Postgres server running

Postgres.app was already installed (found via `PATH`, which included `/Applications/Postgres.app/Contents/Versions/latest/bin`). First attempt to start it failed: port 5432 already in use.

**Diagnosing the port conflict:** ran `psql -l` (without specifying a port) and it succeeded — listing `payments-development`, `risk-development`, `integrator-events-development`,
`yugabyte-development`, all clearly GoCardless work-project databases. This confirmed port 5432 was already owned by a separate, unrelated local Postgres setup (a work Postgres instance, running
independently of Postgres.app), not a broken install.

**Fix:** gave this project's own Postgres.app instance a different port (5433) rather than fighting over 5432, keeping it fully isolated from the work database. Every client tool needs the port
passed explicitly once it's non-default — `psql -p 5433 -l`, `createdb -p 5433 learn_dev` — since they all assume 5432 unless told otherwise. Confirmed the new instance on 5433 by re-running
`psql -p 5433 -l` and seeing only the fresh instance's default databases (`nseglins`, `postgres`, `template0`, `template1`).

## The client-server database model — why directory doesn't matter but port does

**The misconception this corrected:** treating Postgres like SQLite, where "the database" is a file your own process opens and reads directly, and nothing needs to be "running" separately.

**The actual mechanism:** SQLite is an *embedded* database — the SQLite library is linked directly into your app process, and the file *is* the storage; your app opens it like any other file.
Postgres is a *client-server* database — a genuinely separate, long-running program (the Postgres server, i.e. the postmaster process) is the *only* thing that ever touches the real files on
disk. Your app (or `psql`, or `createdb`) is a client: it opens a network connection to that already-running server and sends it commands ("create a database," "run this query") — the server does
the actual disk work on the client's behalf. This is what makes safe concurrent access possible (many connections, even from different apps, can talk to one server safely) — the exact thing
SQLite can't do well under concurrent writers.

**Why this means `createdb`'s working directory is irrelevant:** the command doesn't open a file — it opens a network connection (even for `localhost`, still the client-server protocol) and
sends a request. The port identifies *which server* to talk to (since more than one can run on a machine at once — the work Postgres on 5432, this project's on 5433); the directory you happen to
be standing in when you type the command never enters into it.

## Postgres's data directory ending up inside the git repo

A `psql/` folder was found sitting directly in the repo root, permissions `drwx------` (Postgres itself enforces that restrictive mode on its data directory) — the actual location Postgres.app
had been pointed at for this instance's data.

**Why this was a real risk, not just untidy:** `git status` showed it as untracked and *not* excluded by `.gitignore`. A careless `git add -A` (instead of adding specific files by name) would try
to commit raw Postgres binary data files into the repo — bloating it permanently (git handles large/frequently-changing binary data very badly, and purging it from history later is a real pain)
and mixing runtime data storage with source code, which doesn't match how this will actually run in production anyway (Postgres there is Cloud SQL, a separate managed service with nothing to do
with the app's own filesystem or repo).

**Fix:** stopped the server in Postgres.app, deleted and recreated the instance on the same port (5433) with its location pointed *outside* any project folder, then deleted the leftover `psql/`
directory from the repo (`rm -rf`). Nothing of value was lost — only the default template databases existed at that point, nothing project-specific.

## Server vs. database — the actual distinction

A recurring point of confusion: "I already have a server for this project, why do I also need a database?" These aren't competing things — the server is already-running infrastructure (one
server can host many databases, like a filing cabinet with many drawers); a database is just one named, isolated space *inside* that server (one drawer). `createdb -p 5433 learn_dev` breaks down
as: `createdb` (a small client program whose only job is "ask a server to create a database"), `-p 5433` (which server to send the request to, by port — necessary specifically because more than
one server can be running), and `learn_dev` (the name of the new drawer to create inside that already-running server). It doesn't start anything new — the server's already running; it just adds
one named database inside it.

**Retrieval check (confirmed correct, with one refinement):** the reason the command can be run from anywhere isn't that "the data isn't saved locally" — it's saved locally, on the same disk,
wherever the server's data directory now lives (outside the repo). The real distinction is *who touches that data directly*: with SQLite, your own process opens the file itself; with Postgres,
only the server process ever touches the files — your command just sends a message over a connection, and the server acts on its own storage, wherever that happens to be.

## `.env` + `pydantic-settings` — the connection URL

Connection URL shape: `postgresql+asyncpg://user@host:port/dbname` → `postgresql+asyncpg://nseglins@localhost:5433/learn_dev` for this setup (Postgres.app's local default: trust auth, no
password, Mac username as the default role).

**Why not hardcoded:** the URL differs per environment (laptop/CI/production point at different servers), and a hardcoded connection string is exactly the kind of thing that ends up committed
to git by accident — the same category of risk `CLAUDE.md` already flags for secrets in logs/errors. `.env` is already covered by `.gitignore`'s `/.env*` rule, so it's safe from being committed.
`pydantic-settings` was added as a dependency to load it into a typed object instead of scattering `os.environ.get(...)` calls.

### Writing the `Settings` class — three attempts

**Attempt 1:**
```python
class Settings

  database_url: str
```
Missing the parent class entirely (`BaseSettings`) — a plain class with a type-hinted attribute has no behavior behind it; it doesn't read anything from the environment on its own. Also missing
the colon after `class Settings` — a block-opening statement needs a `:` (same Python-vs-Ruby distinction as ticket 1's module-scope bug: indentation alone isn't enough, something has to
explicitly open the block).

**The general shape needed** (illustrative, not the literal answer):
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class ExampleSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    some_field: str
```
`BaseSettings` is the parent class that actually provides "read this from the environment" behavior. `SettingsConfigDict(env_file=".env")` is what tells it to also read a `.env` file — by
default, `BaseSettings` only reads real environment variables, *not* `.env`, unless told to.

**Attempt 2:**
```python
class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env")
  database_url: str

print(model_config, database_url)
```
Inheritance and colon fixed — but `print(model_config, database_url)` treats names defined *inside the class body* as if they were bare module-level names. They aren't: `model_config` and
`database_url` belong to the class (or to an instance of it), the same way a name assigned inside a function isn't visible outside it. Nothing had actually built a `Settings` object yet — the
class is only a blueprint.

**Attempt 3 (correct):**
```python
settings = Settings()
print(settings.model_config, settings.database_url)
```
`Settings()` builds an actual instance, and `settings.database_url` correctly accesses that instance's attribute. Confirmed working by booting the app and seeing the real value from `.env`
printed in the terminal — the temporary print line was then deleted once its job was done.

### The engine and session factory

**The mechanism, from the ground up:** Postgres talking requires a network connection; opening a brand-new one per query would be slow (TCP + Postgres auth handshake every time), so
SQLAlchemy's `AsyncEngine` maintains a *pool* of already-open connections. The engine doesn't run queries itself — it manages the pool and knows how to open more connections when needed, using
the URL it was given. Because setting up the pool has real cost, you want exactly one engine for the whole process's life, created once at startup.

A `Session` is different and much shorter-lived: what your code actually uses to do database work, borrowing one connection from the engine's pool while it's active and returning it when done.
You want a fresh session per unit of work (later: one per request), so one request's half-finished work never bleeds into another's. `async_sessionmaker` is a *factory* — a reusable recipe that
produces a correctly-configured session bound to the one engine, built once, alongside the engine.

**Design question raised explicitly: should this live inside `Settings`, or separately?** Answered via `CLAUDE.md`'s own Sandi Metz rule (each class does one thing) — `Settings`' job is reading
config; creating an engine and session factory is a different job. Kept separate.

**First attempt at the separate piece:**
```python
class AsyncEngineSettings():
  engine = create_async_engine(settings.database_url)
  session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async_engine = AsyncEngineSettings()
```
Several issues, in order of how they surfaced:
- **Import paths** — `create_async_engine`, `async_sessionmaker`, and `AsyncSession` all live in `sqlalchemy.ext.asyncio`, not top-level `sqlalchemy`; `AsyncSession` was missing from the import
  entirely. (Fact to know, not something to reason out.)
- **Naming collision** — the custom class was named `AsyncEngine`, the same name as the real object `create_async_engine()` returns. Not broken, but confusing; renamed to `AsyncEngineSettings`.
- **The deeper conceptual issue**: `engine = ...` and `session = ...` sit directly in the class body, not inside a method — which means (same rule as `model_config` earlier) they run *once, the
  moment Python processes the `class ...:` statement itself* — which happens to be correct timing (once)! But `async_engine = AsyncEngineSettings()` isn't what creates them; they already existed
  as class attributes before that instantiation ran at all. Given there's never a reason to want more than one engine or session factory for the whole process, a class buys nothing here — no
  per-instance state is ever needed. Recommendation: plain module-level assignments instead, no class:
```python
engine = create_async_engine(settings.database_url)
session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
```

**The "vague understanding" moment:** partway through this, self-reported not having a confident enough mental model of either `Settings` or the engine/session setup to evaluate them — not a
request for an easier question, a request to stop and actually build the foundation. This triggered a full ground-up re-explanation of both mechanisms (captured above, in the "connection URL"/
"engine and session factory" sections) before returning to the code review. This exchange is also what established the standing rule (now in the global `CLAUDE.md`) to trust an accurate
self-report of "I don't understand enough to answer that" immediately, rather than rephrasing the same guiding question.

**Also established here:** this ticket's own `Read first` (*SQLAlchemy 2 In Practice*, Chapter 7, "Asynchronous SQLAlchemy") already covered exactly this engine/session material directly — the
gap was in not having read it yet, not the resource being missing. This became a standing rule too: check whether a ticket's assigned reading already covers a point of confusion before
re-deriving the explanation from scratch.

## Detour: "What Color is Your Function?" (Bob Nystrom) and the async coloring problem

Reached via Chapter 7's own reference to the essay. Worked through using a real example pulled from an old personal project (`buy_coins.js`, a crypto trading bot on GitHub), not a hypothetical —
chosen deliberately, since concrete code already trusted is how this sticks best.

### The concrete example
```js
db.all(sql, [], (err, rows) => {        // plain callback — NOT async
  let allCoins = rows

  async function buy_coin() {           // carved out a separate async function
    for (coin of allCoins) {
      let amounts = await routerContract.getAmountsOut(...)   // ethers.js — Promise-based
      await wbnbContract.approve(...)
      await approveTx.wait()
      await routerContract.swapExactTokensForTokens(...)
      await swapTx.wait()
    }
  }

  buy_coin();   // called WITHOUT await
});
```

### Anatomy of `db.all(sql, [], (err, rows) => {...})`
- `db` — an object (a `sqlite3.Database` instance); `.all` — a method on it.
- Three arguments: `sql` (query text), `[]` (query parameters — see below), and a function.
- **Higher-order** just means "a function that takes another function as an argument (and/or returns one)." `db.all`'s third argument isn't data — it's a function `db.all` will *call itself*,
  later, once the read finishes. Proof of the mechanism: pass a non-function there (`db.all(sql, [], "hello")`) and it fails at the moment sqlite3 tries to *invoke* "hello" as a function —
  confirming that's literally what happens internally.

### Query parameters (`[]`) vs. writing values into the SQL string — simple, then detailed with code

**Simple version:** gluing text together to build a sentence, where one piece comes from someone else — if that piece secretly contains extra "instructions," the reader can't tell your original
instructions from the sneaky ones anymore, since it's all one sentence now. A placeholder avoids the gluing: "here's my instruction with a blank," separately, "here's the value for the blank" —
filled in as pure data, never re-read as instructions, no matter what's inside it.

**Unsafe — building the SQL string directly:**
```js
const userInput = "1 OR 1=1";                          // pretend this came from a user
const sql = "SELECT * FROM users WHERE id = " + userInput;
// sql is now literally: "SELECT * FROM users WHERE id = 1 OR 1=1"
db.all(sql, [], callback);
```
`sql` becomes one single string, and that's all the database ever sees — it has no idea `"1 OR 1=1"` was ever a separate value. Since `1=1` is always true, this returns *every* user, not just id
1. If `userInput` were `"1; DROP TABLE users; --"`, the glued string becomes two SQL statements back to back, and some drivers will run both.

**Safe — placeholder + separate array:**
```js
const userInput = "1 OR 1=1";
const sql = "SELECT * FROM users WHERE id = ?";
db.all(sql, [userInput], callback);
```
`sql` never contains `userInput` at all — it stays a fixed string with no external data mixed in. `userInput` travels separately, in the array, tagged as "a value for the `?` slot." The driver
treats the whole string as one value being compared to `id`, never as SQL to execute — matching nothing, rather than returning everything.

**Why one is just better, concretely:** the placeholder version never lets the SQL text and the data touch each other; the concatenation version merges them into one string with no way to
un-merge them afterward.

In this project's own query (`SELECT id coinId... FROM buy_coins`), there are no `?` placeholders at all — nothing dynamic is inserted — so the array is empty; the function signature always
expects three arguments in that position regardless.

### Why pass a function instead of getting a value back — simple, then detailed with code

**Simple version:** normally you ask a question and stand there waiting for the answer before using it. If the answer takes a while, that wastes your time — so instead you say "here's my
number, call me back," and go do something else meanwhile.

**Ordinary, synchronous shape** (works only because the answer is instant):
```js
function double(x) {
  return x * 2;
}
let result = double(5);
console.log(result);    // 10, usable right away
```

**The "call me back" shape:**
```js
function getDataSlowly(callback) {
  setTimeout(() => {              // stands in for a slow disk read
    let result = 42;
    callback(result);             // getDataSlowly calls YOUR function
  }, 2000);
}

getDataSlowly((result) => {
  console.log(result);            // 42, printed 2 seconds later
});

console.log("this prints FIRST, immediately");
```
`getDataSlowly(...)` returns right away with no `return` statement handing back `42` — it only *schedules* work. The `console.log("this prints FIRST...")` line runs before the 2 seconds are up,
proving the call itself finished instantly, well before the real result existed. Only once the scheduled work actually completes does it call `callback(result)` — your function, invoked *by*
`getDataSlowly`, at the only point the value actually exists. This is exactly `db.all`'s shape: `db.all` is `getDataSlowly`, the disk read is the wait, `(err, rows) => {...}` is the callback.

### "Returns immediately" vs. "fetches all the data" — resolving the apparent contradiction

"Returns immediately" describes the *statement* `db.all(...)` finishing and letting the next line run — not the data being ready. `db.all` starts the read and returns before it's complete; the
read continues in the background; only once every row is actually retrieved does it call the callback with the real `rows`. The call and the underlying work finish at two different times.

### What "blocked" actually means

The one thread running the JavaScript stops advancing and sits idle until one specific thing (the disk finishing) happens. This freezes *everything else* because ordinary JS execution has
exactly one thread doing all the work — every other pending callback, timer, or request has to take a turn on that same thread. If it's stuck waiting, nothing else can run, not because it's
forbidden, but because there's no other thread free to run it on.

### Does Node use threads at all?

Yes — internally (via libuv's thread pool) for things like file reads, DNS lookups; this project's own sqlite3 read is one of them. But **your own JavaScript never runs on those threads** —
they're invisible plumbing that lets the *waiting* happen off the main thread; the result still gets handed back to the single main thread to actually process. Contrast Ruby/Java: when you
explicitly create a thread there, *your own code* runs on it. In Node, your code is always confined to the one main thread — which is why it still needs callbacks/promises/`async`, even though
real threads exist under the hood you never write code for directly.

### sqlite3 vs. Postgres — two different "concurrency" questions, not one

- **Node's process-level concurrency**: can this one process do other, unrelated things (a different HTTP request, a different timer) while this one query is in flight? This is what "other
  requests" meant in the blocking discussion — not requests to sqlite, requests to the whole process.
- **sqlite's own database-level concurrency**: can sqlite itself handle multiple simultaneous queries/writes to the *same* file without contention? This is the separate, real
  SQLite-vs-Postgres locking limitation already covered in `docs/architecture.md`.

### Why is sqlite3 (the npm package) callback-based at all?

It predates Promises in JavaScript entirely (standardized 2015, `async`/`await` later still). When its API was designed, callbacks were the *only* mechanism available for "tell me when this
finishes." Once an API is public and depended on, changing its shape breaks everyone using it — so it stayed callback-shaped even after Promises became the preferred style for new code.

### Why Ruby and (traditional) Java don't have the coloring problem, and why it can't just be copied

Two fundamentally different answers to "how does a program wait without freezing":

- **Real OS threads (Ruby, traditional Java).** The OS runs several independent lines of execution; when one blocks on I/O, the OS schedules a different thread onto the CPU meanwhile. No keyword
  needed — the "let something else run while I wait" job belongs to the OS, invisible to function signatures. Ruby (MRI) has a GIL limiting true parallel *bytecode* execution, but releases it
  during I/O waits, so threads still meaningfully overlap.
  - **Cost**: OS threads are heavy (megabyte-scale stacks each, real context-switch overhead) — fine for hundreds of concurrent things, breaks down at tens of thousands. This is the actual
    reason JS/Python didn't just copy this.
- **One thread, explicit pause points (JS, Python `asyncio`).** JS is single-threaded by design (partly to avoid multi-thread DOM-mutation bugs) — with only one thread, you *can't* block it, so
  a function has to explicitly declare "I might pause here" (`async`/`await`), letting the event loop run other work meanwhile and resume this function later. The color exists *because* there's
  no second thread to fall back on.

**Why not just adopt the other model?**
- JS: single-threaded at the level of the whole language/ecosystem — real shared-memory threading would require re-architecting the language and breaking the huge single-threaded-assumption
  ecosystem. (Node's "worker threads" don't share memory the normal way, precisely because full threading doesn't fit the model.)
- Python: the GIL caps true parallelism similarly to Ruby's; Python has started removing it optionally (free-threaded builds), and library tricks (`greenlet` — which SQLAlchemy itself uses
  internally in places) implement Ruby/Loom-style implicit stack-switching under the hood, but this remains a specialized mechanism, not the mainstream `asyncio` model.
- **The deepest reason**: implicit suspend/resume at *any* point in a call stack (not just an explicit `await`) requires the runtime to support continuations — capturing and restoring execution
  state arbitrarily. That's not a small patch; it's a multi-year runtime rewrite (what Java's Project Loom actually took, to get virtual threads that look like blocking code but don't block a
  real OS thread). There's also a genuine, unresolved philosophical disagreement: explicit `async`/`await` makes it *visible* exactly where a function might yield (useful for reasoning about
  correctness); implicit fiber-switching hides that, which can make some concurrency bugs harder to spot.

### Putting it together

The `buy_coins.js` friction came from `db.all`'s pre-Promise, callback-shaped API (built when that was JS's only option) meeting `ethers.js`'s fully Promise-based API (built after `async`/`await`
existed) — two different eras answering the same one-thread constraint, that don't compose cleanly. Ruby and traditional Java never needed that constraint, because the OS was doing the "let
something else run" job — at the cost of threads being too heavy to spin up millions of. Newer Java (Loom) and Go get both properties at once, only by rebuilding runtime machinery most languages
haven't (yet) rebuilt.

## Status

In progress. Done: Postgres server running locally on port 5433 (data directory relocated outside the repo), `learn_dev` database created, `.env` with `DATABASE_URL`, `pydantic-settings` added
and a working `Settings` class confirmed reading it correctly. Still open: the async engine + session factory code (module-level, no wrapping class, per the design conclusion above), Alembic
initialization (`alembic init -t async alembic`), and the first migration.
