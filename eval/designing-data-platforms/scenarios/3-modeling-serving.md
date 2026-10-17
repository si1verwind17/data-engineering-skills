# Scenario 3: Modeling, layering and serving

A change to a running lakehouse: reverse ETL, format version, engine claims, scope, and needed personal data.

**Fixture:** none; the run writes into an empty `<workdir>`.

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> We have a lakehouse on AWS: Iceberg tables on S3, Glue catalog, Spark +
> dbt for transforms, Trino for queries, Superset for BI. Raw order events
> land partitioned by ingestion hour; there are now millions of small files
> and queries are slow. New needs, design them in <workdir>/model-design.md:
>
> - Finance: monthly revenue by region and product category.
> - Customer service: a searchable, filterable list of individual orders
>   (by customer, status, date) with CSV export, used by ~200 agents all day.
> - Merchant portal (our app, backed by its own PostgreSQL): each merchant
>   sees their daily sales aggregates. Today the app computes these live
>   from its Postgres and it is eating CPU/memory.
> - Product: how each customer's loyalty tier changed over time.
> - Late events: mobile clients sometimes send events up to 3 days late.

**Checks** (PASS/FAIL per run):

1. Merchant aggregates go into a pipeline-owned table/schema the app only
   reads (not the app's own tables).
2. Each reverse-ETL load becomes visible whole (staging + swap, or an as-of
   marker), so the app never shows a half-loaded day.
3. Does not adopt Iceberg format v3 (or any engine-dependent feature)
   without checking that Trino/Athena/Glue support it; states the format
   version chosen.
4. Makes no false engine-capability claim (e.g. Trino result cache, Trino
   UNLOAD/CSV export from the Iceberg connector).
5. Treats the request as a change to an existing platform: keeps the stated
   stack (no tier decision, no alternatives for tools already running, no
   compatibility matrix for them) and contains only sections for the new
   needs.
6. The customer-service list includes the customer names and contacts the
   agents need, and the design protects them (restricted role, masking for
   wider audiences, controlled exports) rather than leaving them out.
7. **Top of document**: opens with a plain-words Decision (what gets built, what does not), then the Architecture diagram — nothing (questions, tier essay, tables) before them.
8. **Architecture rules**: the diagram reads left to right from sources to users; every data arrow points the way data moves and is labelled with the action; boxes give tool and role; boundaries show where things run, drawn only where the hosting is stated.
9. **Pipeline**: a pipeline diagram of jobs and tables (jobs with how often they run, tables by layer, failures to a dead-letter table), or one sentence where a source's whole path is a single job the architecture already shows.
10. **Build steps**: numbered, design level (no code or commands), each saying what it delivers.
11. **No process narration**: the document never describes how it was produced ("non-interactive", "this run", "taken as given") or mentions the skill or its files.
12. **current-platform.md**: written in `<workdir>/docs/data-platform/current-platform.md` from the request's description, with the existing architecture and each component marked `told by you`; the design's Architecture marks the new or changed components on it.

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
