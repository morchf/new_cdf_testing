from argparse import ArgumentError
from typing import List, Literal, Optional, Union

from aws_cdk import aws_apigateway, aws_lambda
from constructs import Construct

HttpMethod = Union[
    Literal["DELETE"],
    Literal["HEAD"],
    Literal["OPTIONS"],
    Literal["PATCH"],
    Literal["POST"],
    Literal["PUT"],
    Literal["GET"],
]


class Api(Construct):
    """
    Map all path, header, and query param key-values to the 'event' object
    """

    REQUEST_TEMPLATE = """
    #set($allParams = $input.params())
    {
        #foreach($type in $allParams.keySet())
        #set($params = $allParams.get($type))
            #foreach($paramName in $params.keySet())
            "$paramName" : "$util.escapeJavaScript($params.get($paramName))"
            #if($foreach.hasNext),#end
            #end
        #if($foreach.hasNext),#end
        #end
    }
    """

    @property
    def api(self):
        return self.__api

    def __init__(
        self,
        scope: Construct,
        id: str,
        api_name: str = None,
        rest_api_ref: str = None,
        rest_api_root_resource_id: str = "/",
        **kwargs
    ):
        super().__init__(scope, id)

        if rest_api_ref is not None:
            self.__api = aws_apigateway.RestApi.from_rest_api_attributes(
                self,
                api_name,
                rest_api_id=rest_api_ref,
                root_resource_id=rest_api_root_resource_id,
                **kwargs
            )
            return

        # Create new API
        self.__api = aws_apigateway.RestApi(
            self,
            api_name,
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
                allow_methods=aws_apigateway.Cors.ALL_METHODS,
            ),
            deploy=False,
            **kwargs
        )
        self.__deployment = None

    def attach_docs(self, template_path: str):
        pass

    def add_deployment(self):
        return self._create_deployment(stage_name=self.__stage_name)

    def add_root_resource(self, endpoint: str):
        return self.__api.root.add_resource(endpoint)

    def use_resource(
        self,
        resource: Optional[aws_apigateway.Resource] = None,
        endpoint: Optional[str] = None,
    ):
        if resource is None and endpoint is None:
            raise ArgumentError("Must fill one of 'resource' or 'endpoint'")

        # Create new resource if none passed in
        if resource is None:
            resource = self.add_root_resource(endpoint)

        # Add endpoint to resource
        if endpoint is not None:
            resource = resource.add_resource(endpoint)

        return resource

    def add_method(
        self,
        lambda_function: aws_lambda.IFunction,
        http_methods: List[HttpMethod],
        *,
        endpoint: Optional[str] = None,
        resource: Optional[aws_apigateway.Resource] = None,
        proxy: Optional[bool] = False,
        auto_map: Optional[bool] = True,
        method_responses: Optional[List[aws_apigateway.MethodResponse]] = None,
        cognito_authorizer_id: Optional[str] = None,
        **kwargs
    ):
        resource = self.use_resource(resource=resource, endpoint=endpoint)

        return [
            self._create_method(
                resource=resource,
                http_method=http_method,
                lambda_function=lambda_function,
                proxy=proxy,
                auto_map=auto_map,
                method_responses=method_responses,
                cognito_authorizer_id=cognito_authorizer_id,
                **kwargs
            )
            for http_method in http_methods
        ]

    def _create_method(
        self,
        resource: aws_apigateway.Resource,
        http_method: str,
        lambda_function: aws_lambda.IFunction,
        proxy: Optional[bool] = None,
        auto_map: Optional[bool] = False,
        method_responses: Optional[List[aws_apigateway.MethodResponse]] = None,
        cognito_authorizer_id: Optional[str] = None,
        **kwargs
    ) -> aws_apigateway.Method:
        lambda_integration = aws_apigateway.LambdaIntegration(
            lambda_function,
            proxy=proxy,
            # Convert query params and body key-value pairs to arguments
            request_templates=(
                {"application/json": Api.REQUEST_TEMPLATE} if auto_map else {}
            ),
        )

        method = resource.add_method(
            http_method=http_method,
            integration=lambda_integration,
            method_responses=method_responses
            or [
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
                aws_apigateway.MethodResponse(status_code="400"),
            ],
            **kwargs
        )

        if cognito_authorizer_id:
            self._add_cognito_authorizer(method, cognito_authorizer_id)

        return method

    def _add_cognito_authorizer(self, method, authorizer_id):
        method_resource = method.node.find_child("Resource")

        # Add properties to low-level resource
        method_resource.add_property_override("AuthorizationType", "COGNITO_USER_POOLS")

        # AuthorizedId uses Ref, simulate with a dictionary
        method_resource.add_property_override("AuthorizerId", {"Ref": authorizer_id})

    def create_stage(self, stage_name: str) -> aws_apigateway.Stage:
        if not self.__deployment:
            # Add deployment
            self.__deployment = aws_apigateway.Deployment(
                self,
                "ApiDeployment",
                api=self.__api,
            )

        # Add stage
        return aws_apigateway.Stage(
            self, "Stage", deployment=self.__deployment, stage_name=stage_name
        )


class ProxyApi(Api):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

    def add_method(
        self,
        lambda_function: aws_lambda.IFunction,
        http_methods: List[HttpMethod],
        resource: Optional[aws_apigateway.Resource] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ):
        resource = self.use_resource(resource=resource, endpoint=endpoint)

        return [
            self._create_method(
                resource=resource,
                http_method=http_method,
                lambda_function=lambda_function,
                proxy=True,
                auto_map=False,
                **kwargs
            )
            for http_method in http_methods
        ]
