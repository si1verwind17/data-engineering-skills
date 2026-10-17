# Reverse ETL and serving loads

Read when the change loads analytics results into an application database or
a serving store.

- **Write into a table or schema the pipeline owns** and the app only reads —
  never into the app's own tables, where an app write and a load collide.
- **Make each load visible whole.** Load into a staging table and swap it in
  (rename in one transaction, or a view repointed at the end), or write
  an as-of marker the app reads last. The app must never show a half-loaded
  period.
- **Late-arriving data** is handled by reprocessing a trailing window of
  periods on each run (the window the source's lateness needs), not by
  appending corrections.
- Personal data the use case needs travels with its protection: a restricted
  role on the target, masked values for wider audiences
  ([`sensitive-data.md`](sensitive-data.md)).

## Self-review

- Does the load write only tables the pipeline owns?
- Can the app ever read a half-loaded period?
- Does each run reprocess the trailing window lateness needs?
