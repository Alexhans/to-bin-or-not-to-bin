"""Run a tutorial Dag for one evening with `dag.test()`, and return what each task returned.

The Airflow checks' conftest gives them their own Airflow home and database first.
"""

import datetime as dt
import json
import os
from pathlib import Path

import pendulum

USAGE_KEY = "usage"
MODEL_KEY = "__AIRFLOW__COMMON_AI_MODEL_NAME__"


def run(dag, day: dt.date) -> dict:
    """Run `dag` as it would run at 7pm on `day`, and return {task_id: what it returned}.

    If a task asked a model, also print its usage as a `[bin_day]` line.
    """
    from airflow.models.xcom import XComModel
    from airflow.sdk.serde import deserialize
    from airflow.utils.session import create_session

    # dag.test() reads the Dag from its folder, so point Airflow at this Dag's folder.
    os.environ["AIRFLOW__DAG_PROCESSOR__DAG_BUNDLE_CONFIG_LIST"] = json.dumps([{
        "name": "dags-folder",
        "classpath": "airflow.dag_processing.bundles.local.LocalDagBundle",
        "kwargs": {"path": str(Path(dag.fileloc).parent)},
    }])
    dag_run = dag.test(logical_date=pendulum.datetime(day.year, day.month, day.day, 19, tz="Europe/London"))
    assert dag_run.state == "success", f"The Dag run for {day} ended as {dag_run.state}"

    returned, usage, model = {}, {}, {}
    with create_session() as session:
        for xcom in session.query(XComModel).filter(XComModel.run_id == dag_run.run_id):
            value = deserialize(XComModel.deserialize_value(xcom))
            if xcom.key == "return_value":
                returned[xcom.task_id] = value
            elif xcom.key == USAGE_KEY:
                usage[xcom.task_id] = value
            elif xcom.key == MODEL_KEY:
                model[xcom.task_id] = value
        seconds = {ti.task_id: ti.duration for ti in dag_run.get_task_instances(session=session)}
    for task_id, used in usage.items():
        cost = f" cost_usd={float(used['cost']):.4f}" if used.get("cost") else ""
        print(f"[bin_day] model={model.get(task_id, '?')} tokens_read={used['input_tokens']} "
              f"tokens_written={used['output_tokens']} seconds={seconds[task_id]:.1f}{cost}")
    return returned
