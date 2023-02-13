from os import getenv

from models.response import Response
from services.postgres import PostgresService
from utils.sql_builder import SqlParser

secret_arn = getenv("REDSHIFT_SECRET_ARN")
postgres_service = PostgresService(secret_arn=secret_arn)


def handler(event, context):
    response = Response(event, context)

    query = SqlParser.parse_template("sql/meta/status.sql", **event)

    availability = postgres_service.execute(query)

    if not availability or not len(availability) == 1:
        return response.prepare(
            {
                "availability": {
                    "schedule_deviation": {},
                    "travel_time": {},
                }
            }
        )

    return response.prepare(
        {
            "availability": {
                "schedule_deviation": {
                    "min": availability[0]["schedule_deviation_min"],
                    "max": availability[0]["schedule_deviation_max"],
                },
                "travel_time": {
                    "min": availability[0]["travel_time_min"],
                    "max": availability[0]["travel_time_max"],
                },
            }
        }
    )
