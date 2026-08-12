# Ticket 2 — Set up Postgres via SQLAlchemy (async) + Alembic: Learning Notes

Companion to this ticket's structured breakdown in `TASKS.md` — that file has the canonical What it is / Why we use it / How it works / What breaks without it / Industry context reference. This
file captures the actual discussion, debugging, and side-questions that came up while doing the work, in order — including a full detour into the async "function coloring" problem, triggered by
this ticket's own assigned reading.

## 1. Getting a local Postgres server running

Postgres.app was already installed (found via `PATH`, which included `/Applications/Postgres.app/Contents/Versions/latest/bin`). First attempt to start it failed: port 5432 already in use.

**Diagnosing the port conflict:** ran `psql -l` (without specifying a port) and it succeeded — listing `payments-development`, `risk-development`, `integrator-events-development`,
`yugabyte-development`, all clearly GoCardless work-project databases. This confirmed port 5432 was already owned by a separate, unrelated local Postgres setup (a work Postgres instance, running
independently of Postgres.app), not a broken install.

**Fix:** gave this project's own Postgres.app instance a different port (5433) rather than fighting over 5432, keeping it fully isolated from the work database. Every client tool needs the port
passed explicitly once it's non-default — `psql -p 5433 -l`, `createdb -p 5433 learn_dev` — since they all assume 5432 unless told otherwise. Confirmed the new instance on 5433 by re-running
`psql -p 5433 -l` and seeing only the fresh instance's default databases (`nseglins`, `postgres`, `template0`, `template1`).

**Follow-up 1.1 — a second port conflict.** Port 5433 later turned out to collide with an unrelated project too. Same mechanism, different number: reconfigured Postgres.app's server settings to
listen on 5434 instead and restarted it. Since this only changed which port the *same* server instance listens on — the data directory and everything in it were untouched — `learn_dev` came
through intact; confirmed with `psql -p 5434 -l` (lists `learn_dev`) and `psql -p 5433 -l` (nothing answers there anymore). Port is a property of the connection, not of the stored data — see
"Server vs. database" below for why.

## 2. The client-server database model — why directory doesn't matter but port does

**The misconception this corrected:** treating Postgres like SQLite, where "the database" is a file your own process opens and reads directly, and nothing needs to be "running" separately.

**The actual mechanism:** SQLite is an *embedded* database — the SQLite library is linked directly into your app process, and the file *is* the storage; your app opens it like any other file.
Postgres is a *client-server* database — a genuinely separate, long-running program (the Postgres server, i.e. the postmaster process) is the *only* thing that ever touches the real files on
disk. Your app (or `psql`, or `createdb`) is a client: it opens a network connection to that already-running server and sends it commands ("create a database," "run this query") — the server does
the actual disk work on the client's behalf. This is what makes safe concurrent access possible (many connections, even from different apps, can talk to one server safely) — the exact thing
SQLite can't do well under concurrent writers.

**Why this means `createdb`'s working directory is irrelevant:** the command doesn't open a file — it opens a network connection (even for `localhost`, still the client-server protocol) and
sends a request. The port identifies *which server* to talk to (since more than one can run on a machine at once — the work Postgres on 5432, this project's on 5433); the directory you happen to
be standing in when you type the command never enters into it.

## 3. Postgres's data directory ending up inside the git repo

A `psql/` folder was found sitting directly in the repo root, permissions `drwx------` (Postgres itself enforces that restrictive mode on its data directory) — the actual location Postgres.app
had been pointed at for this instance's data.

**Why this was a real risk, not just untidy:** `git status` showed it as untracked and *not* excluded by `.gitignore`. A careless `git add -A` (instead of adding specific files by name) would try
to commit raw Postgres binary data files into the repo — bloating it permanently (git handles large/frequently-changing binary data very badly, and purging it from history later is a real pain)
and mixing runtime data storage with source code, which doesn't match how this will actually run in production anyway (Postgres there is Cloud SQL, a separate managed service with nothing to do
with the app's own filesystem or repo).

**Fix:** stopped the server in Postgres.app, deleted and recreated the instance on the same port (5433) with its location pointed *outside* any project folder, then deleted the leftover `psql/`
directory from the repo (`rm -rf`). Nothing of value was lost — only the default template databases existed at that point, nothing project-specific.

## 4. Server vs. database — the actual distinction

A recurring point of confusion: "I already have a server for this project, why do I also need a database?" These aren't competing things — the server is already-running infrastructure (one
server can host many databases, like a filing cabinet with many drawers); a database is just one named, isolated space *inside* that server (one drawer). `createdb -p 5433 learn_dev` breaks down
as: `createdb` (a small client program whose only job is "ask a server to create a database"), `-p 5433` (which server to send the request to, by port — necessary specifically because more than
one server can be running), and `learn_dev` (the name of the new drawer to create inside that already-running server). It doesn't start anything new — the server's already running; it just adds
one named database inside it.

