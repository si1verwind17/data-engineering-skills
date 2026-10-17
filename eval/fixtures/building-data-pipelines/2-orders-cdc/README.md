# orders-platform

Infrastructure and jobs for the orders reporting pipeline on AWS.

- `terraform/`: the shop's RDS PostgreSQL 16 primary and its read replica, the warehouse (RDS PostgreSQL 16), an
  ECS cluster for long-running services, a Kinesis stream.
- `dags/`: Airflow (MWAA) jobs.
- `apply/`: Python jobs that apply changes into the warehouse (empty so far).
- `docs/data-platform/`: the design and the current platform.
