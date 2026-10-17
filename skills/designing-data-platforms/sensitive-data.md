# Sensitive data and erasure

Read when regulated data is in scope (PII, card data, health data) or
erasure is asked. Rules for the Why section's sensitive data and erasure.

## Sensitive data

Decide **per column**, top-down:

1. No analytics use for the raw value → do not load it.
2. Needed only to join or count → **keyed pseudonym, never a plain hash**,
   with a key the engine can use without a service call per row (a
   KMS-wrapped keyset, not per-row KMS signing):
   a hash of a phone number or national ID is reversed by hashing every
   possible value. On BigQuery, the document names its built-in SHA-256
   masking rule as one of those plain hashes.
3. Needed only in aggregate (age band from birth date) → derive, drop the
   source.
4. Raw value needed by a few people → separate restricted table keyed by the
   pseudonym.
5. Partial value needed by many → column masking.

**Card numbers are never loaded**: keeping them out keeps the whole platform
out of PCI DSS scope, which no access control achieves. A source that stores
full card numbers is a compliance issue to escalate, not just a column to
drop.

**Enforce at the layer every path passes through.** List every way people
reach the data — BI tool, direct SQL, notebooks, exports. If the BI tool is
the only path and its edition can enforce the needed row/column control,
BI-level control is enough. Otherwise — no BI tool, a BI edition that
cannot restrict, or any direct warehouse access — restrict in the
warehouse or catalog. BI tools query through one service account, so BI
permissions protect only BI users and per-user warehouse policies never
apply through them. In a single-engine warehouse (BigQuery, Snowflake) its
native column and row policies are the primary control; with several
engines reading the data, the separate restricted table is the default
because it works everywhere.

**Personal data the stated use case needs is in scope** (names and
contacts in a support lookup): design its protection — restricted role,
masking, export controls — rather than leaving it out pending an owner.

Applicability of regulations, agreements with every third party the data
reaches (cloud provider, BI or messaging vendors), and retention periods
are decisions for a compliance owner: record each as a question, never
assert it.

## Erasure requests

Erasure is its own pipeline, not a wait for the source change to flow
through — the raw layer keeps every earlier version, and any rebuild from it
restores what was erased. The design states:

- **Every copy it must reach**: raw, cleaned, business, serving stores,
  reverse-ETL targets, exports — overwritten in place, so totals stay intact.
- **The deadline includes retention the platform cannot purge**: time
  travel and backups (BigQuery: up to 7 days time travel + 7 days
  fail-safe, about 14 days).
- **PII kept in one restricted table**, so erasure touches one small table.
- In one line each: a request log as the audit record; a zero-match check
  before closing; a **suppression list** that ingestion, backfills and
  restores read, so a replay cannot bring the person back; and deleting an
  encryption key (crypto-shredding) is not erasure — encrypted personal data
  is still personal data.

In a design review, a plain hash used as a pseudonym, erasure that skips
raw or exports, or no suppression list are gaps.