**Retrieval check (confirmed correct, with one refinement):** the reason the command can be run from anywhere isn't that "the data isn't saved locally" — it's saved locally, on the same disk,
wherever the server's data directory now lives (outside the repo). The real distinction is *who touches that data directly*: with SQLite, your own process opens the file itself; with Postgres,
only the server process ever touches the files — your command just sends a message over a connection, and the server acts on its own storage, wherever that happens to be.

**Follow-up 4.1 — does this distinction hold up when the port itself changes later?** Yes, and it's the same "who touches the data" argument applied one layer further: the port isn't stored
*inside* the database at all, it's connection-layer config on the server process. `createdb -p 5433 learn_dev` used `5433` once, as a phone number to reach the server at that moment — it left zero
trace of that number anywhere in `learn_dev`'s own files. So when the server's listening port later changed to 5434 (1.1 above), the drawer moved with the cabinet for free; nothing about the
database itself ever referenced 5433 to begin with.

## 5. `.env` + `pydantic-settings` — the connection URL

Connection URL shape: `postgresql+asyncpg://user@host:port/dbname` → `postgresql+asyncpg://nseglins@localhost:5433/learn_dev` for this setup (Postgres.app's local default: trust auth, no
password, Mac username as the default role). (Port later became 5434 — see 1.1 above; `.env` was updated to match, no other change needed.)

**Why not hardcoded:** the URL differs per environment (laptop/CI/production point at different servers), and a hardcoded connection string is exactly the kind of thing that ends up committed
to git by accident — the same category of risk `CLAUDE.md` already flags for secrets in logs/errors. `.env` is already covered by `.gitignore`'s `/.env*` rule, so it's safe from being committed.
`pydantic-settings` was added as a dependency to load it into a typed object instead of scattering `os.environ.get(...)` calls.

### 5.1 Writing the `Settings` class — three attempts

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

### 5.2 The engine and session factory

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

**Follow-up 5.2.1 — confirmed fixed.** `main.py` now has `engine` and `session_factory`/`session` as plain module-level assignments, no wrapping class — matching the recommendation above.

## 6. Detour: "What Color is Your Function?" (Bob Nystrom) and the async coloring problem

Reached via Chapter 7's own reference to the essay. Worked through using a real example pulled from an old personal project (`buy_coins.js`, a crypto trading bot on GitHub), not a hypothetical —
chosen deliberately, since concrete code already trusted is how this sticks best.

### 6.1 The concrete example
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

### 6.2 Anatomy of `db.all(sql, [], (err, rows) => {...})`
- `db` — an object (a `sqlite3.Database` instance); `.all` — a method on it.
- Three arguments: `sql` (query text), `[]` (query parameters — see below), and a function.
- **Higher-order** just means "a function that takes another function as an argument (and/or returns one)." `db.all`'s third argument isn't data — it's a function `db.all` will *call itself*,
  later, once the read finishes. Proof of the mechanism: pass a non-function there (`db.all(sql, [], "hello")`) and it fails at the moment sqlite3 tries to *invoke* "hello" as a function —
  confirming that's literally what happens internally.

### 6.3 Query parameters (`[]`) vs. writing values into the SQL string — simple, then detailed with code

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

### 6.4 Why pass a function instead of getting a value back — simple, then detailed with code

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

### 6.5 "Returns immediately" vs. "fetches all the data" — resolving the apparent contradiction

"Returns immediately" describes the *statement* `db.all(...)` finishing and letting the next line run — not the data being ready. `db.all` starts the read and returns before it's complete; the
read continues in the background; only once every row is actually retrieved does it call the callback with the real `rows`. The call and the underlying work finish at two different times.

### 6.6 What "blocked" actually means

