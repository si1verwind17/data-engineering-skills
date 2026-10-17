# clinic-analytics (dbt)

dbt project on BigQuery (project `clinic-analytics`, datasets `staging`, `marts`, `exports`). Sources land daily in
dataset `raw` from the booking service (one table per source table, appended, partitioned by `_loaded_at` date).

Runs in the team's CI with the production profile; there is no local profile in this repo.

Backlog:
- Marketing gets `exports.marketing_sms` daily as a CSV for SMS campaigns.
- Legal says we must be able to handle erasure requests ("delete my data") from patients; none handled yet.
