import json
import logging
import re
from datetime import datetime, timedelta
from typing import Tuple

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.sensors.s3_prefix import S3PrefixSensor
from common.common import (
    check_connection,
    date_pattern,
    date_range,
    format_dict_values,
    on_failure,
)
from common.constants import RT_GTFS_TABLE, RT_RADIO_TABLE
from common.dates import parse_dates
from common.init_dags import get_dags_to_load
from services.dwh import RtGtfsDwhService, RtRadioDwhService

LOGGER = logging.getLogger(__name__)


class RtGtfsDatasetFactory:
    @staticmethod
    def get_name() -> str:
        return "rt-gtfs"

    def __call__(self, agency: str, *args, **kwargs) -> Tuple[str, DAG]:
        config = Variable.get(f"{agency}_config", deserialize_json=True)
        env = config["env"]

        rt_gtfs_config = config.get(self.get_name())

        agency_id = config["agency_id"]
        local_timezone = config["local_timezone"]

        schedule_interval = rt_gtfs_config["schedule_interval"]
        buckets = {
            "rt_gtfs_vehicle_positions": f"s3://client-api-etl-{env}/gtfs-realtime/vehicle_positions/agency_id={agency_id}/utc_date=",
            "rt_radio_messages": f"s3://rt-radio-message-{env}/agency_id={agency_id}/utc_date=",
            **(rt_gtfs_config["buckets"] or {}),
        }

        bucket_rt_gtfs_vehicle_positions, bucket_rt_radio_messages = [
            buckets[k] for k in ["rt_gtfs_vehicle_positions", "rt_radio_messages"]
        ]

        dag_id = f"{self.get_name()}-{agency}"
        with DAG(
            catchup=False,
            dag_id=dag_id,
            max_active_runs=1,
            default_args={"depends_on_past": False, "on_failure_callback": on_failure},
            tags=[self.get_name(), agency],
            description=f"Realtime GTFS dataset DAG ({agency})",
            schedule_interval=schedule_interval,
            start_date=datetime(2018, 5, 2),
            user_defined_macros={
                "json": json,
                "date_pattern": date_pattern,
                "date_range": date_range,
            },
        ) as dag:
            ds = "{{ ds }}"
            prefixes = {
                "rt_gtfs_vehicle_positions": f"{bucket_rt_gtfs_vehicle_positions}{ds}",
                "rt_radio_messages": f"{bucket_rt_radio_messages}{ds}",
            }
            s3a = re.compile(r"s3a://(?P<bucket>.+?)/(?P<prefix>.+)")

            aws_conn_id = (
                f"aws_{agency}" if check_connection(f"aws_{agency}") else "aws_default"
            )
            check_prefixes = [
                S3PrefixSensor(
                    bucket_name=m["bucket"],
                    prefix=m["prefix"],
                    task_id=f"check_prefixes_{table}",
                    timeout=timedelta(minutes=30).total_seconds(),
                    aws_conn_id=aws_conn_id,
                    execution_timeout=timedelta(minutes=30),
                )
                for table, prefix in prefixes.items()
                for m in s3a.finditer(prefix)
            ]

            format_dates = PythonOperator(
                task_id="parse_dates",
                python_callable=parse_dates,
                op_kwargs={
                    "date_range": "{{ dag_run.conf.get('date_range') }}",
                    "date_pattern": "{{ date_pattern(ds, %s) }}"
                    % rt_gtfs_config["pattern"],
                },
            )

            redshift_conn_id = (
                f"redshift_{agency}"
                if check_connection(f"redshift_{agency}")
                else "redshift_default"
            )

            rt_gtfs_dwh_service = RtGtfsDwhService(
                conn_id=redshift_conn_id,
                agency=agency,
                partitions={
                    "agency": [agency],
                    "date": "{{ json.loads(ti.xcom_pull(task_ids='parse_dates')) }}",
                },
            )
            rt_radio_dwh_service = RtRadioDwhService(
                conn_id=redshift_conn_id,
                agency=agency,
                agency_id=agency_id,
                partitions={
                    "agency_id": [agency_id],
                    "utc_date": "{{ json.loads(ti.xcom_pull(task_ids='parse_dates')) }}",
                },
            )

            (
                check_prefixes
                >> format_dates
                >> [rt_radio_dwh_service.prepare(), rt_gtfs_dwh_service.prepare()]
                >> rt_radio_dwh_service.sync_tables(
                    tables=[format_dict_values(RT_RADIO_TABLE, env=env)],
                    local_timezone=local_timezone,
                )
                >> rt_gtfs_dwh_service.sync_tables(
                    tables=[format_dict_values(RT_GTFS_TABLE, env=env)]
                )
                >> rt_gtfs_dwh_service.load_travel_time()
            )

            return dag_id, dag


for dag_id, dag in get_dags_to_load(RtGtfsDatasetFactory()):
    globals()[dag_id] = dag
