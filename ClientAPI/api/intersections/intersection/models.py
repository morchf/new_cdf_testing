from typing import Any, Dict, Literal

from gtt.api import HttpRequest
from pydantic import BaseModel, Field

BASIC_FIELDS = {
    "agency_id",
    "serial_number",
    "intersection_name",
    "intersection_id",
    "latitude",
    "longitude",
    "last_communicated",
    "make",
    "model",
    "timezone",
    "operation_mode",
    "status",
    "firmware_version",
    "is_configured",
    "unit_id",
}


class GetRequest(HttpRequest):
    class QueryParameters(BaseModel):
        agency_id: str = Field(alias="agencyId")

    class PathParameters(BaseModel):
        serial_number: str = Field(alias="serialNumber")

    http_method: Literal["GET"]
    query_parameters: QueryParameters
    path_parameters: PathParameters


class CreateRequest(HttpRequest):
    class QueryParameters(BaseModel):
        agency_id: str = Field(alias="agencyId")

    class PathParameters(BaseModel):
        serial_number: str = Field(alias="serialNumber")

    http_method: Literal["POST"]
    query_parameters: QueryParameters
    path_parameters: PathParameters
    body: Dict[str, Any]


class UpdateRequest(HttpRequest):
    class QueryParameters(BaseModel):
        agency_id: str = Field(alias="agencyId")

    class PathParameters(BaseModel):
        serial_number: str = Field(alias="serialNumber")

    http_method: Literal["PUT"]
    query_parameters: QueryParameters
    path_parameters: PathParameters
    body: Dict[str, Any]
