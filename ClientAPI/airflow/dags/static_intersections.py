import json
from datetime import datetime
from typing import Tuple

from airflow import DAG
from airflow.hooks.base_hook import BaseHook
from airflow.models import Variable
from services.gmaps import GMapsService
from services.s3 import S3Service


class StaticIntersectionsFactory:
    """
    Factory to create DAG for populating intersection locations from an existing intersections dataset using Google API
    """

    @staticmethod
    def get_name() -> str:
        return "static-intersections"

    def __call__(
        self,
        agency_id: str,
        agency: str,
        env: str,
        schedule_interval: str = "@daily",
        *args,
        **kwargs,
    ) -> Tuple[str, DAG]:
        ds = "{{ ds }}"

        # S3 buckets
        assets_bucket = f"scp-analytics-{env}--assets"

        # Connections
        aws_conn_id = "aws_default"
        google_maps_conn_id = "gmaps_default"

        dag_id = f"{self.get_name()}--{agency_id}"
        with DAG(
            catchup=False,
            dag_id=dag_id,
            default_args={"depends_on_past": False},
            description="Google Maps-based intersection locations",
            schedule_interval=schedule_interval,
            start_date=datetime(2018, 5, 2),
            tags=[self.get_name(), agency],
        ) as dag:
            ds = "{{ ds }}"

            partition = f"agency_id={agency_id}/utc_date={ds}"
            prefixes = {"intersections": f"{assets_bucket}/intersections/{partition}"}

            s3_service = S3Service(aws_conn_id=aws_conn_id)

            gmaps_conn = BaseHook.get_connection(google_maps_conn_id)
            gmaps_conn_details = json.loads(gmaps_conn.get_extra())
            google_maps_api_key = gmaps_conn_details.get("gmaps")

            gmaps_service = GMapsService(api_key=google_maps_api_key)

            (
                s3_service.check_prefixes(prefixes=prefixes)
                >> gmaps_service.ingest_street_address_geocodes(
                    task_id="ingest-street-address-geocodes",
                    s3_bucket=assets_bucket,
                    s3_partition=partition,
                )
            )

            return dag_id, dag


factory = StaticIntersectionsFactory()

agencies = Variable.get("agencies_list", deserialize_json=True)
agency_configs = [
    Variable.get(f"{agency}_config", deserialize_json=True) for agency in agencies
]

for agency_config in [c for c in agency_configs if factory.get_name() in c.get("dags")]:
    dag_id, dag = factory(**agency_config, **agency_config.get(factory.get_name(), {}))
    globals()[dag_id] = dag
