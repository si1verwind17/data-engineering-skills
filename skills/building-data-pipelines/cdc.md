# CDC — the traps that lose data silently

Read with [`ingestion.md`](ingestion.md) when the change sets up or changes
change data capture. Baseline: Debezium 3.x, PostgreSQL 16–18, MongoDB 4.4+
(snapshot 2026-10 — re-check version-specific behavior against current docs).

## Where the slot can live (PostgreSQL)

Check before writing connector config; a wrong source is not fixed by config.

- **Decoding from a read replica** works on PostgreSQL 16+ (RDS 16.1+, with
  `rds.logical_replication` on source and replica) and moves load off the
  primary — but it needs `hot_standby_feedback`, which pushes vacuum delay and
  bloat back onto the primary. **Aurora PostgreSQL readers cannot decode**:
  on Aurora the slot goes on the writer. Asked to read from a source that
  cannot decode, say so, give the options, and ask — don't point a connector
  at it.
- **A slot on the primary does not survive failover before PostgreSQL 17.**
  The standby promoted in its place has no copy of it; recreating it risks a
  gap and forces a re-snapshot. PG17+ failover slots need `failover=true` on
  the slot (`slot.failover=true` in Debezium), `sync_replication_slots`,
  `hot_standby_feedback`, and `synchronized_standby_slots`. A slot on a read
  replica stays when that replica is promoted; its risk is the replica being
  replaced or rebuilt — then the connector re-snapshots.

## PostgreSQL connector settings

- **Unchanged large columns arrive as a placeholder.** With the default
  replica identity, an UPDATE that doesn't touch a TOASTed column (large
  text/jsonb) emits `__debezium_unavailable_value` for it; a plain upsert
  overwrites the real value. Fix one of: `REPLICA IDENTITY FULL` on the
  table (more WAL), the reselect-columns post-processor (re-queries the
  source; can race with newer writes), or a sink merge that keeps the stored
  value when the placeholder arrives.
- **A WAL cap trades disk safety for re-snapshots.** `max_slot_wal_keep_size`
  (default unlimited) protects the primary's disk; once WAL the slot needs is
  removed, the slot is lost and the connector must re-snapshot. Without a cap,
  a stalled consumer fills the primary's disk. Set the cap AND alert on slot
  lag (`pg_replication_slots`, `pg_wal_lsn_diff`) well before it.
- **Quiet captured tables still pin WAL.** If the captured tables are idle but
  the server writes WAL elsewhere, the slot never advances. Heartbeat interval
  alone is not enough: something must write to a heartbeat table included in
  the publication. Slot on the primary: `heartbeat.action.query`. Slot on a
  read replica, which is read-only: a scheduled write on the primary (pg_cron
  or an orchestrator task every few minutes) that replicates to it.

## Transactions and ordering

- **Changes from one source transaction can land in different batches.**
  Where cross-table consistency matters (order + order items), enable
  transaction metadata (`provide.transaction.metadata`) and apply per
  transaction; Debezium emits BEGIN/END markers but the consumer must buffer.
- **Per-key ordering** comes from partitioning the topic by primary key. A
  "newer source position wins" guard is enough for current-state tables but
  not for history tables built from the change log — those need the events
  in order.

## MongoDB

- **Resume tokens expire with the oplog.** A consumer down longer than the
  oplog window cannot resume and must re-snapshot. Size the oplog (or
  `storage.oplogMinRetentionHours`) for the longest outage you will tolerate.

## Backfill alongside live CDC

- Use incremental snapshots (`execute-snapshot` signal, chunked, runs beside
  streaming, resumable; needs a primary key or surrogate key) rather than a
  separate bulk load.
- Any backfill writes through the same version guard as the stream, so it
  can never overwrite a newer streamed row, and is throttled against the
  source.

## Self-review

- Is the slot on a source that can decode, and is its failover or rebuild
  case handled?
- Does the sink keep the stored value when the placeholder arrives (or is
  replica identity / reselect set)?
- WAL cap set, slot-lag alert wired, heartbeat action query configured?
- Transaction metadata where tables must stay consistent together?
- Backfill through the stream's version guard, throttled?
- Does the handover name the slot-loss cases (replica rebuilt or replaced,
  failover, WAL cap exceeded), that each forces a re-snapshot, and how to
  run it (incremental snapshot)?
