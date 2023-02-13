from typing import Dict

from airflow.providers.amazon.aws.operators.athena import AWSAthenaOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator


class PostgresService:
    """
    Send SQL commands and run procedures
    """

    TASK_ID = "postgres"

    def __init__(self, conn_id: str):
        self.conn_id = conn_id

    def execute(self, sql: str, task_id: str, **kwargs):
        """
        Execute a SQL script
        """
        return PostgresOperator(
            postgres_conn_id=self.conn_id,
            task_id=f"{PostgresService.TASK_ID}__{task_id}",
            sql=sql,
            **kwargs,
        )

    def call_procedure(
        self,
        procedure_name: str,
        task_id: str = None,
        procedure_args: str = None,
        params: Dict[str, str] = {},
        **kwargs,
    ):
        """
        Run a stored procedure with the given arguments
        """
        return PostgresOperator(
            postgres_conn_id=self.conn_id,
            task_id=f"{PostgresService.TASK_ID}__{task_id if task_id else procedure_name}",
            sql=f"CALL {procedure_name}{procedure_args if procedure_args else '()'}",
            params=params,
            **kwargs,
        )


class AthenaService:
    """
    Send SQL commands to Athena
    """

    TASK_ID = "athena"

    def __init__(self, output_location: str, workgroup: str = "primary"):
        self._output_location = output_location
        self._workgroup = workgroup

    def execute(self, task_id, **kwargs):
        return AWSAthenaOperator(
            task_id=f"{AthenaService.TASK_ID}__{task_id}",
            output_location=self._output_location,
            workgroup=self._workgroup,
            **kwargs,
        )
