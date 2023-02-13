import os

import aws_cdk as cdk
from api.intersection_health_monitoring.ihm_api_module import (
    IntersectionsHealthMonitoringApiModule,
)
from aws_cdk import Stack
from constructs import Construct
from gtt.constructs.cdk import App


class IntMonitoringApp(Stack):
    def __init__(self, scope: Construct, id: str, environment: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.__ihm_api_module = IntersectionsHealthMonitoringApiModule(
            self,
            id=f"{id}-IntersectionsApi",
            environment=environment,
            redshift_secret_arn=os.getenv("REDSHIFT_SECRET_ARN"),
            cognito_user_pool_arn=os.getenv("COGNITO_USER_POOL_ARN"),
        )

        cdk.CfnOutput(self, "ApiId", value=self.__ihm_api_module.api_id)


with App(
    project_id="ClientAPI",
    app_id="IntHM",
    owner="kiran.mukunda",
) as app:
    IntMonitoringApp(**app.kwargs)
