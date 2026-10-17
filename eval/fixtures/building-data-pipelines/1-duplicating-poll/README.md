# orders-pipeline

Hourly copy of the `orders` table from the shop's PostgreSQL service database into the warehouse
(PostgreSQL 16, schema `raw`), then `core.orders` for finance dashboards.

- `dags/orders_hourly.py`: scheduled hourly.
- `dags/orders_hourly_manual.py`: the same load for a period given by hand (reruns, backfills).
- `sql/core_orders.sql`: builds `core.orders` from `raw.orders` after each load.
- `tests/`: pytest, run with `pytest`.

Source notes: `orders(order_id bigint pk, customer_id, status, amount_cents, updated_at timestamptz)`.
Cancelled orders are hard-deleted from the source within 24 hours. Some service transactions stay open for
several minutes before committing.
