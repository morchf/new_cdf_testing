import uuid
from typing import List, Literal, Union

from gtt.api.requests import HttpRequest, Request, SqsRecord, SqsRequest
from pydantic import BaseModel, Field, parse_obj_as


class TestRequests:
    def test__http_request(self):
        class FeaturePersistenceRequest(HttpRequest):
            class QueryParameters(BaseModel):
                feature_name: str = Field(alias="FeatureName")

            class Body(BaseModel):
                agency_id: Union[str, uuid.UUID]

            http_method: Literal["POST"]
            query_parameters: QueryParameters
            body: Body

        event = {
            "requestContext": {"httpMethod": "POST"},
            "queryStringParameters": {"FeatureName": "gtfs-realtime-api"},
            "body": {"agency_id": "test"},
        }

        http_request = HttpRequest(**event)

        request = FeaturePersistenceRequest(**http_request.dict())

        assert request.http_method == "POST"
        assert request.query_parameters.feature_name == "gtfs-realtime-api"
        assert request.body.agency_id == "test"

    def test__http_request__get(self):
        class FeaturePersistenceRequest(HttpRequest):
            class QueryParameters(BaseModel):
                feature_name: str = Field(alias="FeatureName")

            http_method: Literal["GET"]
            query_parameters: QueryParameters

        event = {
            "requestContext": {"httpMethod": "GET"},
            "queryStringParameters": {"FeatureName": "gtfs-realtime-api"},
        }

        http_request = HttpRequest(**event)

        request = FeaturePersistenceRequest(**http_request.dict())

        assert request.http_method == "GET"
        assert request.query_parameters.feature_name == "gtfs-realtime-api"
        assert request.body is None

    def test__sqs(self):
        class FeaturePersistenceRecord(SqsRecord):
            class Body(BaseModel):
                test: str

            body: Body

        class FeaturePersistenceBatchRequest(SqsRequest):
            records: List[FeaturePersistenceRecord]

        body = {
            "attributes": {
                "ApproximateFirstReceiveTimestamp": "1530576251596",
                "ApproximateReceiveCount": "1",
                "SenderId": "sender-id",
                "SentTimestamp": "1530576251595",
            },
            "awsRegion": "us-west-2",
            "body": '{"test":"this"}',
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-west-2:12345:queue-name",
            "md5OfBody": "1223123102319203819230821",
            "messageAttributes": {},
            "messageId": "message-id",
            "receiptHandle": "receipt-handle",
        }
        event = {"Records": [body]}

        sqs_request = SqsRequest(**event)
        request = FeaturePersistenceBatchRequest(**sqs_request.dict())

        assert len(request.records) == 1
        assert request.records[0].body.test == "this"

    def test__multi_source(self):
        # HTTP

        class SingleRequest(HttpRequest):
            class QueryParameters(BaseModel):
                test2: str

            class Body(BaseModel):
                test: str

            http_method: Literal["POST"]
            query_parameters: QueryParameters
            body: Body

        http_event = {
            "requestContext": {"httpMethod": "POST"},
            "queryStringParameters": {"test2": "this2"},
            "body": {"test": "this"},
        }

        # SQS

        class BatchRequest(SqsRequest):
            class Record(SqsRecord):
                class Body(BaseModel):
                    test: str
                    test2: str

                body: Body

            records: List[Record]

        sqs_event = {
            "Records": [
                {
                    "attributes": {
                        "ApproximateFirstReceiveTimestamp": "1530576251596",
                        "ApproximateReceiveCount": "1",
                        "SenderId": "sender-id",
                        "SentTimestamp": "1530576251595",
                    },
                    "awsRegion": "us-west-2",
                    "body": '{"test":"this","test2":"this2"}',
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-west-2:12345:queue-name",
                    "md5OfBody": "1223123102319203819230821",
                    "messageAttributes": {},
                    "messageId": "message-id",
                    "receiptHandle": "receipt-handle",
                }
            ]
        }

        # Test

        request = parse_obj_as(Request, sqs_event)

        # Can parse either way
        parse_obj_as(Union[SingleRequest, BatchRequest], request)
        event = parse_obj_as(Union[SingleRequest, BatchRequest], sqs_event)

        assert type(event) == BatchRequest
        assert len(event.records) == 1
        assert event.records[0].body.test == "this"
        assert event.records[0].body.test2 == "this2"

        request = parse_obj_as(Request, http_event)
        event = parse_obj_as(Union[SingleRequest, BatchRequest], request)

        assert type(event) == SingleRequest
        assert event.body.test == "this"
        assert event.query_parameters.test2 == "this2"

    def test__http_request_context(self):
        class SpecificRequest(HttpRequest):
            http_method: Literal["POST"]

            class PathParameters(BaseModel):
                serial_number: str = Field(alias="serialNumber")

            path_parameters: PathParameters

        event = {
            "requestContext": {"httpMethod": "POST"},
            "queryStringParameters": {"FeatureName": "gtfs-realtime-api"},
            "body": {"agency_id": "test"},
            "pathParameters": {"serialNumber": "123"},
        }

        http_request = HttpRequest(**event)

        request = SpecificRequest(**http_request.dict())

        assert request.http_method == "POST"
        assert request.path_parameters.serial_number == "123"
