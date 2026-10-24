# Scenario 2: Implement a build step from a design document

CDC from a PostgreSQL read replica, following the design document the repo already holds.

**Fixture:** copy [`fixtures/building-data-pipelines/2-orders-cdc/`](../../fixtures/building-data-pipelines/2-orders-cdc/)
to `<workdir>/repo`. **Variant A (one run):** copy `2a-orders-cdc-aurora/` instead (Aurora PostgreSQL; the design
says to capture from the reader).

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> Implement build step 2 of our orders CDC design. Repo: <workdir>/repo.

**Checks** (PASS/FAIL per run; the probe without the skill passed what is not here):

1. **No document**: no design document, HTML page or new file under `docs/data-platform/` (README edits are fine).
2. **In code**: the scenario's rules are implemented in code or config, not only described in the reply.
3. **Handover**: the reply lists what was not run, the manual steps the code cannot do, and the alerts to wire with
   who should own them.
4. **Honest about running**: nothing is called verified, tested or working that was not actually run.
5. **Cheap checks after the load**: checks for the change's risks exist in code (dbt test, check task, alarm) and
   read only the run's slice, small tables or metadata — no full scan of an incremental target on every load (a
   table rebuilt in full each run may be tested whole: the rebuild already reads it all).
6. **Heartbeat that works on a replica**: with the slot on the read-only replica, the heartbeat is written on the
   primary (scheduled write to a heartbeat table in the publication), not only a heartbeat interval.
7. **Slot loss named**: the reply or config says the slot is lost when the replica is rebuilt or replaced (forcing a
   re-snapshot) and what to do then.
9. **Recovery needs no writes on the replica**: the recovery the run sets up or names works against the read-only
   replica — a read-only incremental snapshot (no signal-table watermark writes) over a channel that does not write,
   or a full re-snapshot with its cost stated. A default incremental snapshot through a signal table, which writes
   watermarks over the connector's replica connection, fails this check even when the signal row is inserted on the
   primary.
8. **Variant A (Aurora; one run, graded with checks 1–5 instead of 6, 7 and 9)**: states that an Aurora PostgreSQL reader cannot host a logical slot, gives the options
   (slot on the writer, or change the design), asks once, and points no connector at the reader.

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
