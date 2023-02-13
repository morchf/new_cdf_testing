import time
import logging

from datetime import datetime, timedelta
from typing import Dict, Tuple, Union


import boto3
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import BranchPythonOperator, PythonOperator

logging.basicConfig(format="%(asctime)s %(message)s:", datefmt="%m/%d/%Y %I:%M:%S %p")


class DataPipelineFactory:
    """
    Factory to create DAGs for scheduling Data Pipeline jobs

    See: https://github.com/gtt/automation_production_code/blob/master/central_repo/cvp-etl-pipeline.py
    See: https://github.com/gtt/automation_production_code/blob/master/central_repo/cms-etl-pipeline.py
    """

    @staticmethod
    def get_name() -> str:
        return "data-pipeline"

    def run_task(self, config, date):
        MAX_RETRIES = 3
        current_retries = 0
        ssm_client = boto3.client("ssm", region_name=config["instance_region"])

        instance_state = self.get_instance_state(config)

        # Wait for the instance to finish startup before running the command
        while instance_state != "running":
            logging.info(
                "Instance state is "
                + instance_state
                + ", expected 'running'. Waiting to start command"
            )

            time.sleep(10)
            instance_state = self.get_instance_state(config)

        # Sleep before running the command
        # Should not be needed because of above loop, but without this it throws an InvalidInstanceId exception
        time.sleep(30)

        while current_retries <= MAX_RETRIES:

            logging.info("Starting command")
            cmd_response = self.run_ec2_cmd(config, date)

            # Wait for the command to run before polling/retrying.
            time.sleep(60)

            cmd_id = cmd_response["Command"]["CommandId"]
            instance_id = cmd_response["Command"]["InstanceIds"][0]

            cmd_response = ssm_client.get_command_invocation(
                CommandId=cmd_id, InstanceId=instance_id
            )
            cmd_status = cmd_response["Status"]

            # If the command is still running, wait 30 seconds and re-poll
            if cmd_status == "InProgress":
                while cmd_status == "InProgress":
                    logging.info("Command in progress, waiting to finish")
                    time.sleep(30)
                    cmd_response = ssm_client.get_command_invocation(
                        CommandId=cmd_id, InstanceId=instance_id
                    )
                    cmd_status = cmd_response["Status"]

            if cmd_status == "Success":
                logging.info("Command finished successfully")
                return "end_task"
            else:
                logging.warning(
                    "Command status was "
                    + cmd_status
                    + ", expected 'Success'. Retrying"
                )
                current_retries += 1

        logging.error("Command failed and exceeded retry limit")
        return "notify_task"

    # Notify and end tasks not needed, used as placeholders for error/success notifications
    def notify_task(self, config):
        logging.error("Error in pipeline, error notification task reached")

    def end_task(self, config):
        logging.info("Finished")

    def start_ec2_instance(self, config):
        MAX_RETRIES = 5
        current_retries = 0
        started = False

        state_instance = self.get_instance_state(config)

        # If the instance is stopped, start it right away. Else, wait for it to be stopped
        # If the instance is not stopped within 15 minutes, fail the DAG
        while current_retries < MAX_RETRIES and not started:
            if state_instance == "stopped":
                logging.info("EC2 Instance was stopped - starting now")
                boto3.client(
                    "ec2", region_name=config["instance_region"]
                ).start_instances(InstanceIds=[config["deploy_instance"]])
                started = True
            else:
                logging.warning(
                    "EC2 Instance state was "
                    + state_instance
                    + " - expected 'stopped'. Can't start instance. Trying again in 3 minutes"
                )
                current_retries += 1
                time.sleep(180)
                state_instance = self.get_instance_state(config)

        if not started:
            logging.error(
                "EC2 Instance could not be started - was not stopped before running"
            )
            raise Exception("Failed to start EC2 Instance. Failing DAG")

    def run_ec2_cmd(self, config, date):
        ssm_client = boto3.client("ssm", region_name=config["instance_region"])

        comnd_own = config["comnd_own"]
        git_repo = config["git_repo"]
        git_path = config["git_path"]
        etl_params = config["etl_parameters"]
        script_path = git_path[git_path.rfind("/") + 1 :]

        work_dirs = "/home/" + comnd_own + "/" + git_repo

        main_command = (
            f" mkdir -m 777 -p {work_dirs} && chown ubuntu {work_dirs} && cd {work_dirs} && "
            + f" chmod 777 * && sudo -u {comnd_own} /usr/bin/python3 {script_path} {etl_params} {date} && "
            + " sleep 30 && sudo shutdown -h 2 ||  ( sudo shutdown -h 2 && exit 1 ) "
        )

        print(main_command)

        response = ssm_client.send_command(
            DocumentName="AWS-RunRemoteScript",
            TimeoutSeconds=172800,
            Parameters={
                "sourceType": ["GitHub"],
                "sourceInfo": [
                    '{"owner":"'
                    + config["git_owner"]
                    + '", "repository": "'
                    + config["git_repo"]
                    + '","getOptions":"branch:'
                    + config["git_branch"]
                    + '","path": "'
                    + config["git_path"]
                    + '", "tokenInfo":"{{ssm-secure:'
                    + config["git_token"]
                    + '}}"}'
                ],
                "commandLine": [main_command],
                "workingDirectory": [work_dirs + "/"],
            },
            InstanceIds=[config["deploy_instance"]],
            ServiceRoleArn=config["role_arn"],
            NotificationConfig={
                "NotificationArn": config["sns_notify"],
                "NotificationEvents": ["Failed"],
            },
            CloudWatchOutputConfig={
                "CloudWatchLogGroupName": config["cloud_watch"],
                "CloudWatchOutputEnabled": True,
            },
        )

        return response

    def get_instance_state(self, config):
        ec2_client = boto3.resource("ec2", region_name=config["instance_region"])

        inst_states = []

        for instance in ec2_client.instances.all():
            inst_states.append([instance.id, instance.state["Name"]])

        state_instance = [x for x in inst_states if x[0] == config["deploy_instance"]][
            0
        ][1]

        return state_instance

    def __call__(
        self,
        agency: str,
        source: str,
        schedule_interval: str,
        temp_arn: str,
        config: Dict[str, Union[str, int]],
        *args,
        **kwargs,
    ) -> Tuple[str, DAG]:
        dag_id = f"{self.get_name()}-{agency}-{source}"
        with DAG(
            catchup=False,
            dag_id=dag_id,
            default_args={"depends_on_past": False},
            description=f"Schedule Data Pipeline job ({agency})",
            schedule_interval=schedule_interval,
            start_date=datetime(2018, 5, 2),
            tags=[self.get_name(), agency, source],
        ) as dag:

            start_ec2 = PythonOperator(
                op_kwargs={"config": config},
                python_callable=self.start_ec2_instance,
                task_id="start_ec2_instance",
            )

            run_task = BranchPythonOperator(
                op_kwargs={"config": config, "date": "{{ ds }}"},
                python_callable=self.run_task,
                task_id="run_task",
                execution_timeout=timedelta(minutes=20),
            )

            end_task = PythonOperator(
                op_kwargs={"config": config},
                python_callable=self.end_task,
                task_id="end_task",
            )

            notify_task = PythonOperator(
                op_kwargs={"config": config},
                python_callable=self.notify_task,
                task_id="notify_task",
            )

            (start_ec2 >> run_task >> [end_task, notify_task])

            return dag_id, dag


factory = DataPipelineFactory()

"""
Variables

data_pipelines: [
                    { "agency": "agency_name", "source": "cvp", "config": { ... } }
                    ...
                ]
"""
agency_configs = Variable.get("data_pipelines", deserialize_json=True)


for agency_config in agency_configs:
    dag_id, dag = factory(**agency_config)
    globals()[dag_id] = dag
