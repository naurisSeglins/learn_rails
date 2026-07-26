# Learning Notes

A log of substantive conceptual deep-dives that come out of reading (articles, book chapters) or open-ended discussion — distinct from `books.md` (what to read and why) and `exercises.md` (deliberate practice assignments). Condensed to the actual understanding reached, not a raw transcript. Newest first.

## 2026-07-26 — "What Color is Your Function?" (Bob Nystrom) and the async coloring problem

Triggered by *SQLAlchemy 2 In Practice*'s Chapter 7 (this project's Phase 0 Postgres ticket), which links to the essay. Worked through using a real example pulled from an old personal project (`buy_coins.js`, a crypto trading bot), not a hypothetical.

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
- **Higher-order** just means "a function that takes another function as an argument (and/or returns one)." `db.all`'s third argument isn't data — it's a function `db.all` will *call itself*, later, once the read finishes. Proof of the mechanism: pass a non-function there (`db.all(sql, [], "hello")`) and it fails at the moment sqlite3 tries to *invoke* "hello" as a function — confirming that's literally what happens internally.

### Query parameters (`[]`) vs. writing values into the SQL string
- Never build a query by pasting a value into the string (`"...WHERE id = " + userInput`) — the database receives one string and parses all of it as SQL, with no way to distinguish "this part is data" from "this part is a command." If `userInput` contains SQL syntax, it gets run. That's SQL injection, mechanically.
- The placeholder (`?`) + separate parameters array sends the query text and the value as two distinct pieces; the database substitutes the value in a way that can never be re-parsed as more SQL, regardless of its contents.
- In this file's actual query, there are no placeholders — nothing dynamic is being inserted — so the array is empty. It's still passed because `db.all`'s signature always expects three arguments in that position.
- The placeholder+array way is correct default practice for any value that isn't a literal you typed yourself.

### Why pass a function instead of getting a value back?
Assign-then-use (`data = getSomething(); useIt(data)`) only works if `getSomething()` finishes instantly. Reading from disk takes real time — at the moment `db.all`'s own call returns, the data genuinely doesn't exist yet, so there's nothing to hand back as an ordinary return value. Instead, you hand `db.all` a function in advance, and *it* calls *you* once the real work is done — the calling direction reverses.

### "Returns immediately" vs. "fetches all the data" — resolving the apparent contradiction
"Returns immediately" describes the *statement* `db.all(...)` finishing and letting the next line run — not the data being ready. Mechanically: `db.all` starts the read and returns before it's complete; the read continues in the background; only once every row is actually retrieved does it call the callback with the real `rows`. The call and the underlying work finish at two different times.

### What "blocked" actually means
The one thread running the JavaScript stops advancing and sits idle until one specific thing (the disk finishing) happens. This freezes *everything else* because ordinary JS execution has exactly one thread doing all the work — every other pending callback, timer, or request has to take a turn on that same thread. If it's stuck waiting, nothing else can run, not because it's forbidden, but because there's no other thread free to run it on.

### Does Node use threads at all?
Yes — internally (via libuv's thread pool) for things like file reads, DNS lookups. This project's own sqlite3 read is one of them. But **your own JavaScript never runs on those threads** — they're invisible plumbing that lets the *waiting* happen off the main thread; the result still gets handed back to the single main thread to actually process. Contrast Ruby/Java: when you explicitly create a thread there, *your own code* runs on it. In Node, your code is always confined to the one main thread — which is why it still needs callbacks/promises/`async`, even though real threads exist under the hood you never write code for directly.

### sqlite3 vs. Postgres — two different "concurrency" questions, not one
- **Node's process-level concurrency**: can this one process do other, unrelated things (a different HTTP request, a different timer) while this one query is in flight? This is what "other requests" meant in the blocking discussion — not requests to sqlite, requests to the whole process.
- **sqlite's own database-level concurrency**: can sqlite itself handle multiple simultaneous queries/writes to the *same* file without contention? This is the separate, real SQLite-vs-Postgres locking limitation already covered in `docs/architecture.md`.

### Why is sqlite3 (the npm package) callback-based at all?
It predates Promises in JavaScript entirely (standardized 2015, `async`/`await` later still). When its API was designed, callbacks were the *only* mechanism available for "tell me when this finishes." Once an API is public and depended on, changing its shape breaks everyone using it — so it stayed callback-shaped even after Promises became the preferred style for new code.

### Why Ruby and (traditional) Java don't have the coloring problem, and why it can't just be copied
Two fundamentally different answers to "how does a program wait without freezing":

- **Real OS threads (Ruby, traditional Java).** The OS runs several independent lines of execution; when one blocks on I/O, the OS schedules a different thread onto the CPU meanwhile. No keyword needed — the "let something else run while I wait" job belongs to the OS, invisible to function signatures. Ruby (MRI) has a GIL limiting true parallel *bytecode* execution, but releases it during I/O waits, so threads still meaningfully overlap.
  - **Cost**: OS threads are heavy (megabyte-scale stacks each, real context-switch overhead) — fine for hundreds of concurrent things, breaks down at tens of thousands. This is the actual reason JS/Python didn't just copy this.
- **One thread, explicit pause points (JS, Python `asyncio`).** JS is single-threaded by design (partly to avoid multi-thread DOM-mutation bugs) — with only one thread, you *can't* block it, so a function has to explicitly declare "I might pause here" (`async`/`await`), letting the event loop run other work meanwhile and resume this function later. The color exists *because* there's no second thread to fall back on.

**Why not just adopt the other model?**
- JS: single-threaded at the level of the whole language/ecosystem — real shared-memory threading would require re-architecting the language and breaking the huge single-threaded-assumption ecosystem. (Node's "worker threads" don't share memory the normal way, precisely because full threading doesn't fit the model.)
- Python: the GIL caps true parallelism similarly to Ruby's; Python has started removing it optionally (free-threaded builds), and library tricks (`greenlet` — which SQLAlchemy itself uses internally in places) implement Ruby/Loom-style implicit stack-switching under the hood, but this remains a specialized mechanism, not the mainstream `asyncio` model.
- **The deepest reason**: implicit suspend/resume at *any* point in a call stack (not just an explicit `await`) requires the runtime to support continuations — capturing and restoring execution state arbitrarily. That's not a small patch; it's a multi-year runtime rewrite (what Java's Project Loom actually took, to get virtual threads that look like blocking code but don't block a real OS thread). There's also a genuine, unresolved philosophical disagreement: explicit `async`/`await` makes it *visible* exactly where a function might yield (useful for reasoning about correctness); implicit fiber-switching hides that, which can make some concurrency bugs harder to spot.

### Putting it together
The `buy_coins.js` friction came from `db.all`'s pre-Promise, callback-shaped API (built when that was JS's only option) meeting `ethers.js`'s fully Promise-based API (built after `async`/`await` existed) — two different eras answering the same one-thread constraint, that don't compose cleanly. Ruby and traditional Java never needed that constraint, because the OS was doing the "let something else run" job — at the cost of threads being too heavy to spin up millions of. Newer Java (Loom) and Go get both properties at once, only by rebuilding runtime machinery most languages haven't (yet) rebuilt.
