from datetime import datetime, timedelta
from typing import Tuple

from airflow import DAG
from airflow.models import Variable
from airflow.providers.amazon.aws.operators.emr_add_steps import EmrAddStepsOperator
from airflow.providers.amazon.aws.sensors.emr_step import EmrStepSensor
from common.common import check_connection, date_pattern, date_range, on_failure
from common.init_dags import get_dags_to_load


class LatenessFactory:
    @staticmethod
    def get_name() -> str:
        return "metrics-lateness"

    def __call__(self, agency: str, *args, **kwargs) -> Tuple[str, DAG]:
        config = Variable.get(f"{agency}_config", deserialize_json=True)
        tsp_dataset_config = config.get("tsp-dataset")

        env = config["env"]
        tsp_dataset_pattern = tsp_dataset_config["pattern"]

        artifacts_bucket = f"s3://client-api-artifacts-{env}"
        input_bucket = f"s3a://client-api-etl-{env}"
        output_bucket = f"s3a://client-api-etl-{env}"

        dag_id = f"{self.get_name()}-{agency}"
        with DAG(
            catchup=False,
            dag_id=dag_id,
            default_args={"depends_on_past": False, "on_failure_callback": on_failure},
            description=f"Schedule `metrics/lateness` Spark job ({agency})",
            schedule_interval=None,
            start_date=datetime(2018, 5, 2),
            tags=[self.get_name(), agency],
            user_defined_macros={
                "date_pattern": date_pattern,
                "date_range": date_range,
            },
        ) as dag:
            aws_conn_id = (
                f"aws_{agency}" if check_connection(f"aws_{agency}") else "aws_default"
            )

            job_flow_id = f"{{{{ ti.xcom_pull(dag_id='tsp-dataset-{agency}', task_ids='create_emr_cluster') }}}}"
            run_metrics_lateness_spark_job = EmrAddStepsOperator(
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
                                "{{ dag_run.conf.get('spark_memory') or '1g' }}",
                                "--executor-memory",
                                "{{ dag_run.conf.get('spark_memory') or '1g' }}",
                                "--conf",
                                "spark.yarn.submit.waitAppCompletion=true",
                                f"{artifacts_bucket}/spark/metrics/lateness.py",
                                "--agency",
                                agency,
                                "--date",
                                "{{ date_range(dag_run.conf.get('date_range')) or date_pattern(ds, %s) }}"
                                % tsp_dataset_pattern,
                                "--input-bucket",
                                input_bucket,
                                "--output-bucket",
                                output_bucket,
                            ],
                        },
                        "Name": f"Run `metrics/lateness` Spark job ({agency})",
                    }
                ],
                task_id="run_metrics_lateness_spark_job",
                execution_timeout=timedelta(minutes=30),
            )

            wait_metrics_lateness_spark_job = EmrStepSensor(
                job_flow_id=job_flow_id,
                aws_conn_id=aws_conn_id,
                step_id="{{ ti.xcom_pull(task_ids='run_metrics_lateness_spark_job')[0] }}",
                task_id="wait_metrics_lateness_spark_job",
                execution_timeout=timedelta(hours=1),
            )

            (run_metrics_lateness_spark_job >> wait_metrics_lateness_spark_job)

            return dag_id, dag


for dag_id, dag in get_dags_to_load(LatenessFactory()):
    globals()[dag_id] = dag
