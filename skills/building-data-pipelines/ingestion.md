# Ingestion — failures, redrive, deletes

Read for any ingestion change. The rules for code that loads records and
survives the records that fail.

- **A bad record is never dropped silently; how it fails depends on the
  source.** Records that fail validation, a cast or the write either fail
  the run or go to a dead-letter table:
  - **Fail the run** — the default for a batch whose source can be read
    again (a table, files that stay in place, an API window still
    editable). Name the bad keys and the error in the failure and alert;
    the source still holds the records, so fixing the cause and rerunning
    the period recovers them. A bad record here usually means the source's
    contract changed, which should stop the load, not be set aside.
  - **Dead-letter table** — when the source cannot be read again (a topic
    past retention, an expiring cursor, a push or webhook), when one record
    would block everything behind it (a stream, CDC), or when a high-volume
    load expects a few bad records (unreadable lines in event files). Pair
    a batch dead letter with a reject threshold — fail the run above N bad
    rows — so a broken source still stops the load.
- **Transient vs poison.** Timeouts and throttling retry in place with
  backoff. Only records that cannot succeed fail the run or go to the
  dead-letter destination — otherwise it fills with work that would have
  succeeded.

Where there is a dead letter:

- **Dead-letter record** = original payload + error + source position
  (offset / LSN / page cursor) + first-seen time + attempt count. Without the
  source position, redrive cannot be ordered.
- **Redrive with a version guard.** Apply a full-row record only if its source
  position is newer than the stored row's (`updated_at` only when no position
  exists — timestamps tie and drift across app servers). For partial/patch
  events (only changed fields, no full state), re-read the current row from
  the source instead of applying the patch. A CDC placeholder for an
  unchanged large column is not a patch: keep the stored value.
- **Alert on dead-letter growth** and name who triages it; an unwatched
  dead-letter queue is silent data loss.

Every load:

- **Soft delete in the cleaned layer.** Record source deletes as tombstones
  (`is_deleted` + delete version) and filter them out of business tables. A
  hard delete leaves nothing to compare against, so a late or redriven update
  resurrects the row. Hard delete only for erasure.
- **A source that hard-deletes and offers no change feed** (a poll on
  `updated_at` sees nothing): take the stored keys from the window in which
  deletes happen — e.g. orders created in the last 24 hours when
  cancellations are deleted within a day — and ask the source **by key**
  which of them still exist. Tombstone only the keys it no longer has.
  Never infer a delete from a source query filtered on a column that
  changes (`updated_at`): a row updated since then is missing from that
  set and would be tombstoned while live. If the source query fails or
  returns nothing, tombstone nothing.
- **Reconcile from independent counts**: rows the source query returned
  against rows the target received (plus rows dead-lettered, where there is
  a dead letter). A count derived from the other two always balances and
  never fails.

## Self-review

- Does a bad record fail the run, naming its key, for a source that can be
  read again — and is a dead letter there only for a source that cannot,
  a stream, or a load with a reject threshold?
- Does every dead-letter record carry the source position?
- Is the apply guarded on source position, with `updated_at` only as a
  fallback?
- Do source deletes become tombstones, and do business tables filter them?
- Does the job reconcile read = written (+ dead-lettered), and does
  something alert when a run fails or dead letters arrive?
- Does the batch take its period from the run (SKILL.md, Reruns and
  backfill)?
- Is every table the pipeline rebuilds swapped in atomically, with no
  `drop` + `create` in place?
- Does every check's filter use a column the table it reads is indexed or
  partitioned on?
