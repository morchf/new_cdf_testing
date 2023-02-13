from typing import Literal

from gtt.api import HttpRequest
from pydantic import BaseModel, Field


class InvalidateStaticGtfsHttpRequest(HttpRequest, allow_population_by_field_name=True):
    class QueryParameters(BaseModel):
        agency_id: str = Field(alias="agencyId")

    class PathParameters(BaseModel):
        endpoint: Literal["invalidate"]

    http_method: Literal["POST"]
    query_parameters: QueryParameters
    path_parameters: PathParameters


class InvalidateStaticGtfsEventRequest(BaseModel, allow_population_by_field_name=True):
    class Detail(BaseModel, allow_population_by_field_name=True):
        agency_id: str = Field(alias="agencyId")
        endpoint: Literal["invalidate"]

    detail: Detail
