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

    lag_partition = [
        "stopstartname",
        "stopendname",
        "direction",
    ]
    on_time_lower, on_time_upper = event["on_time_range"]
    query = SqlParser.parse_template(
        "athena/agg_lateness_per_route.sql",
        **event,
        # Filter
        f_timeperiod=F.f_timeperiod(event["timeperiod"], "stopstarttime"),
        # Percentage
        f_percentage__early=F.f_percentage(on_time_upper=on_time_upper),
        f_percentage__on_time=F.f_percentage(
            on_time_lower=on_time_lower, on_time_upper=on_time_upper
        ),
        f_percentage__late=F.f_percentage(on_time_lower=on_time_lower),
        # Lag
        f_lag__start_lateness=F.f_lag("stopstartlateness", lag_partition),
        f_lag__end_lateness=F.f_lag("stopendlateness", lag_partition),
        f_lag__lateness_reduction=F.f_lag("latenessreduction", lag_partition),
        f_lag__early=F.f_lag("earlypercentage", lag_partition),
        f_lag__on_time=F.f_lag("ontimepercentage", lag_partition),
        f_lag__late=F.f_lag("latepercentage", lag_partition),
    )

    query_results = postgres_service.execute(query)

    # Missing data in current period
    if query_results is None or (
        not event["start_date"] in unique(query_results, "period")
    ):
        return response.prepare(query_results)

    for row in query_results:
        for field in ["stopstartlateness", "stopendlateness", "latenessreduction"]:
            row[field] = Datum.from_numeric(
                json.loads(row[field]), is_higher_better=field == "lateness_reduction"
            )

        for field in ["earlypercentage", "ontimepercentage", "latepercentage"]:
            row[field] = Datum.from_percent(
                json.loads(row[field]), is_higher_better=field == "ontimepercentage"
            )

    return response.prepare(query_results)
