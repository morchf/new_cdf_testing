"""
Manage DWH migrations
"""

import json
import logging
from argparse import ArgumentParser
from os import getenv, listdir

from core.aws import AWSRedshift, AWSSecretsManager
from core.dwh_manager import DwhManager

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger().setLevel(logging.INFO)


def main(test=False, path=None, sql=None, *args, **kwargs):
    """
    Run DWH migration, included scripts, or raw SQL

    Substitute the user password secret ARNs with the password value stored in Secrets Manager
    """

    secrets_client = AWSSecretsManager(region_name=getenv("AWS_REGION"))

    redshift_conection = secrets_client.load_secret(getenv("REDSHIFT_SECRET_ARN"))
    redshift_client = AWSRedshift(connection=redshift_conection)

    # Load SQL script arguments
    sql_kwargs = json.loads(getenv("SQL_SCRIPT_KWARGS"))

    # Load user passwords
    for key in ["API_USER_SECRET", "EVP_USER_SECRET"]:
        # Retrieve password from secret
        sql_kwargs[key] = secrets_client.load_secret(sql_kwargs[key])["password"]

    # Load database version
    sql_kwargs["DWH_VERSION"] = max(map(int, listdir("versions")))

    dwh_manager = DwhManager(postgres_client=redshift_client, sql_kwargs=sql_kwargs)

    # Run specific SQL script
    if path is not None:
        dwh_manager.execute_script(path)

    # Run passed-in SQL script
    if sql is not None:
        dwh_manager.execute(sql)

    # Run migration
    if path is None and sql is None:
        dwh_manager.migrate_dwh()

    # Run test suite
    if test:
        dwh_manager.test()


def handler(event=None, *args):
    """
    Lambda handler
    """

    if event is None:
        event = {}

    main(**event)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Migrate DWH using current scripts and current DWH version"
    )
    parser.add_argument(
        "-t", "--test", action="store_true", help="Run tests after migration"
    )
    parser.add_argument("-p", "--path", type=str, help="Run a specific script")
    parser.add_argument("-s", "--sql", type=str, help="Run a SQL command")
    args = parser.parse_args()

    main(**vars(args))
