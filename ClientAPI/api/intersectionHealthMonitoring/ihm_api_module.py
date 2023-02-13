from pathlib import Path

from aws_cdk import (
    aws_apigateway,
    aws_cognito,
    aws_iam,
)
from constructs import Construct
from core.util import Environment
from gtt.constructs.cdk import LocalLambda, ProxyApi

LAMBDA_BASE_DIR = Path(__file__).parent.absolute()


class Policies(Construct):
    AllowRedshiftAccess: aws_iam.ManagedPolicy

    def __init__(
        self, scope: Construct, id: str, environment: str, redshift_secret_arn: str
    ):
        super().__init__(scope, id)
        self.AllowRedshiftAccess = aws_iam.ManagedPolicy(
            self,
            "AllowRedshiftAccess",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        actions=[
                            "secretsmanager:GetSecretValue",
                            "secretsmanager:DescribeSecret",
                            "secretsmanager:ListSecrets",
                        ],
                        effect=aws_iam.Effect.ALLOW,
                        resources=[redshift_secret_arn],
                    ),
                ],
            ),
        )


class IntersectionsHealthMonitoringApiModule(Construct):
    @property
    def api_id(self):
        return self.__api.api.rest_api_id

    def __init__(
        self,
        scope: Construct,
        id: str,
        cognito_user_pool_arn: str,
        environment: str,
        redshift_secret_arn: str,
        **kwargs,
    ):

        super().__init__(scope, id, **kwargs)
        environment = Environment(short_name=environment).long_name

        self.__policies = Policies(
            self,
            f"{id}-Policies",
            environment=environment,
            redshift_secret_arn=redshift_secret_arn,
        )

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

        resource = self.__api.add_root_resource("intersections")
        hm_lambda = LocalLambda(
            self,
            "IHM",
            base_dir=LAMBDA_BASE_DIR,
            function_name=f"{id}-Intersection-HM",
            code_dir="intersection_health_monitoring/intersections",
        )
        hm_lambda.function.role.add_managed_policy(self.__policies.AllowRedshiftAccess)

        self.__api.add_method(
            lambda_function=hm_lambda.function,
            http_methods=["GET"],
            resource=resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )
