# Scenario 5: Existing platform given as a repo

A change entangled with an existing platform the skill must learn from a repo: it records the current platform,
then designs the change on it.

**Fixture:** copy [`fixtures/designing-data-platforms/5-existing-platform/`](../../fixtures/designing-data-platforms/5-existing-platform/)
to `<workdir>/platform-repo`. The run's working directory is `<workdir>`. Two one-run variants grade checks 7 and 8:

- **Variant A (empty repo):** `<workdir>/platform-repo` is an empty folder.
- **Variant B (stale record):** the fixture as above, plus `<workdir>/docs/data-platform/current-platform.md` listing
  the same platform but with Metabase as the BI tool (the repo has Superset).

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> Product wants order status changes to show on the operations dashboard within 5 minutes; today they see
> yesterday's data. Our data platform is in <workdir>/platform-repo. Design the change, in
> <workdir>/order-status-design.md.

**Checks** (PASS/FAIL per run; checks 1–6 and 9 on the main runs):

1. **No needless offer**: does not ask whether to answer questions or read a repo (the path was given).
2. **Repo first, one batch**: the design reflects what the repo holds (nightly `orders_daily` extract from the RDS
   replica, dbt on Athena, Iceberg marts, Superset, Airflow on EKS); the questions it records are only what the repo
   cannot answer (who operates it, budget, the exact freshness each consumer needs), in one batch.
3. **current-platform.md**: written at `<workdir>/docs/data-platform/current-platform.md` (nothing written inside
   `platform-repo/`), with the existing architecture and each component marked `found in repo`, naming the file.
4. **Change on the current architecture**: the design opens with the Decision, then the Architecture showing the
   existing platform with the new components (for example CDC from the orders database and a fresher path to the
   dashboard) marked new.
5. **Keeps the stack**: no re-pick or alternatives for Airflow, dbt, Athena, S3/Glue, Iceberg or Superset.
6. **Ingestion design still fires**: the Why section says where the CDC slot lives (replica or primary) and what
   happens on failover, names WAL cap / slot-lag alert and heartbeat in one line, and has a version-guarded apply
   with dead letters for bad events. Connector settings are not required.
7. **Variant A**: the reply or document says the repo holds no pipeline or infrastructure files and falls back to
   asking; no current platform is invented.
8. **Variant B**: records one question about which BI tool is current (Metabase in the record, Superset in the
   repo) and does not silently overwrite the record.

9. **Engine features checked**: no function, connector, sink or managed-service feature the design relies on is
   presented as settled when the vendor's current docs list it as unsupported, deprecated or community-only;
   unconfirmed ones sit in a verify-before-building list. The judge looks each one up.

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
