from time import time
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Response:
    """
    Wrap database response with metadata

    Usage:
        resposne = Resposne()
        return response.finish(data)
    """

    def __init__(self, event, context):
        self.start_time = time()

        # Save execution context and event
        self.event = event
        self.context = context

        self._log("Called function")

    def _log(self, *args):
        logger.info("".join([f"{self.context.function_name}: ", *args]))

    def prepare(self, data, errors=[]):
        end_time = time()

        self._log("Finished execution")

        return data
        return {
            "data": data,
            "errors": errors,
            "meta": {
                "start_time": self.start_time,
                "end_time": end_time,
                "event": {
                    "function_name": self.context.function_name,
                    "function_version": self.context.function_version,
                    "invoked_function_arn": self.context.invoked_function_arn,
                    "memory_limit_in_mb": self.context.memory_limit_in_mb,
                    "aws_request_id": self.context.aws_request_id,
                    "log_group_name": self.context.log_group_name,
                    "log_stream_name": self.context.log_stream_name,
                },
            },
        }
