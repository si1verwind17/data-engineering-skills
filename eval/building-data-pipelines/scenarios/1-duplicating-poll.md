# Scenario 1: A poll job that duplicates on retry

An hourly Airflow poll with a stored watermark and a copy-pasted manual twin: idempotent load, deletes, dead
letters, reruns by period, and cheap checks.

**Fixture:** copy [`fixtures/building-data-pipelines/1-duplicating-poll/`](../../fixtures/building-data-pipelines/1-duplicating-poll/)
to `<workdir>/repo`.

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> Finance found duplicate orders after a failed hourly run was retried, and we need to backfill last Tuesday. Fix the
> pipeline in <workdir>/repo.

**Checks** (PASS/FAIL per run; the probe without the skill passed what is not here):

1. **No document**: no design document, HTML page or new file under `docs/data-platform/` (README edits are fine).
2. **In code**: the scenario's rules are implemented in code or config, not only described in the reply.
3. **Handover**: the reply lists what was not run, the manual steps the code cannot do, and the alerts to wire with
   who should own them.
4. **Honest about running**: nothing is called verified, tested or working that was not actually run.
5. **Cheap checks after the load**: checks for the change's risks exist in code (dbt test, check task, alarm) and
   read only the run's slice, small tables or metadata — no full scan of an incremental target on every load (a
   table rebuilt in full each run may be tested whole: the rebuild already reads it all).
6. **Deletes captured**: source hard deletes become tombstones (or a key compare for the period records them),
   not left for later.
7. **Dead letters**: rows that cannot load go to a dead-letter table keeping their source position, with an alert.
8. **Twin DAG safe**: the manual DAG calls the same task code as the scheduled one, and the two cannot write the same
   period at once (shared pool of one slot, a lock, or equivalent).
9. **Complete**: the load reconciles rows read = rows written + rows dead-lettered, and fails or alerts otherwise.
10. **Atomic core**: `core.orders` is no longer dropped and recreated in place; readers never see it missing or half
    built (merge, transaction, or build-and-swap).
11. **Tests for failure paths**: pytest cases for a rerun of the same period and a replayed delete are added.

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
