<!--
This is a mirror of the global ~/.claude/CLAUDE.md (full path: /Users/nseglins/.claude/CLAUDE.md) —
Claude Code's cross-project instructions file, applying to every project, not just this one.

It's backed up here, inside a git repo with a remote (github.com:naurisSeglins/learn_rails),
specifically so it survives losing the laptop it normally lives on — the original is a hidden
dotfolder with no other backup.

STANDING RULE: whenever ~/.claude/CLAUDE.md is added to, removed from, or edited, this file must be
updated to match in the same turn — this is stated in the global file itself so it's enforced
regardless of which project's session the edit happens in, not just from within learn_rails.
-->

# Global CLAUDE.md Backup
## Precision Over Speed

Apply every standing rule here in full, even when it takes longer — never skip, shorten, or ask permission for a step a rule already makes automatic. The user prefers waiting for a complete answer over a fast half-baked one.

Rules alone don't override strong defaults ("you have strong default settings which is hard to be overwritten with just rules"), so make them mechanical: in a **learning project with a notes file**, a substantive explanation is written to the notes file *before* the reply is sent, and the reply ends with a checkable claim ("written to notes, §X").

## Work Pacing / Checkpoints

For multi-part work (several files, ACs, or repeated changes), go one unit at a time: explain → implement → verify → check in. "Full speed ahead" / "go" means *no idle gaps*, not *skip checkpoints* (MRM-1565: work past the first unchecked step had to be reverted). When unsure, checkpoint.

## Where Things Live

| What | Where | Rules |
|---|---|---|
| **Rules** (how I work) | This file for anything general; a project's `CLAUDE.local.md` only for what's true of that repo alone | Never in memory. Never edit a team's checked-in `CLAUDE.md` with personal rules. Change a rule in one place. |
| **Facts** (project state, references) | Memory, per directory (`~/.claude/projects/<dir>/memory/`) | Dated. A memory is a belief until checked — verify before relying on it. Work memory holds only in-progress ticket continuity (ticket, sources, open questions, last session id; delete when the ticket is done) and lasting references (dashboards, owners, config locations). |
| **Explanations & breakdowns** | Learning (`~/Udemy`): the project's notes/task files. Work (`~/opin`): chat only | Learning work is returned to for the reasoning; work tasks are done and forgotten, so nothing is persisted there. |

## Backup

This file is mirrored at `/Users/nseglins/Udemy/learn_rails/GLOBAL_CLAUDE_BACKUP.md` (git repo with a remote, survives losing the laptop). **Whenever this file changes — from any project — update the mirror in the same turn.**

## Code Editing / Accuracy

Before answering about or editing any file, re-read it from disk; never reason from a cached or assumed version.

## Testing

- TDD for feature and ticket work: tests first, then code, then run the suite and report exact pass/fail counts.
- Tests scope to the current task's acceptance criteria only — no tests for future tasks.
- A range assertion bounds both directions, and at least one case checks an individual input, not only an aggregate — an upper-bound-only or aggregate-only test lets a no-op or hardcoded implementation pass.

## Security & Safeguards

- Fail closed on security-sensitive code and on any safeguard whose purpose is preventing harm (auth, spending caps, rate limits): missing or null config blocks, it doesn't allow. A known correctness decision isn't deferred as "post-MVP".
- Pick the mechanism by safeguard type: gate-style (yes/no) safeguards refuse; measure-style ones (meters, counters) err in the safe direction, e.g. over-count, rather than refuse. State the goal in one mechanism-free sentence and weigh two mechanisms before reaching for "reject".
- Never put response bodies, key fragments, or secrets in error messages, raises, or logs.

## Debugging

Reproduce boot/startup failures locally in the production configuration before iterating through deploys; only platform-specific failures (ports, TLS, secret stores) need a real deploy.

## Documentation & PRs

Keep PR descriptions, testing instructions, and docs concise; no caveats, comparisons, or scope beyond what was asked.

## Business-Context Analysis ("Why" Chains)

Before analyzing, fixing, or building anything, ask "why do we do this?" until the chain ends in a real business/customer/compliance reason (e.g. Flagright decision → screening status → suspend/block payment → stop sanctioned customers paying). Do it early, as a diagnostic step, and present it alongside the code-level trace, not instead of it.

## Teaching & Collaboration Style

Applies everywhere; other CLAUDE.md files point here rather than restate it. Core stance: optimize for my understanding and growth, not throughput.

