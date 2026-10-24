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
| 1 | 6d812bf | skill | 29/33 (3 runs) | every run fails the run for the re-readable databases; click events dead-lettered with a reject threshold in one; misses: boxes without a named tool (2), a hosting boundary drawn round unknown hosting, a generic verification list |
| 2 | 6d812bf | skill | 43/45 (3 runs) | one run passes all 15; every run dead-letters only the CDC stream and fails the run for both batch sources; misses: `current-platform.md` not written (2) |
| 3 | 6d812bf | skill | 34/36 (3 runs) | two runs pass all 12; misses: a load arrow drawn right to left, one line of process wording |
| 4 | 9eb3496 | skill | 36/39 (3 runs) | each run misses one: a leaked question number or the skill's own wording (2), one tier remark; no pseudonym computed by a per-row KMS call |
| 5 | 6d812bf | skill | 18/18 (3 runs); variant A pass at e6ce8de; variant B 3/3 at a2af0ab | variant B at e6ce8de overwrote the stale record; fixed by keeping the record until the user answers |
| 1 | — | control | 0/33 (3 runs) | no simpler tier weighed, hedged layers, no diagrams or build steps |
| 2 | — | control | 9/45 (3 runs) | no diagrams, inventory or build steps; no backfill beside CDC; SQL and settings in the design; two of three fail the batch run and quarantine the stream |
| 3 | — | control | 12/36 (3 runs) | app writes its own table, no format version, no current-platform record |
| 4 | — | control | 11/39 (3 runs) | key deletion as erasure, no suppression list, no fail-safe in the deadline |
| 5 | — | control | 8/18 (3 runs) | no current-platform record, nothing marked new |
