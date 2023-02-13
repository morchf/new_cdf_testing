import json
import logging
from argparse import ArgumentParser
from collections.abc import Callable
from typing import Any


def trigger_local(handler: Callable[Any, Any]):
    parser = ArgumentParser(description="Test lambda with specified event/context")
    parser.add_argument("--event", type=str, help="event passed to lambda_handler")
    parser.add_argument("--context", type=str, help="context passed to lambda_handler")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    # override to just print the response
    def http_response(statusCode, body, _=None):  # noqa: F811
        logging.info(f"Status Code: {statusCode} Body: {body}")

    handler(json.loads(args.event or "null"), json.loads(args.context or "null"))
