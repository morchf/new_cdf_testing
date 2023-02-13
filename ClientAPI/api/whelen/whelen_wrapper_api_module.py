import os
from aws_cdk import (
    aws_apigateway,
    aws_cognito,
    aws_lambda,
)
from constructs import Construct
from gtt.constructs.cdk import ProxyApi


class WhelenWrapperApiModule(Construct):
    @property
    def api_id(self):
        return self.__api.api.rest_api_id

    def __init__(
        self,
        scope: Construct,
        id: str,
        cognito_user_pool_arn: str,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.__api = ProxyApi(
            self,
            "Api",
            api_name=f"{id}-Api",
        )

        self.__auth = aws_apigateway.CognitoUserPoolsAuthorizer(
            self,
            "Authorizer",
            cognito_user_pools=[
                aws_cognito.UserPool.from_user_pool_arn(
                    self, "UserPool", cognito_user_pool_arn
                )
            ],
        )

        whelen_lamba = aws_lambda.Function.from_function_arn(
            self,
            f"{id}-Lambda",
            os.getenv("WHELEN_BATCH_PROCESSING_LAMBDA_ARN"),
        )

        change_preemption_resource = self.__api.add_root_resource("changepreemption")

        # POST
        self.__api.add_method(
            lambda_function=whelen_lamba,
            http_methods=["POST"],
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="202",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                ),
            ],
            resource=change_preemption_resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )

        import_vehicle_resource = self.__api.add_root_resource("importvehicles")

        # GET
        self.__api.add_method(
            lambda_function=whelen_lamba,
            http_methods=["GET"],
            resource=import_vehicle_resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )
