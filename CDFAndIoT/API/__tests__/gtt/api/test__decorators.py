import json

from gtt.api.decorators import http_response
from gtt.api.exceptions import NotFoundException, ServerError


class TestDecorators:
    def test__http_response__200(self):
        @http_response
        def handler(*args, **kwargs):
            return {}

        response = handler({}, {})

        assert "statusCode" in response
        assert response["statusCode"] == 200

        assert "body" in response
        assert "headers" in response

    def test__http_response__500(self):
        @http_response
        def handler(*args, **kwargs):
            raise ServerError("Error!")

        response = handler({}, {})

        assert "statusCode" in response
        assert response["statusCode"] == 500

        assert "body" in response
        assert json.loads(response["body"])["error"] == "Error!"

        assert "headers" in response

    def test__http_response__404(self):
        @http_response
        def handler(*args, **kwargs):
            raise NotFoundException()

        response = handler({}, {})

        assert "statusCode" in response
        assert response["statusCode"] == 404

        assert "body" in response
        assert "headers" in response

    def test__http_response__400(self):
        @http_response
        def handler(*args, **kwargs):
            raise ValueError()

        response = handler({}, {})

        assert "statusCode" in response
        assert response["statusCode"] == 400

        assert "body" in response
        assert "headers" in response

    def test__http_response__generic_500(self):
        @http_response
        def handler(*args, **kwargs):
            raise Exception()

        response = handler({}, {})

        assert "statusCode" in response
        assert response["statusCode"] == 500

        assert "body" in response
        assert "headers" in response
