# Current platform

The shop's orders live in an Aurora PostgreSQL 16 cluster; a nightly job copies them into the warehouse (RDS
PostgreSQL 16) for the operations dashboard in Metabase.

## Components

| Component | What it does | Tool | Source |
|---|---|---|---|
| Shop database | Orders, written by the shop service | Aurora PostgreSQL 16 writer | found in repo (`terraform/main.tf`) |
| Aurora reader | Reporting copy of the shop database | Aurora PostgreSQL 16 reader | found in repo (`terraform/main.tf`) |
| Warehouse | Report tables | RDS PostgreSQL 16 | found in repo (`terraform/main.tf`) |
| Scheduler | Runs the jobs | Airflow (MWAA) | told by you |
| BI tool | Operations dashboard | Metabase | told by you |

## Unknown

Who is on call for the pipeline.
