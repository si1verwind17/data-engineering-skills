"""Copy yesterday's changed orders from the orders service DB to the lake, nightly."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.amazon.aws.transfers.sql_to_s3 import SqlToS3Operator

with DAG(
    dag_id="orders_daily",
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 3, "retry_delay": timedelta(minutes=10)},
) as dag:
    SqlToS3Operator(
        task_id="extract_orders",
        sql_conn_id="orders_db_replica",
        query="""
            SELECT * FROM orders
            WHERE updated_at >= '{{ data_interval_start }}' AND updated_at < '{{ data_interval_end }}'
        """,
        s3_bucket="shop-lake-raw",
        s3_key="orders/dt={{ ds }}/orders.parquet",
        file_format="parquet",
        replace=True,
    )
