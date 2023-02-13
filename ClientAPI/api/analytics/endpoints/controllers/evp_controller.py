from models.response import Response
from utils.sql_builder import SqlParser


class EvpController:
    """
    /evp/{endpoint}
    """

    def __init__(self, postgres_service):
        self.postgres_service = postgres_service

    def route(self, event, context):
        endpoint = event["endpoint"]

        if endpoint == "report":
            return self.report(event, context)

        raise Exception(f"Unknown endpoint '{endpoint}'")

    def report(self, event, context):
        """
        POST /report
        """

        response = Response(event, context)

        # Signal delay
        signal_delay_by_intersection = self.postgres_service.execute(
            SqlParser.parse_template(
                "sql/evp/signal_delay_by_intersection.sql", **event
            )
        )

        # Drive time
        drive_time_by_segment = self.postgres_service.execute(
            SqlParser.parse_template("sql/evp/drive_time_by_segment.sql", **event)
        )

        # Travel time
        travel_time_by_date = []

        # Trip
        trips_by_date = self.postgres_service.execute(
            SqlParser.parse_template("sql/evp/trips_by_date.sql", **event)
        )

        # Segements
        segments = self.postgres_service.execute(
            SqlParser.parse_template("sql/evp/segments.sql", **event)
        )

        return response.prepare(
            {
                "input": event,
                "output": {
                    "signal_delay": {"by_intersection": signal_delay_by_intersection},
                    "drive_time": {"by_segment": drive_time_by_segment},
                    "segments": {"summary": segments},
                    "travel_time": {"by_date": travel_time_by_date},
                    "trips": {"by_date": trips_by_date},
                },
            }
        )
