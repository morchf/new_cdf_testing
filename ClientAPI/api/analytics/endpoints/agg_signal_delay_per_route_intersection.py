import json
from os import getenv

from models.response import Response
from services.postgres import PostgresService
from utils.datum import Datum
from utils.direction import from_direction
from utils.list import unique
from utils.sql_builder import SqlFunctions as F
from utils.sql_builder import SqlParser

secret_arn = getenv("REDSHIFT_SECRET_ARN")
postgres_service = PostgresService(secret_arn=secret_arn)


def handler(event, context):
    response = Response(event, context)

    query_results = postgres_service.execute(
        SqlParser.parse_template(
            "athena/agg_signal_delay_per_route_intersection.sql",
            **event,
            f_timeperiod=F.f_timeperiod(event["timeperiod"], '"timestamp"'),
            f_lag__signal_delay=F.f_lag("signaldelay", ["locationid"]),
            direction_ids=list(map(from_direction, event["selected_direction"])),
        )
    )

    # Missing data in current period
    if query_results is None or (
        not event["start_date"] in unique(query_results, "period")
    ):
        return response.prepare(query_results)

    for row in query_results:
        row["signaldelay"] = Datum.from_numeric(json.loads(row["signaldelay"]))

    return response.prepare(query_results)
