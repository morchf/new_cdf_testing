import csv
import io
from os import getenv

import shapely.wkb
from models.response import Response
from services.postgres import PostgresService
from shapely.geometry import Point
from utils.direction import from_direction, from_direction_id
from utils.sql_builder import SqlParser

secret_arn = getenv("REDSHIFT_SECRET_ARN")
postgres_service = PostgresService(secret_arn=secret_arn)


def handler(event, context):
    response = Response(event, context)

    timeframe = postgres_service.call_procedure(
        """sp_routes_availability_period(
            %(agency)s::VARCHAR,
            %(start_date)s::DATE,
            %(end_date)s::DATE,
            %(cursor)s
        )""",
        **event,
    )

    if not timeframe:
        return response.prepare([])

    query_results = postgres_service.execute(
        SqlParser.parse_template(
            "sql/gtfs/stops.sql",
            **{**event, **timeframe[0]},  # Override start/end dates
            direction_ids=list(map(from_direction, event["selected_direction"])),
        )
    )

    output = {}
    for row in query_results:
        key = (row["shape_id"], row["direction_id"])
        if key in output:
            continue

        direction_id = row["direction_id"]
        direction = from_direction_id(direction_id)

        line = shapely.wkb.loads(row["line"], hex=True)

        points = [
            {
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "progress": round(line.project(Point(lon, lat)), 5),
            }
            for i, (lon, lat) in enumerate(line.coords)
        ]
        stops = [
            {
                "label": x["label"].strip(),
                "lat": round(float(x["lat"].strip()), 5),
                "lon": round(float(x["lon"].strip()), 5),
                "progress": round(
                    float(line.project(Point(float(x["lon"]), float(x["lat"])))), 5
                ),
                "order": int(x["order"].strip()),
                "stopid": x["stopid"].strip(),
            }
            for x in sorted(
                csv.DictReader(
                    io.StringIO("\n".join(row["stops"].strip("[]").split("],["))),
                    fieldnames=["order", "label", "lat", "lon", "stopid"],
                ),
                key=lambda x: int(x["order"]),
            )
        ]

        points_and_stops = sorted([*points, *stops], key=lambda x: float(x["progress"]))
        stops_indexes = [i for i, x in enumerate(points_and_stops) if "label" in x]
        segments = [
            {
                "points": points_and_stops[
                    stop_start
                    if i != 1
                    else 0 : stop_end + 1
                    if i != len(points_and_stops)
                    else i
                ],
                "stopendname": points_and_stops[stop_end]["label"],
                "stopendorder": points_and_stops[stop_end]["order"],
                "stopendlat": points_and_stops[stop_end]["lat"],
                "stopendlon": points_and_stops[stop_end]["lon"],
                "stopendid": points_and_stops[stop_end]["stopid"],
                "stopstartname": points_and_stops[stop_start]["label"],
                "stopstartid": points_and_stops[stop_start]["stopid"],
                "stopstartorder": points_and_stops[stop_start]["order"],
                "stopstartlat": points_and_stops[stop_start]["lat"],
                "stopstartlon": points_and_stops[stop_start]["lon"],
                "direction": direction,
            }
            for i, (stop_start, stop_end) in enumerate(
                zip(stops_indexes, stops_indexes[1:]), 1
            )
        ]
        output[key] = {
            "date": row["date"],
            "segments": segments,
            "shape": row["shape_id"],
            "route": event["route"],
        }

    return response.prepare(
        # Sort by GTFS segment age
        sorted(
            output.values(),
            key=lambda x: -1 * int(x["shape"]),
        )
    )
