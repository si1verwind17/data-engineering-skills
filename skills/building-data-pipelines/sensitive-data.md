# Sensitive data and erasure in pipelines

Read when the change handles PII, card or health data, or an erasure
request. What to decide per column (drop, pseudonymize, derive, restrict,
mask) is a design decision; follow the design doc or the request, and ask
when neither says.

## Pseudonyms and restricted values

- **Keyed pseudonyms only.** HMAC (or deterministic encryption) with a
  managed key the engine can use without a service call per row: a
  KMS-wrapped keyset, or a secret the pipeline reads at run time — not a
  KMS signing call per row, which hits API quotas at volume. A salt or pepper concatenated
  before a plain hash is not a keyed pseudonym. The key never appears in SQL
  text: a literal or a templated variable (dbt `var`, `env_var`) lands in the
  compiled SQL and the query history. In BigQuery, use a KMS-wrapped keyset
  (`KEYS.KEYSET_CHAIN` with `DETERMINISTIC_ENCRYPT`), or compute the
  pseudonym upstream in code that reads the key from a secret manager. A
  plain hash of a phone number or national ID is brute-forceable in minutes — including BigQuery's built-in SHA-256 masking rule,
  `SHA256()`, `FARM_FINGERPRINT()` and `MD5()`. Normalize the value before
  hashing (E.164 for phones, trimmed and upper-cased IDs) so joins match.
- **Raw values live in one restricted table** keyed by the pseudonym, in a
  dataset or schema only a named role can read, built straight from raw.
  Staging is where identifiers are split off: it carries the pseudonym and
  never the raw value, and every other model joins or counts on the
  pseudonym. Grant the access in code (Terraform, dbt `grants`) or list it
  as a manual step.
- **Card numbers are never loaded.** A source column with full card numbers
  is excluded at extract, not masked later; flag it to the owner.
- **Enforce where every path passes**: the warehouse's column or row
  policies, or the restricted table — not the BI tool, which queries through
  one service account. Exports (a CSV for marketing, a reverse-ETL target)
  read the pseudonym or the masked value, never the restricted table.

## Erasure

Run erasure as its own job, not by waiting for the source change to flow
through — the raw layer keeps every earlier version, and any rebuild from it
restores what was erased.

1. Request log: subject, requested at, approver, status — the audit record.
2. Overwrite identifying values with an unknown value in **every** copy: raw,
   cleaned, business, serving stores, reverse-ETL targets, exports. Anonymizing
   in place keeps fact rows and totals intact. Blank quasi-identifiers too
   (birth date, postcode) where they could single the person out.
3. Expire snapshots and remove orphan files; until then time travel returns
   the old values. Retention the platform cannot purge counts toward the
   deadline: state it as the job's schedule plus that retention (BigQuery:
   up to 7 days time travel + 7 days fail-safe, which nobody can expire —
   about 14 days).
4. Verify zero matches — on the identifier columns only — then close the
   request. This check runs once, inside the erasure job for that request;
   never as a test on every load. Match by joining to the request table,
   never by writing the person's identifiers as literals into query text,
   which keeps them in the query history.
5. Keep a suppression list that ingestion, backfills, and restores check, so a
   replay cannot bring an erased subject back.

Deleting a per-subject encryption key (crypto-shredding) is not erasure:
EDPB guidance treats pseudonymised and encrypted data as still personal data
(Guidelines 01/2025 on pseudonymisation). Use it alongside the overwrite,
not instead of it.

## Self-review

- Any plain hash left on an identifier? Is the key read from a secret, not
  the code?
- Do raw identifiers appear anywhere outside the restricted table?
- Does the erasure job reach every copy, expire snapshots, and write the
  suppression list that ingestion reads?
