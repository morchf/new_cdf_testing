from .exceptions import NotFoundException, ServerError
from .http import error, not_found, ok


def http_response(func):
    """
    Parses different Lambda event types and exposes keywork-arguments to the
    wrapped functions

    Args:
        http: Wrap call with HTTP error handling

    Return:
        HTTP response with any response data loaded into the "body" key and
        error messages within an error object

    {
        "statusCode": status_code,
        "body": json_body | { "error": error_message },
        "headers": {
            "Content-Type": content_type,
            "Access-Control-Allow-Origin": "*"
        },
    }
    """

    def wrapper(event, context, *args, **kwargs):
        # Handle typical HTTP exception scenarios
        try:
            return ok(func(event, context, *args, **kwargs))
        except NotFoundException as e:
            return not_found({"error": str(e)})
        except ServerError as e:
            return error({"error": str(e)}, status_code=500)
        except ValueError as e:
            return error({"error": str(e)}, status_code=400)
        except Exception as e:
            return error({"error": str(e)})

    return wrapper
