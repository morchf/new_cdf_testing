from typing import Literal

from gtt.api import HttpRequest
from pydantic import BaseModel, Field

from gtt.data_model.schedule_adherence import VehiclePosition


class GetScheduleStatusHttpRequest(HttpRequest, allow_population_by_field_name=True):
    class QueryParameters(BaseModel):
        agency_id: str = Field(alias="agencyId")
        trip_id: str = Field(alias="tripId")
        vehicle_id: str = Field(alias="vehicleId")

    http_method: Literal["GET"]
    query_parameters: QueryParameters


class UpdateScheduleStatusHttpRequest(HttpRequest, allow_population_by_field_name=True):
    class QueryParameters(BaseModel):
        agency_id: str = Field(alias="agencyId")

    http_method: Literal["POST"]
    query_parameters: QueryParameters
    body: VehiclePosition
