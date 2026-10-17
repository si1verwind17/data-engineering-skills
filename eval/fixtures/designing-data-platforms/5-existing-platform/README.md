# shop-data-platform

Analytics platform for the shop. Nightly Airflow jobs copy the `orders` service database (PostgreSQL 16 on RDS)
into S3 as Parquet; dbt models on Athena build the marts; Superset serves the dashboards.

- `dags/` — Airflow DAGs (Airflow runs on EKS, see `k8s/`)
- `dbt/` — models, run by the `dbt_daily` DAG against Athena
- `terraform/` — AWS resources
