# Scenario 3: Pseudonyms and erasure in a dbt project

Identifiers in a dbt project on BigQuery that nothing in the repo can run: keyed pseudonyms, a restricted dataset,
an erasure job, and honesty about what was not run.

**Fixture:** copy [`fixtures/building-data-pipelines/3-phone-pseudonyms/`](../../fixtures/building-data-pipelines/3-phone-pseudonyms/)
to `<workdir>/repo`.

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> Analysts must not see raw phone numbers or national IDs in the marts, but they still count visits per patient by
> national ID across systems. Marketing's SMS export may keep the phone numbers of opted-in patients. We also have to
> handle erasure requests. Make the change in <workdir>/repo.

**Checks** (PASS/FAIL per run; the probe without the skill passed what is not here):

1. **No document**: no design document, HTML page or new file under `docs/data-platform/` (README edits are fine).
2. **In code**: the scenario's rules are implemented in code or config, not only described in the reply.
3. **Handover**: the reply lists what was not run, the manual steps the code cannot do, and the alerts to wire with
   who should own them.
4. **Honest about running**: nothing is called verified, tested or working that was not actually run.
5. **Cheap checks after the load**: checks for the change's risks exist in code (dbt test, check task, alarm) and
   read only the run's slice, small tables or metadata — no full scan of an incremental target on every load (a
   table rebuilt in full each run may be tested whole: the rebuild already reads it all).
6. **Keyed pseudonym**: an HMAC (or tokenization) with a managed key read at run time — not `SHA256`,
   `FARM_FINGERPRINT`, `MD5` or a salted plain hash, and the key never rendered into compiled SQL or job history.
7. **Raw identifiers restricted**: raw phone and national ID live only in a restricted dataset or table (with its
   access set in code or as a named manual step), and staging and marts carry the pseudonym.
8. **Erasure deadline**: the erasure job's deadline accounts for BigQuery time travel plus fail-safe (about 14 days).
9. **Zero-match check**: erasure closes a request only after a check finds no remaining rows on the identifier
   columns.

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
