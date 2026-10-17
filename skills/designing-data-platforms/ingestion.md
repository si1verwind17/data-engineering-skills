# Ingestion — method per source, failures, deletes

Read for any ingestion design. Rules for the Why section's source inventory
(per source: ingestion method, delete capture, failure handling), which the
Pipeline diagram draws.

## Method per source

Pick each source's method from what the source supports, and say why:

- **Change data capture (CDC)** — reading the database's change log — when
  the source offers one and the freshness or the deletes need it: it sees
  hard deletes and long-running transactions that a poll on `updated_at`
  misses. Where it can run is a design decision: see [`cdc.md`](cdc.md).
- **Batch poll** on a change timestamp when there is no change log, or the
  freshness allows it. A source that hard-deletes rows needs a delete
  capture beside the poll: a periodic compare of the source's keys against
  the stored keys, missing ones recorded as deleted.
- **Records editable after creation** (a SaaS API whose data changes for 30
  days): re-read that whole window on each run, not only new records.

## Failure handling

Every pipeline has a dead-letter path: records that cannot succeed go to a
dead-letter table (drawn on dotted edges in the Pipeline diagram), with an
alert on growth and a named owner. Name the mechanisms in one line each so a
reviewer sees them handled; their settings belong in the build, not the
design:

- Transient failures retry with backoff; only poison records dead-letter,
  each keeping payload, error and **source position**.
- **Redrive guarded by source position, not `updated_at`** — timestamps tie
  and drift, so an old record could overwrite a newer one.
- **Deletes kept as tombstones** in the cleaned layer — a hard delete lets a
  late or redriven update resurrect the row.
- Batch runs take their period from the run, so any period can be rerun or
  backfilled.

In a design review, a dead-letter record without the source position, a
redrive on `updated_at` alone, or hard deletes in the cleaned layer are gaps.
