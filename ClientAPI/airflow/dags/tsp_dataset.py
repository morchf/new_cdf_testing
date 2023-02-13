import json
import logging
import re
from datetime import datetime, timedelta
from typing import Tuple

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.amazon.aws.operators.emr_add_steps import EmrAddStepsOperator
from airflow.providers.amazon.aws.operators.emr_create_job_flow import (
    EmrCreateJobFlowOperator,
)
from airflow.providers.amazon.aws.operators.emr_terminate_job_flow import (
    EmrTerminateJobFlowOperator,
)
from airflow.providers.amazon.aws.operators.glue_crawler import AwsGlueCrawlerOperator
from airflow.providers.amazon.aws.sensors.emr_job_flow import EmrJobFlowSensor
from airflow.providers.amazon.aws.sensors.emr_step import EmrStepSensor
from airflow.providers.amazon.aws.sensors.s3_prefix import S3PrefixSensor
from common.common import (
    check_connection,
    date_pattern,
    date_range,
    format_dict_values,
    on_failure,
)
from common.constants import CVP_TABLES
from common.dates import parse_dates
from common.init_dags import get_dags_to_load
from services.dwh import CvpDwhService

LOGGER = logging.getLogger(__name__)
S3_PATH_RE = re.compile(r"s3a://(?P<bucket>.+?)/(?P<prefix>.+)")