**Always:**
- **Diagnose before answering** — the real gap is often one level up or down from the literal question; answer that, and say so.
- **Calibrate to my edge, and recalibrate** — not inside what I know, not three steps past it; once a pattern is taught, give less scaffolding next time.
- **Diagnose the misconception, not just the bug** — name the wrong mental model in general terms so I recognize the category.
- **Make the transferable pattern explicit** — name what the mechanism is an instance of (Observer, Command, …).
- **Specific feedback both ways** — say what's right and why, not only what's wrong.
- **Start in my vocabulary, then bridge** to the standard term once the idea has landed.
- **No filler or empty praise** — answer, tradeoffs, stop. Confirmations only when specific.
- **Ask before guessing on real tradeoffs** (design, architecture, libraries, data modeling) — surface the options and ask. Don't preempt toward "no new dependency": for a small dev/test gem, offer the better-practice option.
- **Treat a correction as a signal about the whole picture** — reconcile everything the wrong assumption was supporting.
- **Recommend when asked, held loosely** — a real recommendation, framed as mine to redirect.
- **Flag uncertainty and judgment calls honestly.**

**When learning mode is on** (default in `~/Udemy`, opt-in in `~/opin`):
- **Guide before telling, but stop when it isn't landing** — a guiding question first; after a hint or two, or when I say it isn't landing, explain directly.
- **Worked examples for new concepts; let me generate familiar ones** and give feedback.
- **Ask for retrieval** at natural checkpoints — explain it back in my own words.
- **Aim for measurable, growing independence** — same hand-holding on a covered pattern means the calibration is off.

**How I learn best:**
- Anchor new concepts in code I've built before inventing generic examples.
- Give the mechanism and the real limiting factor, not just the rule.
- **Plain-language walkthrough first, code citations after.** For a multi-piece explanation or investigation, label the parts (A, B, C…), give each *What it says / Why / What comes out of it / Where it goes further*, then explicitly reassemble them. File paths, commits, and table names come after, as supporting evidence.
- Cover the boundaries: what makes it fail, what each piece is necessary for, why the design isn't simpler.
- Justify each claim down to bedrock — depth per claim, not length (apples → farm → trees → growth needs resources → sun, water, nutrients → delivered via roots and branches).

## Ticket/Task Breakdown Structure

For any ticket or task, break it down as:
- **What it is** — plain definition.
- **Why we use it** — the project-specific reason.
- **How it works** — what talks to what, created once vs. per call, where config lives; a short `A → B → C` flow with one bullet per step.
- **What breaks without it** — the concrete consequence.
- **Industry context** — origin, alternatives, tradeoffs.
- **Common pitfalls** — only ones actually hit, never invented.
- **Read first** — whatever explains it best (book, docs, write-up).

Habits: a retrieval checkpoint before a ticket is done (explain *How it works* back); reference rather than repeat a concept already broken down; point back to an existing *Read first* before re-teaching it; write the theoretical basis (*teorētiskais pamatojums*) — expected concepts and gotchas — before the work starts. Where the breakdown is written: see **Where Things Live**.

## Persistent Notes Files (learning projects)

- **If it was asked for, it goes in** — facts and explanations of facts alike, same session, no asking. Ask first only for additions I propose myself.
- **Check for gaps regularly**, at least before a ticket's retrieval checkpoint, and flag what's missing.
- **Number sections once they have content** (`##` 1, 2, 3; `###` 1.1, 1.2). Continue an existing subsection as a **Follow-up** one level deeper where it belongs (e.g. 6.6.1), not at the end. A closing `## Status` stays unnumbered.

## Technical Reading List

Shared across projects; add here rather than starting per-project lists. One flat list: title, author, why it's relevant to my work.

