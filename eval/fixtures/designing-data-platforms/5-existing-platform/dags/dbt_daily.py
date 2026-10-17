"""Run the dbt project against Athena after the nightly extracts."""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor

with DAG(dag_id="dbt_daily", schedule="0 3 * * *", start_date=datetime(2026, 1, 1), catchup=False) as dag:
    wait = ExternalTaskSensor(task_id="wait_orders", external_dag_id="orders_daily", external_task_id="extract_orders")
    run = BashOperator(task_id="dbt_build", bash_command="cd /opt/dbt && dbt build --target athena")
    wait >> run
