# Platform selection — tier, tools, verification

Read for a new platform or a tool/tier choice. Rules for the Why section's
tier, layer table, and verification, which also decide the Architecture.

## Production load first

If reports slow down a production database, the first step — before any
pipeline exists — is pointing those reports at a read replica. It fixes the
stated pain in days, and every later tier still needs it as a clean
extraction source.

## Tier ladder

Start at the lowest tier that fits; move up only on an observed symptom, never
on projected size. Load known today — current event volume, current
concurrent users, a stated access pattern — is observed: design for it from
day one (e.g. high-concurrency point lookups get a serving store, not the
lake engine). There is no vendor-neutral size threshold — published GB
cutoffs come from vendors selling the next tier.

| Tier | Shape | Move up when |
|---|---|---|
| 0 Replica | Read replica of the service DB; BI reads it | Reports need to join several sources, or need history the source doesn't keep |
| 1 Postgres warehouse | Copy sources into one Postgres; SQL + materialized views | Core reports or view refreshes no longer finish inside their refresh interval; sustained I/O wait; replica lag from heavy reads |
| 2 Columnar warehouse | BigQuery / Snowflake / Redshift, or DuckDB/MotherDuck / ClickHouse on a budget | Several engines must share the data, raw files/events arrive at volume, or warehouse cost outgrows object storage + compute |
| 3 Lakehouse | Open table format on object storage + catalog + engines | — |

Postgres materialized views recompute fully on every refresh (`CONCURRENTLY`
needs a unique index and still recomputes); `pg_ivm` is the only incremental
option, for a limited SQL subset. Plan refresh cost before relying on them.

## One default per layer

Commit to one tool per layer, then name one alternative and the condition that
switches to it ("—" where no real alternative exists). A design that lists
"X or Y or Z" for a layer has not decided.

| Layer | Default | Switch when |
|---|---|---|
| Orchestration | Airflow — when someone owns operating it (managed Airflow when paying) | No one owns operating it → cron / CI running dbt. ML/AI pipelines → Flyte |
| BI | Metabase | Advanced visualization, SQL exploration, or per-group row filtering on a free tool → Superset (row-level security is open source; no column masking) |
| Table format | Iceberg | Upsert-heavy near-real-time tables AND every reading engine supports it → Hudi (or Paimon on Flink-centric stacks) |
| Transform | dbt (SQL) | Logic SQL cannot express → Spark |
| CDC | Debezium | Managed CDC already in the cloud contract and it writes what you need |

Metabase open source has no row/column security or per-user impersonation
(paid features, also when self-hosted; impersonation does not support
BigQuery). On the free build, isolate groups by adding the same database
several times, each with a service account scoped to that group's tables.

## Verify compatibility at decision time

When choosing tools that share data, check how they combine — table-format
**version** × every engine and managed service that reads or writes it ×
catalog — against current docs.

- **With web access:** a compatibility matrix; every cell names its source
  (doc URL) and the date checked.
- **Without:** no matrix. Write a short **verify-before-building** list —
  each combination to confirm, what could break, and where to check (the
  vendor doc page) — without saying why there is no matrix, and apply the
  snapshot below silently as your best current knowledge.

Snapshot (2026-10) — guidance for your choices, never a citation:

- Iceberg **v3** (deletion vectors, row lineage): Spark and Snowflake full;
  Trino experimental (no row-level DML); BigQuery read-only preview; Athena
  cannot read v3. Use **v2 unless every engine supports v3** — "latest" is not
  the default.
- Hudi: Athena, Trino, BigQuery read-only (BigQuery copy-on-write only);
  Snowflake none.
- AWS DMS writes CSV/Parquet change files to S3, not Iceberg — a merge step is
  needed. Glue's Iceberg REST endpoint and S3 Tables are REST catalogs.
- Open-source Trino has no query result cache and no CSV export from the
  Iceberg connector.
- Lake Formation row/column/cell filters are enforced by Athena, Redshift
  Spectrum, EMR, and Glue Spark 5.0+ — not by open-source Trino on Glue.
