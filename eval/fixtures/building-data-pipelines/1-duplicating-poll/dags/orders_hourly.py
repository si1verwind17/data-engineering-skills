from datetime import datetime

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(schedule="@hourly", start_date=datetime(2026, 1, 1), catchup=False, tags=["orders"])
def orders_hourly():
    @task
    def extract_load():
        last_run = Variable.get("orders_last_run_time", default_var="1970-01-01T00:00:00+00:00")
        now = datetime.utcnow().isoformat() + "+00:00"
        src = PostgresHook(postgres_conn_id="shop_db")
        rows = src.get_records(
            "select order_id, customer_id, status, amount_cents, updated_at "
            "from orders where updated_at > %s",
            parameters=(last_run,),
        )
        wh = PostgresHook(postgres_conn_id="warehouse")
        wh.insert_rows("raw.orders", rows,
                       target_fields=["order_id", "customer_id", "status", "amount_cents", "updated_at"])
        Variable.set("orders_last_run_time", now)
        return len(rows)

    @task
    def build_core():
        wh = PostgresHook(postgres_conn_id="warehouse")
        with open("/opt/airflow/sql/core_orders.sql") as f:
            wh.run(f.read())

    extract_load() >> build_core()


orders_hourly()
