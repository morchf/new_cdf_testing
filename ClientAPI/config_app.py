import os

import aws_cdk as cdk
from api.intersections import IntersectionsApiModule
from aws_cdk import Stack, aws_ec2
from constructs import Construct
from gtt.constructs.cdk import App


class ConfigApp(Stack):
    def __init__(self, scope: Construct, id: str, environment: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.__subnet_ids = os.getenv("SUBNET_IDS").split(",")

        self.__vpc = aws_ec2.Vpc.from_vpc_attributes(
            self,
            "Vpc",
            vpc_id=os.getenv("VPC_ID"),
            availability_zones=cdk.Fn.get_azs(),
            private_subnet_ids=self.__subnet_ids,
        )

        self.__sg = aws_ec2.SecurityGroup.from_security_group_id(
            self, "SecurityGroup", os.getenv("SG_ID")
        )

        self.__intersections_api_module = IntersectionsApiModule(
            self,
            id=f"{id}-IntersectionsApi",
            environment=environment,
            vpc=self.__vpc,
            sg=self.__sg,
            vps_table_name=os.getenv("VPS_TABLE_NAME"),
            intersections_table_name=os.getenv("INTERSECTIONS_TABLE_NAME"),
            cognito_user_pool_arn=os.getenv("COGNITO_USER_POOL_ARN"),
            instance_ids=os.getenv("INSTANCE_IDS"),
        )

        cdk.CfnOutput(self, "ApiId", value=self.__intersections_api_module.api_id)


with App(
    project_id="ClientAPI",
    app_id="Config",
    owner="kiran.mukunda",
) as app:
    ConfigApp(**app.kwargs)
