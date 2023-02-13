from gtt.api import http_response

import logging

logging.getLogger().setLevel(logging.INFO)


@http_response
def handler(event, context):
    logging.info(f"Received {event=}, {context=}")
    return
