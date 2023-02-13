from os import getenv

from models.response import Response
from services.postgres import PostgresService
from utils.direction import from_direction, from_direction_id
from utils.sql_builder import SqlParser

secret_arn = getenv("REDSHIFT_SECRET_ARN")
postgres_service = PostgresService(secret_arn=secret_arn)


def handler(event, context):
    response = Response(event, context)

    intersection_date = next(
        iter(
            postgres_service.execute(
                SqlParser.parse_template(
                    "sql/tsp/intersection_date.sql",
                    **event,
                    direction_ids=list(
                        map(from_direction, event["selected_direction"])
                    ),
                )
            )
            or []
        ),
        {},
    ).get("date")

    if intersection_date is None:
        return response.prepare([])

    query_results = postgres_service.execute(
        SqlParser.parse_template(
            "sql/tsp/intersections.sql",
            **event,
            date=intersection_date,
            direction_ids=list(map(from_direction, event["selected_direction"])),
        )
    )

    if len(query_results) == 0:
        return response.prepare([])

    output = {}
    for row in query_results:
        key = (row["route_id"], row["route"], row["trip_direction_id"])
        if key not in output:
            output[key] = {
                "route_id": row["route_id"].strip(),
                "route": row["route"],
                "direction": from_direction_id(row["trip_direction_id"]),
                "intersections": [
                    {
                        "device_id": row["device_id"],
                        "location_id": row["location_id"],
                        "location_name": row["location_name"],
                        "latitude": round(float(row["latitude"]), 5),
                        "longitude": round(float(row["longitude"]), 5),
                    }
                ],
            }
        else:
            output[key]["intersections"].append(
                {
                    "device_id": row["device_id"],
                    "location_id": row["location_id"],
                    "location_name": row["location_name"],
                    "latitude": round(float(row["latitude"]), 5),
                    "longitude": round(float(row["longitude"]), 5),
                }
            )

    return response.prepare(list(output.values()))
