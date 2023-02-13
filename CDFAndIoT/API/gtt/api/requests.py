import json
import logging
from abc import ABC
from typing import Any, List, Optional, Type, Union

from pydantic import BaseModel, Field, create_model, root_validator, validator

from .methods import HttpMethod

"""
Event
"""


class BaseRequest(BaseModel, ABC):
    class Config:
        allow_population_by_field_name = True
        use_enum_values = True

    # @abstractmethod
    # def data(self):
    #     # Best way to type 'data' method/field?
    #     raise NotImplementedError()


class HttpRequest(BaseRequest):
    headers: Any = Field(alias="headers")
    body: Optional[Any] = Field(alias="body")
    query_parameters: Optional[Any] = Field(
        alias="queryStringParameters", default_factory=dict
    )
    path_parameters: Optional[Any] = Field(alias="pathParameters", default_factory=dict)

    # Under 'requestContext'
    request_context: Optional[Any] = Field(alias="requestContext", default_factory={})
    http_method: HttpMethod = Field(alias="httpMethod")
    path: Optional[str] = Field(alias="path")
    resource_path: Optional[str] = Field(alias="resourcePath")
    identity: Optional[Any] = Field(alias="identity")

    class Config:
        fields = {
            "http_method": {"alias": "httpMethod"},
            "query_parameters": {"alias": "queryStringParameters"},
            "path_parameters": {"alias": "pathParameters"},
        }
        allow_population_by_field_name = True

    data: Optional[Type[BaseModel]]

    def __init__(self, query_parameters={}, **kwargs):
        super().__init__(query_parameters=query_parameters, **kwargs)

        logging.debug(f"kwargs={query_parameters}")

        self.data = create_model("Data", **query_parameters)

    @root_validator(pre=True)
    def flatten_request(cls, values):
        logging.debug(f"flatten_request: {values=}")

        if ("requestContext" not in values) and ("request_context" not in values):
            raise ValueError("Missing key 'requestContext/request_context'")

        request_context = values.get("requestContext", values.get("request_context"))
        query_parameters = values.get(
            "queryStringParameters", values.get("query_parameters")
        )

        values.update(
            {
                **({} if request_context is None else {}),
                **({} if query_parameters is None else query_parameters),
            }
        )

        return values

    @validator("body")
    def parse_body_json(cls, v):
        """parse API Gateway body as json if possible, else leave it as is"""
        logging.debug(f"parse_body_json: {v=}")
        try:
            return json.loads(v)
        except (ValueError, TypeError):
            return v


class SnsRecord(BaseModel):
    message: str = Field(alias="Message")
    message_id: str = Field(alias="MessageId")


class SqsRecord(BaseModel):
    body: Any
    message_id: str = Field(alias="messageId")

    class Config:
        allow_population_by_field_name = True

    @validator("body", pre=True)
    def parse_body_json(cls, v):
        """parse SQS record body as JSON if possible, else leave it as is"""
        logging.debug(f"parse_body_json: {v=}")
        try:
            return json.loads(v)
        except (ValueError, TypeError):
            return v


class SnsRequest(BaseRequest):
    records: List[SnsRecord]

    class Config:
        fields = {"records": {"alias": "Records"}}


class SqsRequest(BaseRequest):
    records: List[SqsRecord]

    class Config:
        fields = {"records": {"alias": "Records"}}
        allow_population_by_field_name = True


class EventBridgeRequest(BaseRequest):
    version: str
    id: str
    detail_type: str = Field(alias="detail-type")
    source: str
    time: str
    region: str
    resources: List[str]
    detail: Any


# Helper type to parse requests
Request = Union[HttpRequest, SqsRequest, SnsRequest]

"""
Context
"""


class Context(BaseModel):
    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: str
    aws_request_id: str
    log_group_name: str
    log_stream_name: str
