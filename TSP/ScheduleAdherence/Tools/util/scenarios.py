import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from gtt.data_model.schedule_adherence import (
    StaticGtfsStop,
    StaticGtfsStopTime,
    VehiclePosition,
)


class ScenarioDefinition(BaseModel):
    agency_id: str
    date: str
    vehicle_positions: List[VehiclePosition]

    # Static GTFS
    stops: Optional[List[StaticGtfsStop]] = Field(default_factory=list)
    stop_times: Optional[List[StaticGtfsStopTime]] = Field(default_factory=list)


class Scenario:
    def __init__(self, scenario_definition: ScenarioDefinition):
        self._scenario_definition = scenario_definition

        trip_stop_times = {}
        for stop_time in self._scenario_definition.stop_times:
            curr_trip_stop_time = trip_stop_times.get(stop_time.trip_id)
            if curr_trip_stop_time is None:
                curr_trip_stop_time = []
                trip_stop_times[stop_time.trip_id] = []

            curr_trip_stop_time.append(stop_time)

        self._trip_stop_times = trip_stop_times

    @property
    def agency_id(self) -> str:
        return self._scenario_definition.agency_id

    @property
    def date(self) -> str:
        return self._scenario_definition.date

    @property
    def stops(self) -> List[StaticGtfsStop]:
        return self._scenario_definition.stops

    @property
    def trip_stop_times(self) -> str:
        return self._trip_stop_times

    @property
    def vehicle_ids(self) -> List[str]:
        return set(
            map(lambda x: x.vehicle_id, self._scenario_definition.vehicle_positions)
        )

    @property
    def trip_ids(self) -> List[str]:
        return set(self._trip_stop_times.keys())

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self._scenario_definition.vehicle_positions):
            vehicle_position = self._scenario_definition.vehicle_positions[self.n]
            self.n += 1

            return vehicle_position
        else:
            raise StopIteration


class LocalStaticGtfsService:
    def __init__(
        self,
        date: str,
        stops: List[StaticGtfsStop],
        trip_stop_times: Dict[str, List[StaticGtfsStopTime]],
    ):
        self._date = date
        self._stops = stops
        self._trip_stop_times = trip_stop_times

    def get_date(self, *args, **kwargs):
        return self._date

    def get_stop_times(self, trip_id, *args, **kwargs):
        stop_times = self._trip_stop_times.get(trip_id, [])
        return [
            StaticGtfsStopTime(
                **stop_time.dict(exclude={"stop"}),
                stop=next(
                    filter(lambda x: x.stop_id == stop_time.stop_id, self._stops),
                    None,
                )
            )
            for stop_time in stop_times
        ]


def from_breadcrumbs(
    trip_id: str, vehicle_id: str, breadcrumbs: List[Tuple[str, float, float]]
) -> List[VehiclePosition]:
    return [
        {
            "trip_id": trip_id,
            "vehicle_id": vehicle_id,
            "timestamp": timestamp,
            "latitude": latitude,
            "longitude": longitude,
        }
        for [timestamp, latitude, longitude] in breadcrumbs
    ]


def from_file(trip_id: str, vehicle_id: str, file_path: str) -> List[VehiclePosition]:
    with open(file_path, "r") as f:
        reader = csv.reader(f, delimiter=",")
        return list(
            sorted(
                [
                    {
                        "trip_id": trip_id,
                        "vehicle_id": vehicle_id,
                        "timestamp": timestamp,
                        "latitude": latitude,
                        "longitude": longitude,
                    }
                    for [timestamp, latitude, longitude] in reader
                ],
                key=lambda x: datetime.strptime(
                    x["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
                ).timestamp(),
            )
        )
