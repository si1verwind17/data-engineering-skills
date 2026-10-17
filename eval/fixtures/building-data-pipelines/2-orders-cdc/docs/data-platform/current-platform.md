# Current platform

The shop's orders live in an RDS PostgreSQL 16 database; a nightly job copies them into the warehouse (RDS
PostgreSQL 16) for the operations dashboard in Metabase.

## Components

| Component | What it does | Tool | Source |
|---|---|---|---|
| Shop database | Orders, written by the shop service | RDS PostgreSQL 16 (Multi-AZ) | found in repo (`terraform/main.tf`) |
| Read replica | Reporting copy of the shop database | RDS PostgreSQL 16 | found in repo (`terraform/main.tf`) |
| Warehouse | Report tables | RDS PostgreSQL 16 | found in repo (`terraform/main.tf`) |
| Scheduler | Runs the jobs | Airflow (MWAA) | told by you |
| BI tool | Operations dashboard | Metabase | told by you |

## Unknown

Who is on call for the pipeline.
