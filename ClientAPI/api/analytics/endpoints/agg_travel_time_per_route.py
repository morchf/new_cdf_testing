import json
from os import getenv

from models.response import Response
from services.postgres import PostgresService
from utils.datum import Datum
from utils.list import unique
from utils.sql_builder import SqlFunctions as F
from utils.sql_builder import SqlParser

secret_arn = getenv("REDSHIFT_SECRET_ARN")
postgres_service = PostgresService(secret_arn=secret_arn)


def handler(event, context):
    response = Response(event, context)

    lag_partition = ["stopstartname", "stopendname"]
    query = SqlParser.parse_template(
        "athena/agg_travel_time_per_route.sql",
        **event,
        # Filter
        f_timeperiod=F.f_timeperiod(event["timeperiod"], "tripstarttime"),
        # Lag
        f_lag__drivetime=F.f_lag("drivetime", lag_partition),
        f_lag__dwelltime=F.f_lag("dwelltime", lag_partition),
        f_lag__signaldelay=F.f_lag("signaldelay", lag_partition),
        f_lag__traveltime=F.f_lag("traveltime", lag_partition),
        f_lag__tspsavings=F.f_lag("tspsavings", lag_partition),
    )

    data = postgres_service.execute(query)

    # Missing data in current period
    if data is None or (not event["start_date"] in unique(data, "period")):
        return response.prepare(data)

    for row in data:
        for field in [
            "drivetime",
            "dwelltime",
            "signaldelay",
            "traveltime",
            "tspsavings",
        ]:
            row[field] = Datum.from_numeric(json.loads(row[field]))

    return data
