# Scenario 4: Sensitive data (GCP)

Sensitive data on BigQuery: card data, keyed pseudonyms, enforcement, erasure, and compliance questions.

**Fixture:** none; the run writes into an empty `<workdir>`.

**Prompt** (verbatim, after the arm's preamble from [`eval/README.md`](../../README.md)):

> A clinic-booking platform (GCP, BigQuery as warehouse) wants analytics.
> Source tables include: patient name, national ID, phone, date of birth,
> appointment diagnosis notes, and — in a legacy billing module — full
> payment card numbers. Requests: analysts want cohort analysis by age group
> and diagnosis; marketing wants patient phone numbers for SMS campaigns; a
> data scientist wants raw diagnosis notes for an NLP model; the BI tool is
> Metabase. Design how this data enters and is governed in the warehouse,
> in <workdir>/sensitive-data-design.md.

**Checks** (PASS/FAIL per run):

1. Card numbers are not loaded, AND the design states this keeps the
   warehouse out of PCI DSS scope.
2. Pseudonyms are keyed, and the design says never a plain hash — naming
   BigQuery's SHA-256 masking rule — because phone numbers and national IDs
   can be reversed by hashing every possible value.
3. Access is enforced in BigQuery/catalog, with the reason BI permissions
   are insufficient (single service account; no per-user policy through
   Metabase).
4. Erasure is its own pipeline reaching every copy including raw and copies
   outside the warehouse (exports, the SMS list), with a deadline that
   includes time travel + fail-safe (~14 days on BigQuery), and PII kept in
   one restricted table so erasure touches little.
5. A suppression list (or equivalent) is named so replays/backfills cannot
   restore an erased subject.
6. Does not present crypto-shredding / key deletion as sufficient erasure.
7. Regulatory applicability, provider agreements and retention are recorded
   as compliance-owner questions, not asserted.
8. Deliverable includes a per-column sensitive-data table (each column's
   decision) and an erasure section, at design level (no SQL or job code).
9. Stays in scope: no platform tier decision and no alternatives for
   BigQuery or Metabase (both are given).
10. **Top of document**: opens with a plain-words Decision (what gets built, what does not), then the Architecture diagram — nothing (questions, tier essay, tables) before them.
11. **Architecture rules**: the diagram reads left to right from sources to users; every data arrow points the way data moves and is labelled with the action; boxes give tool and role; boundaries show where things run, drawn only where the hosting is stated.
12. **Build steps**: numbered, design level (no code or commands), each saying what it delivers.
13. **No process narration**: the document never describes how it was produced ("non-interactive", "this run", "taken as given") or mentions the skill or its files.

A miss is a skill wording fix, not a test change — unless the check itself was wrong.
