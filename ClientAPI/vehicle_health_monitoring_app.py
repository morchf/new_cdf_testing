import os

import aws_cdk as cdk
from api.vehicleHealthMonitoring import VehicleHealthMonitoringApiModule
from aws_cdk import Stack
from constructs import Construct
from gtt.constructs.cdk import App


class VehicleHealthMonitoringApp(Stack):
    def __init__(self, scope: Construct, id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.__vehicle_health_monitoring_api_module = VehicleHealthMonitoringApiModule(
            self,
            id=f"{id}-VehicleHMApi",
            cognito_user_pool_arn=os.getenv("COGNITO_USER_POOL_ARN"),
        )

        cdk.CfnOutput(
            self, "ApiId", value=self.__vehicle_health_monitoring_api_module.api_id
        )


with App(
    project_id="ClientAPI",
    app_id="VehicleHM",
    owner="ryan.kinnucan",
) as app:
    VehicleHealthMonitoringApp(**app.kwargs)
