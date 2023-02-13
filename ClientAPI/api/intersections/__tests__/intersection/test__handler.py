import json
import logging

from intersection.app import handler

# from moto import mock_dynamodb, mock_ssm

logging.getLogger().setLevel(logging.INFO)


class TestIntersectionHandler:
    def test__handler__empty(self):
        response = handler({}, {})

        assert response
        assert response["statusCode"] == 400
        assert "Missing key" in json.loads(response["body"])["error"]

    def test__handler__basic(self):
        # with mock_dynamodb(), mock_ssm():
        response = handler(
            {
                "requestContext": {},
                "queryStringParameters": {
                    "agencyId": "sfmta",
                    "serialNumber": "123",
                },
                "body": {
                    "intersectionId": 12347,
                    "intersectionName": "abc",
                    "latitude": 37.343312,
                    "longitude": 122.453532,
                    "lastCommunicated": "2022-07-10",
                    "make": "GTT",
                    "model": "v764",
                    "timezone": "CST",
                    "operationMode": "High",
                    "status": "Normal",
                    "firmwareVersion": 1.2,
                },
                "httpMethod": "POST",
            },
            {},
        )

        assert response
        assert response["body"] == ""
        assert response["statusCode"] == 200