class TspDatasetFactory:
    @staticmethod
    def get_name() -> str:
        return "tsp-dataset"

    def __call__(self, agency: str, *args, **kwargs) -> Tuple[str, DAG]:
        config = Variable.get(f"{agency}_config", deserialize_json=True)
        tsp_config = config.get(self.get_name())

        env = config["env"]
        local_timezone = config["local_timezone"]

        schedule_interval = tsp_config["schedule_interval"]
        [
            input_bucket_trip_data,
            input_bucket_trip_log,
            input_bucket_opticom_log,
            input_bucket_device_config,
            input_bucket_intersection_status_report,
        ] = [
            tsp_config["buckets"][k]
            for k in [
                "trip_data",
                "trip_log",
                "opticom_log",
                "device_config",
                "intersection_status_report",
            ]
        ]

        output_bucket = f"s3a://client-api-etl-{env}"
        artifacts_bucket = f"s3://client-api-artifacts-{env}"

        # Get enabled metrics DAGs
        external_dag_ids = [d for d in config.get("dags") if d.startswith("metrics-")]

        dag_id = f"{self.get_name()}-{agency}"
        with DAG(
            catchup=False,
            dag_id=dag_id,
            max_active_runs=1,
            default_args={"depends_on_past": False, "on_failure_callback": on_failure},
            tags=[self.get_name(), agency],
            description=f"TSP dataset DAG ({agency})",
            schedule_interval=schedule_interval,
            start_date=datetime(2018, 5, 2),
            user_defined_macros={
                "json": json,
                "date_pattern": date_pattern,
                "date_range": date_range,
            },
        ) as dag:
            ds = "{{ ds }}"
            aws_conn_id = (
                f"aws_{agency}" if check_connection(f"aws_{agency}") else "aws_default"
            )
            emr_conn_id = (
                f"emr_{agency}" if check_connection(f"emr_{agency}") else "emr_default"
            )

            prefixes = {
                "trip_data": f"{input_bucket_trip_data}{ds}",
                "trip_log": f"{input_bucket_trip_log}{ds}",
                "device_config": f"{input_bucket_device_config}{ds}",
                "intersection_status_report": f"{input_bucket_intersection_status_report}{ds}",
            }

            check_prefixes = [
                S3PrefixSensor(
                    bucket_name=m["bucket"],
                    prefix=m["prefix"],
                    task_id=f"check_prefixes_{table}",
                    timeout=timedelta(minutes=1).total_seconds(),
                    aws_conn_id=aws_conn_id,
                    execution_timeout=timedelta(minutes=1),
                )
                for table, prefix in prefixes.items()
                for m in S3_PATH_RE.finditer(prefix)
            ]

            # Create an EMR cluster
            compute_emr_cluster_parameters = PythonOperator(
                op_kwargs={
                    "agency": agency,
                    "job_flow_overrides": tsp_config.get("job_flow_overrides"),
                },
                python_callable=self.compute_emr_cluster_parameters,
                task_id="compute_emr_cluster_parameters",
                execution_timeout=timedelta(minutes=30),
            )

            create_emr_cluster = EmrCreateJobFlowOperator(
                task_id="create_emr_cluster",
                aws_conn_id=aws_conn_id,
                emr_conn_id=emr_conn_id,
                job_flow_overrides="{{ json.loads(ti.xcom_pull(task_ids='compute_emr_cluster_parameters'))['job_flow_overrides'] }}",
                execution_timeout=timedelta(minutes=30),
            )

            job_flow_id = "{{ ti.xcom_pull(task_ids='create_emr_cluster') }}"
            wait_for_cluster = EmrJobFlowSensor(
                task_id="wait_for_cluster",
                aws_conn_id=aws_conn_id,
                job_flow_id=job_flow_id,
                target_states=["RUNNING", "WAITING"],
                poke_interval=30,  # in seconds
                execution_timeout=timedelta(minutes=30),
            )

            days_pattern = tsp_config["pattern"]
            run_spark_job = EmrAddStepsOperator(
                cluster_states=["RUNNING", "WAITING"],
                job_flow_id=job_flow_id,
                aws_conn_id=aws_conn_id,
                steps=[
                    {
                        "ActionOnFailure": "CONTINUE",
                        "HadoopJarStep": {
                            "Jar": "command-runner.jar",
                            "Args": [
                                "spark-submit",
                                "--deploy-mode",
                                "cluster",
                                "--master",
                                "yarn",
                                "--driver-memory",
                                "{{ json.loads(ti.xcom_pull(task_ids='compute_emr_cluster_parameters'))['spark_memory'] }}g",
                                "--executor-memory",
                                "{{ json.loads(ti.xcom_pull(task_ids='compute_emr_cluster_parameters'))['spark_memory'] }}g",
                                "--conf",
                                "spark.yarn.submit.waitAppCompletion=true",
                                "--conf",
                                "spark.sql.shuffle.partitions=16",
                                f"{artifacts_bucket}/spark/tsp_dataset/tsp_dataset.py",
                                "--date",
                                ds,
                                "--date-range",
                                "{{ json.dumps(dag_run.conf.get('date_range') or []) }}",
                                "--pattern",
                                *[str(d) for d in days_pattern],
                                "--input-bucket-trip-data",
                                input_bucket_trip_data,
                                "--input-bucket-trip-log",
                                input_bucket_trip_log,
                                "--input-bucket-opticom-log",
                                input_bucket_opticom_log,
                                "--input-bucket-device-config",
                                input_bucket_device_config,
                                "--input-bucket-intersection-status-report",
                                input_bucket_intersection_status_report,
                                "--output-bucket",
                                output_bucket,
                                "--agency",
                                agency,
                                "--local-timezone",
                                local_timezone,
                            ],
                        },
                        "Name": f"TSP dataset Spark job ({agency})",
                    }
                ],
                task_id="run_spark_job",
                execution_timeout=timedelta(minutes=30),
            )

            wait_for_job_completion = EmrStepSensor(
                job_flow_id=job_flow_id,
                aws_conn_id=aws_conn_id,
                step_id="{{ ti.xcom_pull(task_ids='run_spark_job')[0] }}",
                task_id="wait_for_job_completion",
                execution_timeout=timedelta(hours=2),
            )

            terminate_emr_cluster = EmrTerminateJobFlowOperator(
                task_id="terminate_emr_cluster",
                aws_conn_id=aws_conn_id,
                job_flow_id=job_flow_id,
                trigger_rule="all_done",
                execution_timeout=timedelta(minutes=30),
            )

            trigger_dags = [
                TriggerDagRunOperator(
                    task_id=f"trigger_dag_{dag_id}-{agency}",
                    trigger_dag_id=f"{dag_id}-{agency}",
                    conf={
                        "date_range": '{{ dag_run.conf.get("date_range") }}',
                        "spark_memory": '{{ json.loads(ti.xcom_pull(task_ids="compute_emr_cluster_parameters"))["spark_memory"] // %d }}g'
                        % len(external_dag_ids),
                    },
                    execution_date="{{ ts }}",
                    reset_dag_run=True,
                    wait_for_completion=True,
                    execution_timeout=timedelta(hours=2),
                )
                for dag_id in external_dag_ids
            ]

            run_tsp_dataset_crawler = AwsGlueCrawlerOperator(
                task_id="run_tsp_dataset_crawler",
                aws_conn_id=aws_conn_id,
                config={"Name": f"client_api-tsp-{env}"},
                execution_timeout=timedelta(minutes=30),
            )

            run_tsp_metrics_crawler = AwsGlueCrawlerOperator(
                task_id="run_tsp_metrics_crawler",
                aws_conn_id=aws_conn_id,
                config={"Name": f"client_api-tsp_metrics-{env}"},
                execution_timeout=timedelta(minutes=30),
            )

            (
                check_prefixes
                >> compute_emr_cluster_parameters
                >> create_emr_cluster
                >> wait_for_cluster
                >> run_spark_job
                >> wait_for_job_completion
            )

            wait_for_job_completion >> run_tsp_dataset_crawler

            (
                wait_for_job_completion
                >> trigger_dags
                >> terminate_emr_cluster
                >> run_tsp_metrics_crawler
            )

            format_dates = PythonOperator(
                task_id="parse_dates",
                python_callable=parse_dates,
                op_kwargs={
                    "date_range": "{{ dag_run.conf.get('date_range') }}",
                    "date_pattern": "{{ date_pattern(ds, %s) }}" % days_pattern,
                },
            )

            redshift_conn_id = (
                f"redshift_{agency}"
                if check_connection(f"redshift_{agency}")
                else "redshift_default"
            )
            dwh_service = CvpDwhService(
                conn_id=redshift_conn_id,
                agency=agency,
                partitions={
                    "agency": [agency],
                    "date": "{{ ti.xcom_pull(task_ids='parse_dates') }}",
                },
            )

            (
                run_tsp_metrics_crawler
                >> format_dates
                >> dwh_service.prepare()
                >> dwh_service.sync_tables(
                    tables=map(lambda x: format_dict_values(x, env=env), CVP_TABLES)
                )
                >> dwh_service.load_travel_time()
            )

            return dag_id, dag

    def compute_emr_cluster_parameters(self, agency, job_flow_overrides):
        # See https://aws.amazon.com/ec2/instance-types/
        job_flow_overrides = job_flow_overrides or {}
        instance_memory = job_flow_overrides.pop("instance_memory", 16)
        job_flow_overrides["Tags"] = [{"Key": "agency", "Value": agency}]
        return json.dumps(
            {
                "job_flow_overrides": job_flow_overrides,
                "spark_memory": int(instance_memory * 0.6),
            }
        )


for dag_id, dag in get_dags_to_load(TspDatasetFactory()):
    globals()[dag_id] = dag
