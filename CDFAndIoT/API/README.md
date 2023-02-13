# GTT / API

## Getting Started

## Parsing Events

### HTTP Events

Map API Gateway endpoints/methods to different handlers. Return HTTP responses. Automatically handle HTTP responses

```python
from .models import GetRequest, PostRequest

from pydantic import BaseModel
from gtt.api import HttpRequest, http_response
from gtt.api.exceptions import ServerError
# from gtt.api.http import ok, error

class GetRequest(HttpRequest):
    class QueryParameters(BaseModel):
        param1: str

    http_method: Literal["GET"]
    query_parameters: QueryParameters

def handle_get(request: GetRequest):
    return { "result": None }


###

class PostRequest(HttpRequest):
    class QueryParameters(BaseModel):
        param1: str

    class Body(BaseModel):
        agency_id: Union[str, uuid.UUID]

    http_method: Literal["GET"]
    query_parameters: QueryParameters

def handle_post(request: PostRequest):
    raise ServerError()

####

@http_response
def handler(event, context, **kwargs):
    http_request = HttpRequest(**event)

    if http_request.http_method == "GET":
        # Wraps result in ok() if no exceptions
        return handle_get(GetRequest(**http_request.dict()))

    if http_request.http_method == "POST":
        # Wraps result in error() if exception
        return handle_post(PostRequest(**http_request.dict()))
```

Map API Gateway endpoints/methods to different handlers. Return HTTP responses. Automatically handle HTTP responses

```python
from .models impoty GetRequest, PostRequest

from pydantic import BaseModel
from gtt.api import HttpRequest, http_response
from gtt.api.exceptions import ServerError
# from gtt.api.http import ok, error

class GetRequest(HttpRequest):
    class QueryParameters(BaseModel):
        param1: str

    http_method: Literal["GET"]
    query_parameters: QueryParameters

def handle_get(request: GetRequest):
    return { "result": None }


###

class PostRequest(HttpRequest):
    class QueryParameters(BaseModel):
        param1: str

    class Body(BaseModel):
        agency_id: Union[str, uuid.UUID]

    http_method: Literal["GET"]
    query_parameters: QueryParameters

def handle_post(request: PostRequest):
    raise ServerError()

####

@http_response
def handler(event, context, **kwargs):
    http_request = HttpRequest(**event)

    if http_request.http_method == "GET":
        # Wraps result in ok() if no exceptions
        return handle_get(GetRequest(**http_request.dict()))

    if http_request.http_method == "POST":
        # Wraps result in error() if exception
        return handle_post(PostRequest(**http_request.dict()))
```

### Multiple Event Types

```python
from gtt.api.http import ok
from pydantic import parse_obj_as

# SingleHttpRequest and BatchSqsRequest are defined in Lambda

def handler(event, context, **kwargs):
    request = parse_obj_as(
        Union[SingleHttpRequest, BatchSqsRequest],
        event
    )

    if type(request) == SingleHttpRequest:
        return ok(handle_single(request))

    if type(request) == BatchSqsRequest:
        return handle_batch(request)
```

## Testing

```sh
python3 -B -m pytest -s
```
