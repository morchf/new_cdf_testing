from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from common.common import on_failure
from datetime import timedelta

with DAG(
    catchup=True,
    dag_id="test-teams-notifications",
    default_args={
        "depends_on_past": False,
        "on_failure_callback": on_failure,
    },
    tags=["test"],
    description="Test MS Teams notification",
    schedule_interval=None,
    start_date=datetime(2021, 8, 4),
) as dag:
    BashOperator(
        task_id="execute_bash_command",
        bash_command="ech",
        execution_timeout=timedelta(minutes=30),
    )
