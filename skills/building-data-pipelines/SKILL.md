---
name: building-data-pipelines
description: >-
  Use when writing, changing, fixing or reviewing data pipeline code and
  config in a repository — ingestion jobs, CDC connectors, dead letters and
  redrive, source deletes, reruns and backfills, reverse-ETL loads, masking
  or pseudonymization in transforms, and erasure jobs. Changes the code and
  config in place and adds the checks that catch silent data loss; writes no
  design document.
---

# Building data pipelines

The change lands in the repo as code, config and checks. General practice
(DAGs, SQL, dbt models, medallion layers, SCD2, compaction) is assumed
known; this skill holds the failure modes that lose or corrupt data without
an error. Output: the change and a short handover — no design document, no
HTML, no files under `docs/data-platform/`.

## A design doc is optional input

If `docs/data-platform/` holds a design for this task (or
`current-platform.md`), or the user names a document, read it and follow its
decisions and build steps. If none exists, work from the repo and the
request; never ask for a design document or write one.

## The loop

1. **Read.** The design doc if any, then the code, config and
   infrastructure the task touches — not the whole repo.
2. **Scope.** Name the task's area and read only its file:

   | Task touches | Read |
   |---|---|
   | Batch ingestion, dead letters, redrive, deletes, reruns | [`ingestion.md`](ingestion.md) |
   | Change data capture (Debezium, logical replication, change streams) | [`ingestion.md`](ingestion.md) + [`cdc.md`](cdc.md) |
   | PII, card or health data in pipelines; erasure | [`sensitive-data.md`](sensitive-data.md) |
   | Loading results back into an application database | [`reverse-etl.md`](reverse-etl.md) |

   Settle what is in and out of the change. A gap in the pipeline you are
   changing that loses or duplicates data — source deletes not captured, no
   dead-letter path — is part of the fix: build it and test it, don't defer
   it. When the repo cannot settle a
   decision the code depends on (the source cannot support CDC), state the
   limit and the options and ask once; for a change that needs a platform
   design rather than code, say the `designing-data-platforms` skill fits.
3. **Build.** Make the change in what the repo already uses — its
   orchestrator, its transform tool, its alerting; add no new tool. Then
   self-review against the area file's checklist.
4. **Verify.** Two parts, below: a test before deploy where one can run, and
   checks that run with the pipeline after deploy.
5. **Hand over.** Only what the diff cannot show: what was not verified;
   manual steps the code cannot do (create a replication slot, set a
   database parameter, deploy order); each alert to wire with an owner
   named by role (the team on call for this pipeline) for the user to
   confirm, never "someone"; risks that remain (what loses data if it
   happens, and how to recover); owner questions. Leave out empty parts.

**Never say "verified", "tested" or "works" about something that was not
run.** Say what was written and what was run.

## What every run must guarantee

Each property is built into the code or checked after the load. Apply only
those the change touches; a plain batch copy may need only Complete and
Fresh.

| Property | Meaning | How |
|---|---|---|
| Complete | nothing silently lost | **check:** the job reconciles its own counts — rows read = rows written + rows dead-lettered |
| Idempotent | a rerun or replay gives the same result | **by construction:** keyed MERGE / upsert, or overwrite of the run's period |
| Ordered | an older version never overwrites a newer one | **by construction:** version guard on source position ([`ingestion.md`](ingestion.md)) |
| Atomic | readers never see half a load | **by construction:** one transaction, staging + swap, or an as-of marker — for every table the pipeline builds, downstream ones included; `drop` + `create` in place fails it |
| Deletes honoured | a deleted row stays deleted after a late update or replay | **by construction:** tombstones; **check:** this run's rows joined to the tombstones |
| Failures visible | bad records don't pile up unseen | **check:** alert on new dead-letter rows, with a named owner |
| Fresh | data arrives within the agreed time | **check:** last successful load time, or CDC slot lag, against the agreed limit |
| Private | erased people stay erased; raw identifiers stay restricted | **by construction:** suppression list read by ingestion; **check:** once per erasure request |

**Before deploy:** if the repo has a test setup (pytest, dbt unit tests),
add cases for the failure paths the change handles — a rerun, a bad record,
a replayed delete — that execute the logic (an in-memory engine such as
SQLite or DuckDB, a fake hook), never tests that search the source text. If it has none but the logic can be isolated (the merge
statement, the dead-letter routing, the pseudonym function), test that piece
on a few rows. If nothing can run, skip it and say so.

**After deploy:** write the checks from the table in what the repo already
runs — a dbt test, a check task after the load, its existing alerting — for
the properties this change touches only. No generic checks, no retrofitting
other pipelines.

**Checks cost money: read only what the run loaded** — its partition or
time window (dbt test `where` config, a partition filter), on a column the
table is partitioned or indexed by (add the index if not), or the filter
still scans everything; on pay-per-scan
engines (BigQuery, Athena) a full scan per load is a bill. Prefer cheap
signals: the job's own counts, the small dead-letter and tombstone tables,
the database's slot-lag view. Whole-table properties come from construction,
not checks: a keyed MERGE makes the uniqueness check "no duplicate keys in
this batch"; tombstones make the delete check "this run's rows joined to
them". No whole-table checks on incremental tables (a table rebuilt in full
each run may be tested whole: the rebuild already reads it all); the one full
check is per erasure request, on the identifier columns only.

## Reruns and backfill

1. **Every batch task takes its period from the run** — the orchestrator's
   data interval (`data_interval_start` / `data_interval_end` in Airflow) or
   start/end parameters — never from "now" or a stored watermark ("rows
   since the last run") — and overwrites or merges that period, so any
   period can be rerun.
2. **Follow the repo's pattern for manual runs.** If it pairs each DAG with
   a manual twin (no schedule, period parameters), change the twin the same
   way, with two guards: both DAGs call the same task code (no copied
   logic), and the two cannot write the same period at once (a shared pool
   of one slot, or a lock). With no pattern, use the same DAG and the
   orchestrator's own backfill.
3. **CDC gaps** are filled with an incremental snapshot beside the live
   stream ([`cdc.md`](cdc.md)), not a DAG backfill.