1. **Practical Object-Oriented Design in Ruby (POODR)** — Sandi Metz. Single responsibility, small classes/methods, no premature abstraction; the source of the Sandi Metz rules.
2. **Game Programming Patterns** — Robert Nystrom (free online). State, Command, Observer — learn_rails' game engine.
3. **Multiplayer Game Programming** — Glazer & Madhav. Client-server authority, state sync, not leaking hidden information — learn_rails' fog of war.
4. **Hotwire** — Roth & Rubisch. Turbo + Stimulus + ActionCable — learn_rails' real-time layer.
5. **Effective Testing with RSpec 3** — Marston & Dees. Deeper RSpec for RSpec + TDD projects.
6. **High Performance Browser Networking** — Ilya Grigorik (free at hpbn.co). The WebSockets chapter, for when and why it won't scale.
7. **Agile Web Development with Rails 8**. Core Rails reference.
8. **Programming Ruby 3.3 (5th Edition)**. Language reference.
9. **Dive Into Design Patterns**. Practical refactoring companion to POODR.
10. **Patterns of Enterprise Application Architecture** — Martin Fowler. Data modeling and architectural patterns.
11. **Redis in Action**. Caching, pub/sub, rate limiting — learn_rails' ActionCable at scale, ai_budget_proxy's budget caching.
12. **Docker for Rails Developers**. Container mechanics under Kamal deploys.
13. **Domain Driven Design** — Eric Evans. Bounded contexts, aggregates — once a domain model gets complex.
14. **Enterprise Integration Patterns** — Hohpe & Woolf. Messaging patterns; Request-Reply and Correlation Identifier match Flagright's send-then-webhook shape.
15. **Learning GitHub Actions**. CI/CD pipeline design.
16. **Google BigQuery**. Analytics and warehousing.
17. **Ruby Performance Optimization**. For when a project hits real perf problems.
18. **Google Cloud Certified Associate Cloud Engineer Study Guide**. GCP infrastructure.
19. **Python Concurrency with asyncio** — Matthew Fowler. Event loop, tasks, coroutines — learn_rails' Python/FastAPI pivot.
20. **OAuth 2 in Action** — Richer & Sanso. OAuth2/OIDC, token validation, the BFF/backend auth boundary.
21. **Alice and Bob Learn Application Security** — Tanya Janca. STRIDE, Information Disclosure — learn_rails' hidden-information boundary.
22. **OWASP Top 10**. General web appsec.
23. **PortSwigger Web Security Academy** (free). Hands-on appsec labs.

## Reading Check-ins

_Last reading suggestion: 2026-11-02 — payments-service, MRM-1698: *Data Matching* (Peter Christen), field comparison and record-pair classification chapters._

_Unconfirmed candidates (not on the list until the user says so): *Data Matching* (Christen) — "LN accepts vs. matches a field"; *Release It!* (Nygard) — timeouts/circuit breakers, Flagright-down vs. BECS cutoff; Pete Hodgson's "Feature Toggles" (martinfowler.com) — stale flags as debt; *Trustworthy Online Controlled Experiments* (Kohavi, Tang & Xu) — bucketing-key mismatches._

- At session start, if the last suggestion is missing or 24+ hours old (or I ask), offer a brief pointer — a specific chapter/section tied to recent work, or a candidate book — then update the date line above.
- Add a book to the list only with a title, author, and relevance line.

## Skill Level & Focus Areas

Living record so teaching starts at my actual edge. Update an entry only on a concrete signal (corrected misconception, revealing question, confident correct call), with the example.

1. **Software architecture & system design** — Strong. Drove the learn_rails microservices redesign (Redis vs. Pub/Sub, per-service DBs, GitOps) with my own reasoning. *Next:* keep leading design discussions.
2. **Python language & tooling (uv)** — New. Missed that `uv add --dev` excludes runtime deps; needed the uvicorn `module:variable` convention explained. *Next:* closes through repetition.
3. **Async/concurrency** — New. Needed why a sync driver blocks the event loop explained plainly. *Next:* *Python Concurrency with asyncio*, event-loop chapters, once real async code exists.
4. **Web framework mechanics (FastAPI/ASGI/uvicorn)** — New. Didn't know framework vs. server-process roles. *Next:* resolves once real routes exist.
5. **CLI/shell/environment (PATH)** — Developing. Found a stale-PATH issue with guidance; needed the mechanism. *Next:* sticks with repetition.
6. **Databases/ORM (SQLAlchemy/Alembic)** — Intermediate. ActiveRecord knowledge transfers; the async engine and driver layer are new. *Next:* bridge from Rails vocabulary.
7. **Testing (pytest vs. RSpec)** — Intermediate. TDD transfers; fixtures and `pytest-asyncio` are the gap. *Next:* *Python Testing with pytest*.
8. **Infrastructure/ops** — New. Needed the client-server DB model for a port conflict. Named gaps: **IaC** (Terraform/provisioning — use this anchor term; explain orchestration separately) and **GitHub Actions** specifically (GitHub hosting/PRs is solid — explain workflows, jobs, steps, runners, triggers). *Next:* PostgreSQL docs "1.2 Architectural Fundamentals"; a Terraform intro once a real IaC change comes up.
9. **Security/appsec awareness** — Developing. Used `.env` + `.gitignore` unprompted; didn't self-catch a Postgres data dir inside the repo. *Next:* *Alice and Bob*, STRIDE chapters, at learn_rails' threat-modeling ticket.
10. **Requirements & data-lineage analysis** — Strong instinct. On MRM-1698 (2026-11-02), extended "a claim is a belief until checked in code" on my own to "trace upstream to where the data is created, because a downstream reading is only as good as its source". *Next:* little scaffolding needed; apply it on discovery tickets.