The one thread running the JavaScript stops advancing and sits idle until one specific thing (the disk finishing) happens. This freezes *everything else* because ordinary JS execution has
exactly one thread doing all the work — every other pending callback, timer, or request has to take a turn on that same thread. If it's stuck waiting, nothing else can run, not because it's
forbidden, but because there's no other thread free to run it on.

**6.6.1 Follow-up — doesn't `setTimeout` contradict this?** `setTimeout(callback, 2000)` clearly lets the code after it run immediately, with the callback only firing ~2 seconds later — which
looks like two things happening "at once" on one thread. Resolution: the 2-second countdown itself never happens *on* the JS thread at all. `setTimeout` only registers the request with the
runtime underneath (an instant operation, nothing to do with the 2000ms) and returns immediately; the countdown is tracked entirely by the runtime's own timer facilities (same delegation
mechanism as the disk read below), and the callback only touches the JS thread once, later, once the timer's elapsed *and* the thread is free. What genuinely blocks is code that runs *directly
on* the JS thread's own call stack with nothing to delegate to — a synchronous loop, `fs.readFileSync` — since that work isn't waiting on something external, it *is* the thing that needs
finishing, instruction by instruction, monopolizing the one thread that exists. Bedrock version: waiting requires no CPU work during the wait (delegable to a clock interrupt or an OS completion
signal); computing does require CPU work, and JS's own code only ever runs on its one thread — waiting is delegable, computing isn't.

