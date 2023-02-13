from os import getenv

from models.response import Response
from services.postgres import PostgresService
from utils.sql_builder import SqlFunctions as F
from utils.sql_builder import SqlParser

secret_arn = getenv("REDSHIFT_SECRET_ARN")
postgres_service = PostgresService(secret_arn=secret_arn)


def handler(event, context):
    response = Response(event, context)

    query = SqlParser.parse_template(
        "athena/agg_travel_time_per_route_day.sql",
        **event,
        # Filter
        f_timeperiod=F.f_timeperiod(event["timeperiod"], "tripstarttime"),
    )

    data = postgres_service.execute(query)

    if data is None:
        return response.prepare(data)

    for row in data:
        for field in [
            "drivetime",
            "dwelltime",
            "traveltime",
            "signaldelay",
            "tspsavings",
        ]:
            row[field] = {"secs": round(row[field], 3) if row[field] else None}

    return response.prepare(data)
