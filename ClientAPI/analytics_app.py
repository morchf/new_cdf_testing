import os

import aws_cdk as cdk
from api.analytics import AnalyticsApiModule
from aws_cdk import Stack, aws_apigateway, aws_ec2
from constructs import Construct
from dwh.dwh_module import DwhModule
from gtt.constructs.cdk import App


class AnalyticsApp(Stack):
    def __init__(self, scope: Construct, id: str, environment: str, **kwargs) -> None:
        assert id

        super().__init__(scope, id, **kwargs)

        self.__environment = environment

        # Networking
        self.__subnet_ids = os.getenv("SUBNETS").split(",")
        self.__vpc = aws_ec2.Vpc.from_vpc_attributes(
            self,
            f"{id}-vpc",
            vpc_id=os.getenv("VPC_ID"),
            availability_zones=cdk.Fn.get_azs(),
            private_subnet_ids=self.__subnet_ids,
        )
        self.__sg = aws_ec2.SecurityGroup.from_security_group_id(
            self,
            f"{id}-sg",
            os.getenv("SECURITY_GROUP"),
        )

        self.__redshift_secret_arn = os.getenv("REDSHIFT_SECRET_ARN")
        self.__redshift_cluster_endpoint = os.getenv("REDSHIFT_CLUSTER_ENDPOINT")

        # DATA WAREHOUSE module
        dwh = DwhModule(
            self,
            f"{id}-dwh",
            environment=self.__environment,
            vpc=self.__vpc,
            sg=self.__sg,
            redshift_secret_arn=self.__redshift_secret_arn,
            redshift_cluster_endpoint=self.__redshift_cluster_endpoint,
            dwh_role_arn=os.getenv("DWH_ROLE_ARN"),
            glue_analytics_db=os.getenv("GLUE_ANALYTICS_DB"),
            glue_evp_db=os.getenv("GLUE_EVP_DB"),
            glue_tsp_db=os.getenv("GLUE_TSP_DB"),
            glue_gtfs_db=os.getenv("GLUE_GTFS_DB"),
        )

        # Analytics API module
        AnalyticsApiModule(
            self,
            f"{id}-analyticsApi",
            vpc=self.__vpc,
            sg=self.__sg,
            cognito_user_pool_arn=os.getenv("COGNITO_USER_POOL_ARN"),
            redshift_secret_arn=dwh.api_secret_arn,
            athena_work_group=os.getenv("ATHENA_WORK_GROUP", "primary"),
            athena_query_results_bucket_arn=os.getenv(
                "ATHENA_QUERY_RESULTS_BUCKET_ARN"
            ),
            data_lake_bucket_arn=os.getenv("DATA_LAKE_BUCKET_ARN"),
        )

        aws_apigateway.SpecRestApi(
            self,
            id,
            api_definition=aws_apigateway.ApiDefinition.from_asset(
                "api/analytics/openapi.yaml"
            ),
        )


with App(
    project_id="ClientAPI",
    app_id="Analytics",
    owner="jacob.sampson",
) as app:
    AnalyticsApp(**app.kwargs)
