# CDC — where it can run and what it costs

Read with [`ingestion.md`](ingestion.md) once change data capture is a
candidate. Baseline: Debezium 3.x, PostgreSQL 16–18, MongoDB 4.4+ (snapshot
2026-10 — re-check version-specific behavior against current docs).

## Where the slot can live (PostgreSQL)

A logical replication slot is the server-side bookmark CDC reads from.

- **On a read replica** on PostgreSQL 16+ (RDS 16.1+, with
  `rds.logical_replication` on source and replica): moves decoding load off
  the primary, but needs `hot_standby_feedback`, which pushes vacuum delay
  and bloat back onto the primary. **Not on Aurora PostgreSQL readers** —
  there the slot goes on the writer.
- **On the primary, it does not survive failover before PostgreSQL 17**: the
  promoted standby has no copy, and recreating it risks a gap and forces a
  re-snapshot. PG17+ failover slots keep it, with settings on both servers.
  A slot on a read replica stays when that replica is promoted; its risk is
  the replica being replaced or rebuilt. Recovery from that cannot write to
  the replica: a read-only incremental snapshot where the connector supports
  one on a standby (chunked, beside the stream), otherwise a full
  re-snapshot that re-reads every captured table with streaming held back.
  Name which, and its cost.
- **No source that can decode** (no logical replication allowed, a managed
  service that hides it): fall back to a batch poll with a periodic key
  compare for deletes ([`ingestion.md`](ingestion.md)), and say what
  freshness that gives.

## MongoDB

Change streams resume from a token that expires with the oplog: size the
oplog for the longest consumer outage you will tolerate — a capacity
decision, not a setting to leave at default.

## Footprint

Kafka + Kafka Connect is not mandatory: Debezium Server streams to Kinesis,
Pub/Sub, Pulsar, HTTP, Iceberg and others. At a few changes per second with
a small team, the lighter footprint usually wins.

## Name these in one line each

The design names each risk and its mitigation so a reviewer sees it handled;
the settings belong in the build:

- **WAL cap plus slot-lag alert** — an uncapped slot can fill the primary's
  disk; a capped one is lost when it falls behind and forces a re-snapshot.
- **Heartbeat on quiet tables** — an idle captured table stops the slot
  advancing and pins WAL; with the slot on a replica, the heartbeat is
  written on the primary.
- **Unchanged large columns** (large text/jsonb) arrive as a placeholder that
  a plain upsert would write over the real value.
- **Transaction boundaries** where tables must stay consistent together
  (order + order items).
- **Backfill beside the live stream** (incremental snapshot) through the
  same version guard, never a separate bulk load over newer rows.

In a design review, a slot on an Aurora reader, a slot on a pre-17 primary
with no failover answer, a replica slot whose recovery writes to the replica,
or no WAL cap and lag alert are gaps.
