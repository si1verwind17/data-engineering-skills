# Scenario 2: Ingestion design

Ingestion only: failure handling, dead letters and redrive, deletes, CDC traps, backfill, and staying in scope.

**Fixture:** none; the run writes into an empty `<workdir>`.

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> Design ingestion into our warehouse (Postgres-based today, may move to a
> lakehouse later) for three sources, in <workdir>/ingestion-design.md:
>
> - `orders` in a PostgreSQL service DB (40M rows, ~200k changes/day). Rows
>   have `updated_at`. Cancelled orders are hard-deleted within 24h. The
>   service sometimes runs transactions lasting several minutes.
> - A document database the team says has no CDC support in our tooling.
> - A third-party SaaS REST API (rate-limited, paginated, data editable for
>   30 days after creation).
>
> Today an hourly Python job selects `updated_at > last_run_time` and
> appends to the warehouse. Last week a run failed halfway, was retried, and
> finance found duplicate orders. Ops also wants order status on a
> dashboard within a minute of changing. Propose the design.

**Checks** (PASS/FAIL per run):

1. **Method per source from what it supports**: CDC for `orders` (it catches the hard deletes and the
   long transactions an `updated_at` poll misses); batch for the document database (no CDC in their tooling) with a
   delete capture beside it; the SaaS API re-reads its 30-day editable window each run.
2. **CDC feasibility and slot placement**: where the replication slot lives (primary or a read replica, with the
   PostgreSQL version it needs) and what happens to it on failover or replica rebuild.
3. **Dead-letter path in every pipeline**: each source's pipeline has a dead-letter table with an alert and an
   owner, and the Pipeline diagram draws it.
4. **Mechanisms named in one line**: redrive guarded by source position (not `updated_at` alone), deletes kept as
   tombstones (with why a hard delete would resurrect rows), WAL cap plus slot-lag alert.
5. **Backfill named**: a backfill runs beside live CDC through the same version guard, not a separate bulk load.
6. **Design level**: no connector settings, code or SQL in the document.
7. Deliverable includes a per-source inventory (ingestion method, delete
   capture, failure handling) and a questions/assumptions section.
8. Stays in scope: no platform tier decision, BI pick, compatibility matrix,
   or erasure procedure (the request is ingestion only).
9. **Top of document**: opens with a plain-words Decision (what gets built, what does not), then the Architecture diagram — nothing (questions, tier essay, tables) before them.
10. **Architecture rules**: the diagram reads left to right from sources to users; every data arrow points the way data moves and is labelled with the action; boxes give tool and role; boundaries show where things run, drawn only where the hosting is stated.
11. **Pipeline**: a pipeline diagram of jobs and tables (jobs with how often they run, tables by layer, failures to a dead-letter table), or one sentence where a source's whole path is a single job the architecture already shows.
12. **Build steps**: numbered, design level (no code or commands), each saying what it delivers.
13. **No process narration**: the document never describes how it was produced ("non-interactive", "this run", "taken as given") or mentions the skill or its files.
14. **current-platform.md**: written in `<workdir>/docs/data-platform/current-platform.md` from the request's description, with the existing architecture and each component marked `told by you`; the design's Architecture marks the new or changed components on it.
15. **Never invent**: no BI tool, orchestrator, or hosting boundary appears that the request does not state (the request names a Postgres-based warehouse, the three sources, an hourly Python job and an ops dashboard).

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
