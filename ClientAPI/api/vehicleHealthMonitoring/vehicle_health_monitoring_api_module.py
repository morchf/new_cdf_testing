from pathlib import Path
from aws_cdk import (
    aws_apigateway,
    aws_cognito,
)
from constructs import Construct
from gtt.constructs.cdk import ProxyApi, LocalLambda

LAMBDA_BASE_DIR = Path(__file__).parent.absolute()


class VehicleHealthMonitoringApiModule(Construct):
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

        # """
        # ENDPOINTS
        # """

        # Vehicles Data
        vehicles_resource = self.__api.add_root_resource("vehicles")

        vehicles_lambda = LocalLambda(
            self,
            "Vehicles",
            base_dir=LAMBDA_BASE_DIR,
            function_name=f"{id}-Vehicles",
            code_dir="vehicles",
        )

        # GET
        self.__api.add_method(
            lambda_function=vehicles_lambda.function,
            http_methods=["GET"],
            resource=vehicles_resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )

        # Vehicles in Communication
        vehicles_in_com_resource = self.__api.add_root_resource(
            "vehicles_in_communication"
        )

        vehicles_in_com_lambda = LocalLambda(
            self,
            "VehiclesInCommunication",
            base_dir=LAMBDA_BASE_DIR,
            function_name=f"{id}-VehiclesInCommunication",
            code_dir="vehiclesInCommunication",
        )

        # GET
        self.__api.add_method(
            lambda_function=vehicles_in_com_lambda.function,
            http_methods=["GET"],
            resource=vehicles_in_com_resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )

        # Vehicles in System
        vehicles_in_sys_resource = self.__api.add_root_resource("vehicles_in_system")

        vehicles_in_sys_lambda = LocalLambda(
            self,
            "VehiclesInSystem",
            base_dir=LAMBDA_BASE_DIR,
            function_name=f"{id}-VehiclesInSystem",
            code_dir="vehiclesInSystem",
        )

        # GET
        self.__api.add_method(
            lambda_function=vehicles_in_sys_lambda.function,
            http_methods=["GET"],
            resource=vehicles_in_sys_resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )
