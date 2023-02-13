import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from common.common import date_pattern, date_range, format_dict_values, on_failure
from common.constants import MP70_TABLES
from common.dates import parse_dates
from services.dwh import EvpDwhService, Mp70DwhService
from services.s3 import S3Service

LOGGER = logging.getLogger(__name__)


class Mp70DatasetFactory:
    @staticmethod
    def get_name() -> str:
        return "mp70"

    def __call__(
        self,
        region: str,
        agency: str,
        agency_id: str,
        env: str,
        pattern: List[int],
        schedule_interval: str = "@daily",
        buckets: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Tuple[str, DAG]:
        assets_bucket = f"s3://scp-analytics-{env}--assets"
        etl_bucket = f"s3://client-api-etl-{env}"

        buckets = {
            "mp70": f"{etl_bucket}/SCPVehicleData/MP70",
            "intersections": f"{assets_bucket}/intersections/agency_id=${agency_id}",
            "devices": f"{assets_bucket}/devices/agency_id=${agency_id}",
            **(buckets or {}),
        }

        bucket_mp70, bucket_intersections, bucket_devices = [
            buckets[k] for k in ["mp70", "intersections", "devices"]
        ]

        dag_id = f"{self.get_name()}--{agency_id}"
        with DAG(
            catchup=False,
            dag_id=dag_id,
            max_active_runs=1,
            default_args={"depends_on_past": False, "on_failure_callback": on_failure},
            tags=[self.get_name(), "evp", f"agency/{agency}", f"region/{region}"],
            description=f"MP70 dataset DAG ({agency})",
            start_date=datetime(2018, 5, 2),
            schedule_interval=schedule_interval,
            user_defined_macros={
                "json": json,
                "date_pattern": date_pattern,
                "date_range": date_range,
            },
        ) as dag:
            ds = "{{ ds }}"
            prefixes = {
                "mp70": f"{bucket_mp70}{ds}",
                "intersections": f"{bucket_intersections}{ds}",
                "devices": f"{bucket_devices}{ds}",
            }

            s3_service = S3Service("aws_default")

            format_dates = PythonOperator(
                task_id="parse_dates",
                python_callable=parse_dates,
                op_kwargs={
                    "date_range": "{{ dag_run.conf.get('date_range') }}",
                    "date_pattern": "{{ date_pattern(ds, %s) }}" % pattern,
                },
            )

            mp70_dwh_service = Mp70DwhService(
                conn_id="redshift_default",
                region=region,
                agency=agency,
                agency_id=agency_id,
                partitions={
                    "agency_id": [agency_id],
                    "utc_date": "{{ json.loads(ti.xcom_pull(task_ids='parse_dates')) }}",
                },
            )
            evp_dwh_service = EvpDwhService(
                conn_id="redshift_default",
                partitions={
                    "agency": [agency],
                    "date": "{{ json.loads(ti.xcom_pull(task_ids='parse_dates')) }}",
                },
            )

            (
                s3_service.check_prefixes(prefixes=prefixes)
                >> format_dates
                >> [mp70_dwh_service.prepare(), evp_dwh_service.prepare()]
                >> mp70_dwh_service.sync_tables(
                    tables=[format_dict_values(table, env=env) for table in MP70_TABLES]
                )
                >> evp_dwh_service.load_evp_metrics()
            )

            return dag_id, dag


factory = Mp70DatasetFactory()

agencies = Variable.get("agencies_list", deserialize_json=True)
agency_configs = [
    Variable.get(f"{agency}_config", deserialize_json=True) for agency in agencies
]

for agency_config in [c for c in agency_configs if factory.get_name() in c.get("dags")]:
    dag_id, dag = factory(**agency_config, **agency_config.get(factory.get_name(), {}))
    globals()[dag_id] = dag
