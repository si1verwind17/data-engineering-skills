# Serving and reverse ETL

Read for serving, modeling, or syncing analytics results back into an
application. Rules for the Why section's serving and model design.

Load known today — concurrent users, a stated access pattern — sets the
serving store from day one: high-concurrency point lookups or row-level
lists go to a serving store (Postgres, a search index), not the lake engine;
aggregates stay in the lake or warehouse.

Personal data the use case needs is in scope: a customer-service lookup
gets customer names and contacts. Design their protection (a restricted
role, masking for wider audiences, controlled exports) instead of leaving
the fields out pending a decision; record the policy questions as open
questions.

## Lake tables

- **State the table-format version** in the design. Iceberg v3 (deletion
  vectors, row lineage) is not readable by every engine yet — in the
  2026-10 landscape Athena cannot read v3 and Trino's support is
  experimental — so use **v2 unless every engine that reads the table
  supports v3**, and say which was chosen.
- Late-arriving events are a modeling concern (each run reprocesses a
  trailing window); they do not make the request an ingestion design — add
  no source inventory or dead-letter rules unless sources themselves change.

## Reverse ETL

When analytics results go back into an application database, write into a
table or schema the pipeline owns and the app only reads — never into the
app's own tables, where an app write and a load collide. Name in one line
that each load becomes visible whole, so the app never shows a half-loaded
period.