**6.6.2 Follow-up — who actually decides what gets delegated, and is there a trend toward delegating more?** The compute-vs-wait split itself is fixed by physics, not a language choice — pure
computation only ever runs on whichever thread executes your code; there's no helper it could be handed to. What *is* a design choice is which side actually implements the delegation, and it's
not the bare language spec deciding this — `setTimeout`/`fetch`/sockets aren't JS language features at all, they're **host APIs** the *environment* embedding the JS engine provides (the browser's
own C++ Web APIs; Node's libuv). The core language only ever defines pure computation (variables, functions, control flow); it has no built-in concept of a network or timer. Concretely: libuv
genuinely uses the OS's non-blocking socket primitives (`epoll`/`kqueue`) for network waits, but for filesystem reads/DNS — where the OS has no equally good non-blocking primitive — it fakes it
via a real background *thread pool* that blocks there instead, then hands a finished result back to the main thread. Not true delegation-for-free, just relocated blocking. There's a real,
decades-long industry trend pushing harder toward the "delegate more" side — the **C10k problem** (holding open tens of thousands of mostly-idle connections at once, which a thread-per-connection
model can't afford, given each OS thread's megabyte-scale cost) is exactly why Node/`asyncio`/Go's event-driven models exist. But the trend only ever pushes *waiting* onto helper systems, never
computation — a CPU-heavy function still blocks the one thread it runs on, no matter how good the OS's async primitives get.

### 6.6.3 Compute vs. Wait — the physical stack, all the way down

*Supersedes the original Parts-A-E walkthrough, its diagram, and the two physical-mapping follow-ups that came after it — same conclusion, reached once here instead of three times spread
across this file.*

**The premise.** Every program is only ever doing one of two things: computing, or waiting for something external to finish (a disk, a network reply, a timer). Only waiting can ever be handed
off to someone else — computing means "a CPU executing your instructions," and there's no way to get instructions executed except by executing them. Fixed by physics, not language design;
equally true for JS, Python, or anything else.

**Layer 1 — the CPU core.** Physical silicon: one instruction pointer (a register holding "the address of the next instruction"), one set of general-purpose registers, an ALU (arithmetic/
logic) (#what is this ???#). Its entire existence is one loop, repeated billions of times a second: *fetch* the instruction the pointer (#what is a pointer how it works and what it actually is ?#)
addresses (#how does this process works ?#), *decode* what it encodes (#why we decode and encode ? and what do we decode and encode?#), *execute* it (add two registers, load a
value from memory, jump the pointer elsewhere)(#what is this ? how does it work ?#), advance the pointer(#advance meaning move forward to next instruction ?#), repeat. A core can only ever be mid-instruction(#what ? what is mid-instruction and why mid-instruction?#)
for one thread at a time because there is physically only one instruction pointer and one register file per core — running a *different* thread means swapping that entire register state out for a different, previously-saved one. (#I think you will need to draw me a diagram/graph for this to be understood#) 
That swap is a **context switch**, and it isn't something a core does to itself — it's done *to* it, by Layer 2.

**Layer 2 — the OS kernel.** A program too, but the one program allowed to run in **ring 0** ("kernel mode") rather than **ring 3** ("user mode") — a hardware-enforced privilege level, not a
software convention. Certain instructions (talk directly to a disk/network controller, change which memory a process may touch, halt the machine) are only legal in ring 0. This exists because
if *any* program could do those things, one buggy or malicious program could read another process's memory or corrupt disk I/O for everyone — so all of that power is funneled through one
trusted, shared gatekeeper. Two things it does that matter here:
- **The scheduler** — keeps a queue of runnable threads per core. On a timer interrupt (every few milliseconds) or whenever a thread blocks, it picks the next thread to run and performs the
  context switch: save the outgoing thread's registers into its kernel-tracked control block, load the incoming thread's saved registers, jump to its saved instruction pointer.
- **`epoll`/`kqueue`** — a kernel-side data structure per "epoll instance": watched file descriptors plus a separate ready-list. Registering interest in a socket hooks a wake-up callback onto
  that socket's own kernel object, so when a hardware interrupt (a network packet arriving) causes the kernel's networking code to mark it "has data," the callback fires: move the fd to the
  ready list, wake whoever's blocked on it.

**Layer 3 — the host process (this project: Python + uvicorn).** An ordinary **user-mode** OS process — same category of thing as Postgres's postmaster, different code. Bundles the
**language engine** (CPython) and the **host-API library** (`asyncio` + `selectors`). CPython doesn't execute your `.py` text directly: it first compiles it to **bytecode** (a lower-level
instruction set of its own — `LOAD_FAST`, `CALL_FUNCTION`, etc.), then runs a C-level **eval loop** — a dispatch over bytecode instructions — that itself executes as ordinary machine code on
a Layer-1 core. So "your code runs" bottoms out in: CPython's own eval-loop C code executing on a core, one bytecode instruction at a time — a software version of Layer 1's fetch-decode-
execute loop, one level up.

*Not all waiting inside Layer 3 is equally free.* For network sockets, Layer 3 uses `epoll`/`kqueue` directly — genuinely free, Layer 2 does the watching, no thread spent. For file reads and
DNS lookups, where the OS has no equally good non-blocking primitive, Layer 3 fakes the same experience: it spawns a small number of extra, real OS threads (a thread pool — 4 by default in
Node's libuv; Python's asyncio has an equivalent default executor) and has one of them make an old-fashioned *blocking* syscall. It still blocks — just on a thread you never see. Relocated,
not eliminated.

**Layer 4 — your own code.** Route handlers, coroutines. The bytecode CPython's eval loop is currently stepping through. Nothing physically new — the top of the stack, not a separate
mechanism.

```
Layer 4  Your code (route handlers, coroutines)
              |
Layer 3  Host process: CPython + asyncio        <- an OS process, PID and all
              |  (syscall crossing, walked through below)
Layer 2  OS kernel: scheduler + epoll/kqueue    <- privileged, kernel-mode code
              |  (context switch)
Layer 1  CPU core                                <- physical silicon
```

**The 2↔3 crossing, slowly — what actually happens on a syscall.** Say asyncio needs "wake me when any of these sockets has data" (`epoll_wait`):

1. asyncio's C code (still ordinary Layer-3 user-mode instructions) loads two things into fixed CPU registers: which operation this is (a number — `epoll_wait` is syscall #232 on x86-64
   Linux) and its arguments. Nothing special yet — this is normal computation.
2. It executes one specific instruction built exactly for this: `syscall` (x86-64) or `svc` (ARM64 — e.g. Apple Silicon). This single instruction is the *entire* doorway between user code and
   the kernel.
3. The CPU, in hardware, does three things atomically the instant it executes that instruction: flips the core's privilege level from ring 3 to ring 0; saves the current instruction pointer
   so it knows where to resume afterward; jumps — not anywhere the calling program chooses, but to one single, fixed address the kernel registered when the machine booted. User code can
   trigger *only* this one kernel-controlled entry point, never arbitrary kernel code — that's precisely what makes it safe.
4. Kernel code now executes — on the *same physical core*, in the *same thread's* context, just with elevated privilege. It reads "232," recognizes `epoll_wait`, and checks its own internal
   ready-list for this epoll instance.
5. Two branches:
   - **Already ready:** the kernel fills in the answer, executes the paired return instruction (`sysret`/ARM equivalent), flips privilege back to ring 3, jumps back to the saved instruction
     pointer. A handful of CPU cycles; the thread never stopped, it just took a very short detour through kernel code.
   - **Nothing ready yet (the real async case):** the kernel marks the thread blocked (removed from the scheduler's runnable list), and the scheduler immediately context-switches the core to
     a different runnable thread. Separately, back when the socket was registered (`epoll_ctl`), the kernel had already wired a hook onto it: when the network card's hardware eventually
     raises an interrupt for an arriving packet, the interrupt handler marks that file descriptor ready and puts the blocked thread back on the runnable list.
6. Later, the scheduler picks the thread again (a context switch onto some core — not necessarily the same physical one). Execution resumes exactly where `epoll_wait`'s kernel code left off,
   sees data is ready, and takes the same "return to user mode" path as the fast branch above.
7. Control lands back in asyncio's C code (Layer 3), right after the original `syscall` instruction, result sitting in a register. asyncio marks the corresponding Future/coroutine resolved;
   the event loop, on its next pass, hands control to your `await`ed code (Layer 4).

Nothing here makes the thread stop existing or move to different hardware conceptually — it's the same OS thread throughout. What changes is only *whether it currently has a core underneath
it*, and that's the scheduler's call, not asyncio's and not yours.

**The conclusion (the wall).** None of Layers 1–3's machinery — `epoll`, the thread pool, the scheduler, the event loop — ever touches *computation*. A genuinely heavy calculation still
completely ties up whichever thread runs it, for exactly as long as it takes, because (the premise, again) computing was never delegable to begin with; no OS trick can execute your
instructions without spending a core's cycles on them. Concretely, for this project: a FastAPI route doing real computation (not just awaiting Postgres) still freezes the one event-loop
thread for every other request — fixing that needs a different tool (a separate process/worker), not something `asyncio`'s event loop can solve on its own.

**Old vocabulary, for reference.** Earlier passes through this material used "Part A/B/C/D/E" labels. Part A = the premise above. Part B = Layer 3. Part C = the two branches inside Layer 3's
waiting strategy (`epoll`/`kqueue` vs. the thread-pool fallback). Part D mixed a real component (the event loop, folded into Layer 3 above) with pure motivation (the **C10k problem**: one
thread per connection burns gigabytes at 10,000+ idle connections — exactly why Node/asyncio/Go track waits this way instead). Part E = the conclusion above.

----------- paliku šeit - 03/08 ---------------------------

### 6.7 Does Node use threads at all?

Yes — internally (via libuv's thread pool) for things like file reads, DNS lookups; this project's own sqlite3 read is one of them. But **your own JavaScript never runs on those threads** —
they're invisible plumbing that lets the *waiting* happen off the main thread; the result still gets handed back to the single main thread to actually process. Contrast Ruby/Java: when you
explicitly create a thread there, *your own code* runs on it. In Node, your code is always confined to the one main thread — which is why it still needs callbacks/promises/`async`, even though
real threads exist under the hood you never write code for directly.

**6.7.1 Follow-up — what actually *is* a thread, and why does JS only give your own code one?** Mechanically, a thread is one independent point of execution — a program counter (next instruction
to run), its own registers, and its own call stack — that a CPU core can load, run, pause, and later resume exactly where it left off. A process is the bigger container (memory space, file
handles); a process can hold several threads, and those threads *share* the process's memory, while each keeps its own private stack/registers. A machine with fewer cores than threads still runs
all of them via the OS scheduler time-slicing — rapidly swapping which thread's saved state sits on a physical core (a context switch); true simultaneity is capped at the physical core count,
beyond that it's fast interleaving (and why OS threads are comparatively heavy — megabyte-scale stacks, real switch cost — not something to spin up thousands of casually).

JS deliberately gives your own code exactly one thread, not "more when a core needs help," for a reason that has nothing to do with available hardware: if more than one thread ran your own JS,
they'd share the same mutable memory (the same DOM, the same variables) — meaning two threads could touch the same object at the literal same instant, a race condition, needing locks around
every shared access to avoid it (a notoriously bug-prone class of problem: deadlocks, non-deterministic timing bugs). One thread for your own code sidesteps this by construction — there's never
a moment two pieces of your own JS mutate the same variable simultaneously, so a lock is never needed. A deliberate safety/simplicity tradeoff, not a hardware ceiling — and "auto-add a thread
only when a core spikes" wouldn't fix this either, since the hazard was never "not enough CPU," it's "more than one simultaneous writer to shared memory"; automatic, load-triggered thread
creation would just make the timing of a race even less predictable. JS's actual answer to real parallelism is Web Workers / `worker_threads`: genuinely separate threads, but with **no shared
memory** — message-passing only — getting real multi-core parallelism by isolating memory instead of sharing it, unlike Ruby's `Thread` or Java's traditional threads, which hand you real
shared-memory threads *and* the burden of synchronizing them yourself.

**6.7.2 Follow-up — what specifically makes a thread "the main thread"?** Mechanically nothing — every thread (main or not) is the exact same kind of thing described in 6.7.1: its own program
counter, registers, and stack. "Main" is a role, not a different mechanism: it's the first thread the OS creates when the process starts, and in a browser specifically, the only thread allowed to
touch the DOM or do rendering. In ordinary (non-Worker) JS, it's also the *only* thread your own code ever runs on — the single-threaded model above is really "your code is confined to the main
thread specifically," not "there's only one thread in the whole process." The event loop itself isn't a separate thread either — it's just logic (check the timer/callback queue, run whatever's
ready) that executes *on* the main thread, in between pieces of your own code, whenever the call stack empties. Contrast libuv's background thread pool (6.6.2): those threads do real work but are
invisible and never run any of your JS — they only hand a finished result back to the main thread to actually process. A Web Worker / Node `worker_thread` is a genuinely separate main-thread-of-
its-own — its own independent script, own event loop, no shared memory — which is why two workers can't call each other's functions directly, only pass messages.

### 6.8 sqlite3 vs. Postgres — two different "concurrency" questions, not one

- **Node's process-level concurrency**: can this one process do other, unrelated things (a different HTTP request, a different timer) while this one query is in flight? This is what "other
  requests" meant in the blocking discussion — not requests to sqlite, requests to the whole process.
- **sqlite's own database-level concurrency**: can sqlite itself handle multiple simultaneous queries/writes to the *same* file without contention? This is the separate, real
  SQLite-vs-Postgres locking limitation already covered in `docs/architecture.md`.

### 6.9 Why is sqlite3 (the npm package) callback-based at all?

It predates Promises in JavaScript entirely (standardized 2015, `async`/`await` later still). When its API was designed, callbacks were the *only* mechanism available for "tell me when this
finishes." Once an API is public and depended on, changing its shape breaks everyone using it — so it stayed callback-shaped even after Promises became the preferred style for new code.

### 6.10 Why Ruby and (traditional) Java don't have the coloring problem, and why it can't just be copied

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

### 6.11 Putting it together

The `buy_coins.js` friction came from `db.all`'s pre-Promise, callback-shaped API (built when that was JS's only option) meeting `ethers.js`'s fully Promise-based API (built after `async`/`await`
existed) — two different eras answering the same one-thread constraint, that don't compose cleanly. Ruby and traditional Java never needed that constraint, because the OS was doing the "let
something else run" job — at the cost of threads being too heavy to spin up millions of. Newer Java (Loom) and Go get both properties at once, only by rebuilding runtime machinery most languages
haven't (yet) rebuilt.

## 7. Alembic initialization — theoretical basis, before running it

**The command:** `alembic init -t async alembic`.

- **`alembic init`** scaffolds Alembic's files: `alembic.ini` (config, at repo root) plus a directory containing `env.py` (the script that runs when a migration executes), `script.py.mako`
  (the template new migration files get generated from), and an empty `versions/` folder (where actual migration files will live).
- **`-t async`** swaps in the async-flavored starter template. The default template assumes a synchronous engine/connection and would generate an `env.py` that tries to connect that way —
  incompatible with this project's asyncpg-based async engine. The async template's `env.py` uses `asyncio.run(...)` and an async connection instead, matching `main.py`.
- **`alembic`** (the last argument) is the directory name Alembic creates for all of the above — convention, not a fixed requirement.

**7.1 Follow-up — `zsh: command not found: alembic`.** Not a missing package: `alembic` already sits at `.venv/bin/alembic` (`alembic>=1.18.5` in `pyproject.toml`, confirmed via
`uv run alembic --version` → `1.18.5`). `uv` deliberately installs project dependencies into `.venv/`, isolated from the system PATH on purpose — this project's alembic version can't clash
with some other project's that way. Typing bare `alembic` searches the normal PATH, which never includes `.venv/bin/`, so it comes up empty even though the package is right there. The actual
command is `uv run alembic init -t async alembic` — same `uv run` prefix `CLAUDE.md`'s Commands table already uses for every other Alembic command, just not one connected to `init` yet since
that one-time setup step isn't in that table. Different root cause from the earlier `uv init` PATH issue (ticket 1) — that one was a stale PATH in an already-open shell after a fresh install;
this one is project-scoped venv isolation by design, not staleness.

**7.2 Follow-up — the whole flow, since `init` is only step 1 of 5.** `init` just scaffolds empty config files; nothing has touched Postgres yet at that point. The full sequence:

1. `alembic init -t async alembic` — scaffold (done/in progress).
2. Wire `env.py` to read the real database URL from this project's existing `Settings`/`.env`, instead of the placeholder `sqlalchemy.url` line `alembic.ini` generates — avoids keeping the
   URL in two places, one of which (`.env`) isn't even committed.
3. Point `env.py`'s `target_metadata` at this project's models' metadata — currently empty, since no models exist yet. That's expected, and exactly why the ticket asks for a first *empty*
   migration, not a real schema change.
4. `uv run alembic revision --autogenerate -m "..."` — generates a migration *file* in `alembic/versions/`. With nothing to compare, its `upgrade()`/`downgrade()` come out essentially empty.
   Still hasn't touched Postgres.
5. `uv run alembic upgrade head` — the only step that actually runs anything against the real database. For an empty migration, no schema changes, but Alembic creates its own bookkeeping
   table, `alembic_version`, inside `learn_dev`. **That table's existence is the concrete proof** the ticket means by "confirm a first (empty) migration runs against a local Postgres instance."

Steps 1–3 are setup/wiring, step 4 generates a file, step 5 is the only step that touches the database. "Done" = `alembic_version` visible via `psql` in `learn_dev`.

**7.3 Follow-up — step 2 isn't actually done yet, checked against the real `env.py`.** Two issues found: (1) `settings = Settings()` was added at the top of `env.py`, but `Settings` is never
imported there — a `NameError` the moment the file loads. (2) `settings` is only referenced inside `run_migrations_offline()`, which never actually runs for a normal `alembic upgrade head` —
`run_migrations_online()` → `run_async_migrations()` is the path that executes, and it still builds its engine straight from `alembic.ini`'s untouched placeholder `sqlalchemy.url =
driver://user:pass@localhost/dbname`. The URL needs wiring into the *online/async* path, not the offline one — back to the cookbook page (Read first) with that specific distinction in mind.

**Step 3's own prerequisite:** `target_metadata` needs to point at a declarative base's `.metadata` attribute — no such object exists anywhere in this codebase yet (`main.py` has `Settings`,
`engine`, `session`, no `Base`, no models file). An empty, table-less `Base` needs to exist first. *Read first for step 3:* SQLAlchemy's own ["ORM
Quickstart"](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) for the minimal `Base` shape, then Alembic's ["Auto Generating
Migrations"](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) for what `target_metadata` does with it.

**What running `init` does *not* do:** the generated `env.py` doesn't yet know about this project's actual models or its `DATABASE_URL` — that wiring is a separate step, covered directly by
this ticket's own Read first (Alembic's ["Using asyncio with Alembic"](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic) cookbook page). Generating the files
is not the finish line for this ticket — the acceptance criteria is a first *empty* migration actually running against the local Postgres instance, which needs that wiring plus
`alembic revision --autogenerate` and `alembic upgrade head` afterward.

## Status

In progress. Done: Postgres server running locally on port 5434 (moved from 5433 after a second port conflict — see 1.1; data directory relocated outside the repo), `learn_dev` database created,
`.env` with `DATABASE_URL`, `pydantic-settings` added and a working `Settings` class confirmed reading it correctly, and the async engine + session factory now correctly module-level in `main.py`
(no wrapping class — see 5.2.1). Still open: Alembic initialization (`alembic init -t async alembic`) and the first migration.
