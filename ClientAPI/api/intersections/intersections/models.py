from typing import Any, Dict, Literal

from gtt.api import HttpRequest
from pydantic import BaseModel, Field

BASIC_FIELDS = {
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
    "mac_address",
}


class GetRequest(HttpRequest):
    class QueryParameters(BaseModel):
        agency_id: str = Field(alias="agencyId")

    http_method: Literal["GET"]
    query_parameters: QueryParameters


class CreateRequest(HttpRequest):
    class QueryParameters(BaseModel):
        agency_id: str = Field(alias="agencyId")

    http_method: Literal["POST"]
    query_parameters: QueryParameters
    body: Dict[str, Any]
