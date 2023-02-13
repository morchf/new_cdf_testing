from os import getenv

from models.response import Response
from services.postgres import PostgresService
from utils.metric import Metric
from utils.sql_builder import SqlFunctions as F
from utils.sql_builder import SqlParser

secret_arn = getenv("REDSHIFT_SECRET_ARN")
postgres_service = PostgresService(secret_arn=secret_arn)


def handler(event, context):
    response = Response(event, context)

    on_time_lower, on_time_upper = event["on_time_range"]
    query = SqlParser.parse_template(
        "athena/agg_lateness_reduction.sql",
        **event,
        f_timeperiod=F.f_timeperiod(event["timeperiod"], "stopstarttime"),
        f_percentage__early=F.f_percentage(on_time_upper=on_time_upper),
        f_percentage__on_time=F.f_percentage(
            on_time_lower=on_time_lower, on_time_upper=on_time_upper
        ),
        f_percentage__late=F.f_percentage(on_time_lower=on_time_lower),
    )

    data = postgres_service.execute(query)

    if data is None:
        return response.prepare(data)

    return response.prepare(Metric.map_fields(data))
