import ast
import json
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional
from urllib.parse import quote

import boto3
from airflow import settings
from airflow.models import Connection
from ms_teams.ms_teams_operator import MSTeamsOperator


def format_dict_values(
    dictionary: Dict[str, str], **kwargs: Dict[str, str]
) -> Dict[str, str]:
    return dict(
        zip(
            dictionary,
            map(evaluate, map(lambda x: x.format(**kwargs), dictionary.values())),
        )
    )


def items(key_values: Dict[str, List]):
    """
    Convert a dictionary to an array of key-value pairs

    Args:
        key_values Dictionary of key-value pairs

    Return: Array of key-value pairs
    """
    return [[k, v] for k, v in key_values.items()]


def evaluate(value: str):
    """
    Attempt to parse literal Python and JSON formats
    """
    try:
        return ast.literal_eval(value)
    except Exception:
        pass

    try:
        return json.loads(value)
    except Exception:
        pass

    return value


def date_pattern(ds: str, tsp_dataset_pattern: List[int]) -> str:
    # Oldest to newest date
    tsp_dataset_pattern.sort(reverse=True)

    ds = datetime.strptime(ds, "%Y-%m-%d")
    globs = [f"{ds - timedelta(days=day):%F}" for day in tsp_dataset_pattern]
    return "{" + ",".join(globs) + "}"


def date_range(date_range: Optional[List[str]]) -> str:
    """
    Converts `date_range` into Hadoop `GlobPattern`.

    **Example**: ::

        date_range(["2020-01-01", "2020-10-01"]) == "{2020-01-*,2020-02-*,2020-03-*,2020-04-*,2020-05-*,2020-06-*,2020-07-*,2020-08-*,2020-09-*,2020-10-01}"
        date_range(["2020-01-13", "2020-10-31"]) == "{2020-01-13,2020-01-14,2020-01-15,2020-01-16,2020-01-17,2020-01-18,2020-01-19,2020-01-20,2020-01-21,2020-01-22,2020-01-23,2020-01-24,2020-01-25,2020-01-26,2020-01-27,2020-01-28,2020-01-29,2020-01-30,2020-01-31,2020-02-*,2020-03-*,2020-04-*,2020-05-*,2020-06-*,2020-07-*,2020-08-*,2020-09-*,2020-10-*}"
        date_range(["2019-01-01", "2021-01-01"]) == "{2019-01-*,2019-02-*,2019-03-*,2019-04-*,2019-05-*,2019-06-*,2019-07-*,2019-08-*,2019-09-*,2019-10-*,2019-11-*,2019-12-*,2020-01-*,2020-02-*,2020-03-*,2020-04-*,2020-05-*,2020-06-*,2020-07-*,2020-08-*,2020-09-*,2020-10-*,2020-11-*,2020-12-*,2021-01-01}"
    """
    if isinstance(date_range, str):
        date_range = json.loads(date_range)
    if isinstance(date_range, str):
        # Attempt to parse multiple times, if JSON as string encoded
        date_range = json.loads(date_range)
    if not date_range:
        return ""
    assert isinstance(date_range, list) and len(date_range) == 2
    start, end = map(lambda x: datetime.strptime(x, "%Y-%m-%d"), date_range)
    assert start <= end
    months = [
        date
        for year in range(start.year - 1, end.year + 2)
        for month in range(1, 12 + 1)
        for date in [datetime(year, month, 1)]
    ]
    months_full = [
        (month_start, month_end - timedelta(days=1))
        for month_start, month_end in zip(months, months[1:])
        if start <= month_start and month_end - timedelta(days=1) <= end
    ]
    globs = (
        (
            [
                f"{start + timedelta(days=day):%F}"
                for day in range((months_full[0][0] - start).days)
            ]
            + [f"{month_start:%Y-%m-*}" for month_start, _ in months_full]
            + [
                f"{months_full[-1][-1] + timedelta(days=day):%F}"
                for day in range(1, (end - months_full[-1][-1]).days + 1)
            ]
        )
        if months_full
        else [
            f"{start + timedelta(days=day):%F}" for day in range((end - start).days + 1)
        ]
    )
    return "{" + ",".join(globs) + "}"


@lru_cache(maxsize=128)
def get_environment_url(environment_name):
    client = boto3.client("mwaa")
    response = client.get_environment(Name=environment_name)
    return response["Environment"]["WebserverUrl"]


def check_connection(connection_id: str) -> bool:
    session = settings.Session()
    return session.query(Connection).filter(Connection.conn_id == connection_id).first()


def on_failure(context):
    dag_run = context["dag_run"]
    ti = context["task_instance"]

    dag_id = dag_run.dag_id
    task_id = ti.task_id

    agency = dag_id.split("-")[-1]
    agency_conn_id = f"ms_teams_{agency}"
    conn_id = agency_conn_id if check_connection(agency_conn_id) else "ms_teams_default"

    host = get_environment_url("airflow-mwaa")
    logs_url = f"https://{host}/log?dag_id={dag_id}&task_id={task_id}&execution_date={quote(context['ts'])}"

    teams_notification = MSTeamsOperator(
        task_id="msteams_notify_failure",
        http_conn_id=conn_id,
        trigger_rule="all_done",
        message=f"`{dag_id}` has failed on task: `{task_id}`",
        button_text="View logs",
        button_url=logs_url,
        theme_color="FF0000",
    )

    teams_notification.execute(context)
