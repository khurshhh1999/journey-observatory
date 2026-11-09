import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("OBSERVATORY_ROOT", Path(__file__).resolve().parents[2]))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from airflow import DAG
from airflow.operators.python import PythonOperator

from pipeline.alert import write_failure
from pipeline.steps import step


def _run(step_name: str) -> None:
    step(step_name)


def failure_alert(context):
    write_failure(context)


with DAG(
    dag_id="journey_observatory",
    start_date=datetime(2025, 10, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    on_failure_callback=failure_alert,
) as dag:
    previous = None
    for name in ("generate", "stage", "link", "friction", "quality", "model", "export"):
        task = PythonOperator(
            task_id=name,
            python_callable=_run,
            op_args=[name],
        )
        if previous is not None:
            previous >> task
        previous = task
