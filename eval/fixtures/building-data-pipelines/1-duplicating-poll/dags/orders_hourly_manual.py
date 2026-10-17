from datetime import datetime

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(schedule=None, start_date=datetime(2026, 1, 1), catchup=False, tags=["orders", "manual"],
     params={"start": Param("", type="string"), "end": Param("", type="string")})
def orders_hourly_manual():
    @task
    def extract_load(params=None):
        src = PostgresHook(postgres_conn_id="shop_db")
        rows = src.get_records(
            "select order_id, customer_id, status, amount_cents, updated_at "
            "from orders where updated_at >= %s and updated_at < %s",
            parameters=(params["start"], params["end"]),
        )
        wh = PostgresHook(postgres_conn_id="warehouse")
        wh.insert_rows("raw.orders", rows,
                       target_fields=["order_id", "customer_id", "status", "amount_cents", "updated_at"])
        return len(rows)

    @task
    def build_core():
        wh = PostgresHook(postgres_conn_id="warehouse")
        with open("/opt/airflow/sql/core_orders.sql") as f:
            wh.run(f.read())

    extract_load() >> build_core()


orders_hourly_manual()
