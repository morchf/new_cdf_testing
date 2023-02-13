import json
import subprocess

import aws_cdk as cdk
from aws_cdk import aws_ec2, aws_iam, aws_lambda
from aws_cdk import aws_secretsmanager as aws_sm
from constructs import Construct
from core.util import Environment


class DwhModule(Construct):
    @property
    def api_secret_arn(self):
        return self.__api_secret_arn

    def __init__(
        self,
        scope: Construct,
        id: str,
        environment: str,
        vpc: aws_ec2.Vpc,
        sg: aws_ec2.SecurityGroup,
        redshift_secret_arn: str,
        redshift_cluster_endpoint: str,
        dwh_role_arn: str,
        glue_analytics_db: str,
        glue_evp_db: str,
        glue_tsp_db: str,
        glue_gtfs_db: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.__vpc = vpc
        self.__lambda_sg = sg
        self.__redshift_secret_arn = redshift_secret_arn

        # Redshift cluster connection details
        redshift_host, redshift_port = redshift_cluster_endpoint.split(":")
        redshift_dbname = environment

        # API execution role
        self.__api_user_secret = aws_sm.Secret(
            scope=self,
            id=f"{id}-secretApi",
            description="API user Redshift. Read-only permissions granted to relevant tables",
            generate_secret_string=aws_sm.SecretStringGenerator(
                exclude_characters="'",
                exclude_punctuation=True,
                generate_string_key="password",
                secret_string_template=json.dumps(
                    {
                        "username": "api",
                        "dbname": redshift_dbname,
                        "host": redshift_host,
                        "port": redshift_port,
                    }
                ),
            ),
        )
        # EVP user role
        self.__evp_user_secret = aws_sm.Secret(
            scope=self,
            id=f"{id}-secretEvp",
            description="EVP user Redshift. Read-only permissions granted to EVP tables",
            generate_secret_string=aws_sm.SecretStringGenerator(
                exclude_characters="'",
                exclude_punctuation=True,
                generate_string_key="password",
                secret_string_template=json.dumps(
                    {
                        "username": "evp",
                        "dbname": redshift_dbname,
                        "host": redshift_host,
                        "port": redshift_port,
                    }
                ),
            ),
        )
        self.__api_secret_arn = self.__api_user_secret.secret_arn
        self.__evp_secret_arn = self.__evp_user_secret.secret_arn

        # Bootstrapping Lambda
        subprocess.call(
            [
                "pip",
                "install",
                "-t",
                "dwh/layer/python/lib/python3.8/site-packages",
                "-r",
                "dwh/sql/requirements.txt",
                "--upgrade",
            ]
        )

        layer = aws_lambda.LayerVersion(
            scope=self,
            id=f"{id}-layerDwhManager",
            code=aws_lambda.Code.from_asset("dwh/layer"),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_8],
        )

        # This lambda function will run SQL commands to setup Redshift users and tables
        env = Environment(long_name=environment)

        dwh_manager_environment = {
            "REDSHIFT_SECRET_ARN": self.__redshift_secret_arn,
            "SQL_SCRIPT_KWARGS": json.dumps(
                {
                    # External buckets
                    "ASSET_S3_BUCKET": f"scp-analytics-{env.long_name}--assets",
                    "CVP_S3_PATH": f"client-api-etl-{env.long_name}/tsp_source_data/tsp_dataset",
                    "RT_RADIO_S3_BUCKET": f"rt-radio-message-{env.long_name}",
                    "STATIC_GTFS_S3_BUCKET": f"client-api-etl-{env.long_name}/gtfs",
                    # "RT_GTFS_VEHICLE_POSITIONS_S3_PATH": f"gtfs-realtime-{env.long_name}/vehicle_positions",
                    "RT_GTFS_VEHICLE_POSITIONS_S3_PATH": f"client-api-etl-{env.long_name}/gtfs-realtime/vehicle_positions",
                    # EVP
                    "MP70_S3_PATH": f"runtime-device-message-{env.long_name}/MP70-EVP",
                    "EVP_S3_PATH": f"scp-analytics-{env.long_name}--assets",
                    # Config
                    "GLUE_ANALYTICS_DB": glue_analytics_db,
                    "GLUE_EVP_DB": glue_evp_db,
                    "GLUE_TSP_DB": glue_tsp_db,
                    "GLUE_GTFS_DB": glue_gtfs_db,
                    "IAM_ROLE": dwh_role_arn,
                    "API_USER_SECRET": self.__api_secret_arn,
                    "EVP_USER_SECRET": self.__evp_secret_arn,
                    "ENV": env.short_name,
                }
            ),
        }
        cdk.CfnOutput(self, "dwhEnvironment", value=json.dumps(dwh_manager_environment))

        # This lambda function will run SQL commands for DWH management
        dwh_manager_function_name = f"{id}-dwhLambda"
        dwh_manager_function = aws_lambda.Function(
            scope=self,
            id=f"{id}-templateDwhManager",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset("dwh/sql"),
            handler="app.handler",
            environment=dwh_manager_environment,
            layers=[layer],
            timeout=cdk.Duration.minutes(15),
            vpc=self.__vpc,
            security_groups=[self.__lambda_sg],
            function_name=dwh_manager_function_name,
            memory_size=256,
        )

        lambda_role = dwh_manager_function.role

        lambda_role.attach_inline_policy(
            aws_iam.Policy(
                self,
                id=f"{id}-policyDwhManager",
                document=aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "ec2:CreateNetworkInterface",
                                "ec2:DescribeNetworkInterfaces",
                                "ec2:DeleteNetworkInterface",
                                "ec2:AssignPrivateIpAddresses",
                                "ec2:UnassignPrivateIpAddresses",
                                "ec2:DescribeSecurityGroups",
                                "ec2:DescribeSubnets",
                                "ec2:DescribeVpcs",
                                "secretsmanager:ListSecrets",
                            ],
                            resources=["*"],
                        ),
                        aws_iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetSecretValue",
                                "secretsmanager:DescribeSecret",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                self.__redshift_secret_arn,
                                self.__api_secret_arn,
                                self.__evp_secret_arn,
                            ],
                        ),
                    ],
                ),
            )
        )
