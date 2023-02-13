import json
import logging

from pydantic import BaseModel


def http_response(status_code, body=None, content_type="application/json"):
    logging.info(f"Status Code: {status_code} Body: {body} ")

    if body is None:
        body = {}

    # Convert body to JSON using Pydantic JSON function if applicable
    json_body = (
        body.json(by_alias=True)
        if isinstance(body, BaseModel)
        else json.dumps(body, default=str)
    )
    return {
        "statusCode": status_code,
        "body": json_body,
        "headers": {"Content-Type": content_type, "Access-Control-Allow-Origin": "*"},
    }


def ok(body, status_code: int = 200, **kwargs):
    return http_response(status_code=status_code, body=body, **kwargs)


def not_found(body, status_code: int = 404, **kwargs):
    return http_response(status_code=status_code, body=body, **kwargs)


def error(body, status_code: int = 500, **kwargs):
    return http_response(status_code=status_code, body=body, **kwargs)
