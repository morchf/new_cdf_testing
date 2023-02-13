import os

import aws_cdk as cdk
from api.whelen import WhelenWrapperApiModule
from aws_cdk import Stack
from constructs import Construct
from gtt.constructs.cdk import App


class WhelenApp(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        environment: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.__whelen_wrapper_api_module = WhelenWrapperApiModule(
            self,
            id=f"{id}-WhelenWrapperApi",
            cognito_user_pool_arn=os.getenv("COGNITO_USER_POOL_ARN"),
        )

        cdk.CfnOutput(self, "ApiId", value=self.__whelen_wrapper_api_module.api_id)


with App(
    project_id="ClientAPI",
    app_id="Whelen",
    owner="ryan.kinnucan",
) as app:
    WhelenApp(**app.kwargs)
