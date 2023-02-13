from datetime import datetime
from typing import Any, Literal, Optional

from gtt.api import HttpRequest
from pydantic import BaseModel, Field


class UploadIntersectionsRequest(HttpRequest):
    class QueryParameters(BaseModel):
        agency_name: str = Field(alias="agencyName")
        region_name: str = Field(alias="regionName")
        utc_date: Optional[datetime] = Field(
            alias="utcDate", default_factory=datetime.utcnow
        )

    http_method: Literal["POST"]
    query_parameters: QueryParameters
    body: Any
