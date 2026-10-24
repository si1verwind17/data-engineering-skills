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

Every source states what happens to a record that cannot succeed — never
dropped silently — and picks one of two paths:

- **Fail the run** — the default for a batch source that can be read again
  (a table, files that stay in place, an API window still editable): the
  run fails naming the bad keys and alerts, and a rerun of the period
  recovers once the cause is fixed. A bad record there usually means a
  contract change that should stop the load.
- **Dead-letter table** (drawn on dotted edges in the Pipeline diagram),
  with an alert on growth and a named owner — when the source cannot be
  read again (a topic past retention, an expiring cursor, a push), when one
  record would block everything behind it (a stream, CDC), or when a
  high-volume load expects a few bad records; a batch dead letter comes
  with a reject threshold that fails the run above it.

Name the mechanisms in one line each so a reviewer sees them handled; their
settings belong in the build, not the design:

- Transient failures retry with backoff; only poison records fail the run or
  dead-letter, a dead-letter record keeping payload, error and **source
  position**.
- **Redrive guarded by source position, not `updated_at`** — timestamps tie
  and drift, so an old record could overwrite a newer one.
- **Deletes kept as tombstones** in the cleaned layer — a hard delete lets a
  late or redriven update resurrect the row.
- Batch runs take their period from the run, so any period can be rerun or
  backfilled.

In a design review, a source with no stated bad-record path, a dead-letter
record without the source position, a redrive on `updated_at` alone, or hard
deletes in the cleaned layer are gaps. So is a dead letter on a re-readable
batch source with no reason given: it adds a table, an alert, an owner and
redrive code that a failed run and a rerun already cover.
