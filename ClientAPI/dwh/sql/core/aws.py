import json
import logging
from typing import Dict

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor


class AWSSecretsManager:
    """
    Manage AWS Secrets Manager secrets
    """

    def __init__(self, region_name: str):
        session = boto3.session.Session()
        self.secretsmanager_client = session.client(
            service_name="secretsmanager", region_name=region_name
        )

    def load_secret(self, secret_arn: str) -> Dict[str, str]:
        """
        Load a secret's content
        """
        secret = self.secretsmanager_client.get_secret_value(SecretId=secret_arn)
        return json.loads(secret["SecretString"])


class AWSRedshift:
    """
    Manage Redshif connecion lifecyle
    """

    def __init__(self, connection: Dict[str, str]):
        self.client = psycopg2.connect(
            dbname=connection["dbname"],
            host=connection["host"],
            port=connection["port"],
            user=connection["username"],
            password=connection["password"],
        )
        self.client.autocommit = True

    def execute(self, sql, sql_kwargs: Dict[str, str] = None) -> None:
        """
        Execute a single SQL statement, substituting the passed-in keyword arguments
        interpreted as literal values in the SQL scripts, templated as '{KWARG}'
        """
        if sql_kwargs is None:
            sql_kwargs = {}

        with self.client.cursor(cursor_factory=RealDictCursor) as cursor:
            try:
                # Attempt to parse as template
                sql = sql.format(
                    # Empty object literal {} != positional argument
                    "{}",
                    # Allow format strings of the format '{ key }'
                    **{**sql_kwargs, **{f" {k} ": v for k, v in sql_kwargs.items()}},
                )
            except Exception as exception:
                logging.error(exception)

            cursor.execute(sql)

            if cursor.pgresult_ptr is None:
                return None

            response = cursor.fetchall()
            return json.loads(json.dumps(response, default=str))

    def rollback(self) -> None:
        """
        Rollback connection state
        """
        with self.client.cursor() as cursor:
            cursor.execute("ROLLBACK")
