import string
import subprocess
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import aws_ec2, aws_iam, aws_lambda, aws_s3
from constructs import Construct

FUNCTION_NAMES = [f.stem for f in Path("api/analytics/endpoints").glob("*.py")]


def exclude_files(current_function_name):
    return [
        f"{function_name}.py"
        for function_name in FUNCTION_NAMES
        if current_function_name != function_name
    ] + ["__init__.py"]


class AnalyticsApiModule(Construct):
    """
    See:
    - https://github.com/aws-samples/aws-cdk-examples/tree/master/python/api-cors-lambda
    - https://github.com/aws-samples/aws-cdk-examples/tree/master/python/image-content-search
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-swagger-extensions.html
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.Vpc,
        sg: aws_ec2.SecurityGroup,
        cognito_user_pool_arn: str,
        redshift_secret_arn: str,
        athena_work_group: str,
        athena_query_results_bucket_arn: str,
        data_lake_bucket_arn: str,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        # Simplify API name for shorter lambda functions
        api_id = id.rstrip("-api") if "-api-" in id else id

        bucket_athena_query_results = aws_s3.Bucket.from_bucket_name(
            self, f"{api_id}-bucketAthenaQueryResults", athena_query_results_bucket_arn
        )
        bucket_data_lake = aws_s3.Bucket.from_bucket_arn(
            self, f"{api_id}-bucketDataLake", data_lake_bucket_arn
        )

        # Create layers
        layers = [
            self.create_layer(
                f"{api_id}-layerPostgres", "layers/postgres-requirements.txt"
            ),
            self.create_layer(
                f"{api_id}-layerAnalytics", "layers/analytics-requirements.txt"
            ),
        ]

        # Create functions
        functions = {
            function_name: aws_lambda.Function(
                self,
                f"{api_id}-{function_name}",
                code=aws_lambda.Code.from_asset(
                    "api/analytics/endpoints", exclude=exclude_files(function_name)
                ),
                environment={
                    "ATHENA_OUTPUT_BUCKET": bucket_athena_query_results.bucket_name,
                    "ATHENA_WORK_GROUP": athena_work_group,
                    "REDSHIFT_SECRET_ARN": redshift_secret_arn,
                },
                # Override to keep function name short
                function_name=f"ClientAPI-Analytics-{function_name}",
                handler=f"{function_name}.handler",
                runtime=aws_lambda.Runtime.PYTHON_3_8,
                timeout=cdk.Duration.seconds(60),
                layers=layers,
                # Add VPC/SG/Layer for Redshift-connected functions
                vpc=vpc,
                security_groups=[sg],
            )
            for function_name in FUNCTION_NAMES
        }
        for function_name, aws_lambda_function in functions.items():
            aws_lambda_function.grant_invoke(
                aws_iam.ServicePrincipal("apigateway.amazonaws.com")
            )

            # Athena and Glue access
            aws_lambda_function.role.attach_inline_policy(
                aws_iam.Policy(
                    self,
                    f"{api_id}-{function_name}-athena",
                    document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                actions=[
                                    "athena:GetQueryExecution",
                                    "athena:GetQueryResults",
                                    "athena:StartQueryExecution",
                                    "glue:Get*",
                                ],
                                effect=aws_iam.Effect.ALLOW,
                                resources=["*"],
                            ),
                        ]
                    ),
                )
            )

            # Redshfit access
            aws_lambda_function.role.attach_inline_policy(
                aws_iam.Policy(
                    self,
                    f"{api_id}-{function_name}-redshift",
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
                                ],
                                resources=["*"],
                            ),
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
            )

            bucket_athena_query_results.grant_read_write(aws_lambda_function)
            bucket_data_lake.grant_read(aws_lambda_function)

        class Template(string.Template):
            delimiter = "$$"

        with open("api/analytics/openapi.template.yaml") as openapi_template, open(
            "api/analytics/openapi.yaml", "w"
        ) as openapi:
            print(
                Template(openapi_template.read()).substitute(
                    ARN_COGNITO_USER_POOL=cognito_user_pool_arn,
                    **{
                        f"ARN_LAMBDA_INVOCATION_{function_name.upper()}": f"arn:${{AWS::Partition}}:apigateway:${{AWS::Region}}:lambda:path/2015-03-31/functions/arn:${{AWS::Partition}}:lambda:${{AWS::Region}}:${{AWS::AccountId}}:function:ClientAPI-Analytics-{function_name}/invocations"
                        for function_name, _ in functions.items()
                    },
                    OPTIONS=""" {"responses":{"204":{"content":{},"description":"204 response","headers":{"Access-Control-Allow-Headers":{"schema":{"type":"string"}},"Access-Control-Allow-Methods":{"schema":{"type":"string"}},"Access-Control-Allow-Origin":{"schema":{"type":"string"}}}}},"x-amazon-apigateway-integration":{"passthroughBehavior":"when_no_match","requestTemplates":{"application/json":"{ statusCode: 200 }"},"responses":{"default":{"responseParameters":{"method.response.header.Access-Control-Allow-Headers":"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent'","method.response.header.Access-Control-Allow-Methods":"'GET,OPTIONS,POST'","method.response.header.Access-Control-Allow-Origin":"'*'"},"statusCode":"204"}},"type":"mock"}} """,
                ),
                file=openapi,
            )

    def create_layer(self, layer_id, requirements_file):
        subprocess.call(
            [
                "pip",
                "install",
                "-t",
                f"api/analytics/{layer_id}/python/lib/python3.8/site-packages",
                "-r",
                f"api/analytics/{requirements_file}",
                "--upgrade",
            ]
        )

        return aws_lambda.LayerVersion(
            scope=self,
            id=layer_id,
            code=aws_lambda.Code.from_asset(f"api/analytics/{layer_id}"),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_8],
        )
