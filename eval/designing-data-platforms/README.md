# Evaluations: designing-data-platforms

Analytics data platforms: tier and per-layer tool choice, ingestion failure handling, serving and reverse ETL,
sensitive data and erasure. The checks cover only what agents without the skill missed: a probe run without the
skill dropped every check those agents already passed 3/3 (layering, grain, SCD2, watermark pitfalls, idempotent
reruns, compaction, late-data windows and more).

## Scenarios

| Scenario | What it tests |
|---|---|
| [1](scenarios/1-platform-tier-aws.md) | a new platform for an e-commerce company on AWS |
| [2](scenarios/2-ingestion.md) | ingestion from Postgres, a document database and a SaaS API |
| [3](scenarios/3-modeling-serving.md) | new needs on a running Iceberg lakehouse, including reverse ETL |
| [4](scenarios/4-sensitive-data-gcp.md) | patient and card data entering BigQuery |
| [5](scenarios/5-existing-platform-repo.md) | a change to an existing platform the skill reads from a repo |

## Pending validation

None.

## Latest results

Each scenario's latest run, Sonnet, graded by an independent judge. `Skill@` is the commit whose skill content was
evaluated.

| Scenario | Skill@ | Arm | Result | Notes |
|---|---|---|---|---|
| 1 | a0ce040 | skill | 32/36 (3 runs) | every engine feature relied on sits in a verify-before-building list; misses: a self-hosted BI tool drawn inside a managed-services boundary (2), questions placed before the Decision |
| 2 | c5358ff | skill | 42/45 (3 runs) | one run passes all 15; a replica slot gets a recovery that does not write to the replica; misses: process wording (2), a batch path that fails without an alert |
| 3 | a0ce040 | skill | 34/36 (3 runs) | one run passes all 12; misses: a store drawn once with arrows looping back into it (2) |
| 4 | a0ce040 | skill | 37/39 (3 runs) | one run passes all 13; misses: the SHA-256 masking rule not named, a second diagram without labelled arrows |
| 5 | c5358ff | skill | 19/21 (3 runs, checks 1–6 and 9); variant A pass at e6ce8de; variant B 3/3 at a2af0ab | misses (one run): a component without its repo file, the connector's heartbeat query stated as writing on the primary |
| 1 | — | control | 3/36 (3 runs) | free-form essays with no diagrams or verification list; CDC from a replica and Firehose into streaming ingestion presented as settled |
| 2 | — | control | 9/45 (3 runs) | no diagrams, inventory or build steps; snapshot loaded before streaming instead of beside it; SQL and settings in the design |
| 3 | — | control | 12/36 (3 runs) | app writes its own table, no format version, no current-platform record |
| 4 | — | control | 11/39 (3 runs) | key deletion as erasure, no suppression list, no fail-safe in the deadline |
| 5 | — | control | 12/21 (3 runs) | no current-platform record, nothing marked new, no failover, WAL cap or dead letters |
