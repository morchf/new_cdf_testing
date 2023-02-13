import json
from time import time
import logging
from typing import List, Union

import boto3
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor


class PostgresService:
    def __init__(self, secret_arn):
        if not secret_arn:
            return

        # Retrieve secrets
        session = boto3.session.Session()
        region_name = session.region_name

        secmgr = session.client(service_name="secretsmanager", region_name=region_name)
        secret = secmgr.get_secret_value(SecretId=secret_arn)
        secret_string = json.loads(secret["SecretString"])

        self.redshift = psycopg2.connect(
            dbname=secret_string["dbname"],
            host=secret_string["host"],
            port=secret_string["port"],
            user=secret_string["username"],
            password=secret_string["password"],
        )

    def call_procedure(self, signature, **kwargs):
        cursor_suffix = repr(time()).replace(".", "")
        cursor_name = f"cursor_{cursor_suffix}"

        try:
            with self.redshift.cursor(cursor_factory=RealDictCursor) as cursor:
                # Call stored procedure and return results using cursor
                cursor.autocommit = 1

                cursor.execute(
                    f"CALL {signature};",
                    {**kwargs, "cursor": cursor_name},
                )

                cursor.execute(f"FETCH ALL FROM {cursor_name};")
                response = cursor.fetchall()
                cursor.execute(f"CLOSE {cursor_name};")

                return json.loads(json.dumps(response, default=str))
        except Exception as e:
            logging.exception(e)
            self.redshift.rollback()

    def execute(
        self, query: Union[str, sql.SQL], args: List[Union[str, sql.SQL]] = None
    ):
        try:
            with self.redshift.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, args)
                response = cursor.fetchall()
                return json.loads(json.dumps(response, default=str))
        except Exception as e:
            logging.exception(e)
            self.redshift.rollback()
