from pathlib import Path
from typing import Optional

from aws_cdk import (
    Duration,
    Stack,
    aws_apigateway,
    aws_cognito,
    aws_dynamodb,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_events,
    aws_events_targets,
)
from constructs import Construct
from core.util import Environment
from gtt.constructs.cdk import LocalLambda, LocalLambdaLayer, ProxyApi

LAMBDA_BASE_DIR = Path(__file__).parent.absolute()


class Policies(Construct):
    AllowSSMExecute: aws_iam.ManagedPolicy
    AllowAssetLibraryAccess: aws_iam.ManagedPolicy
    AllowAssetsWrite: aws_iam.ManagedPolicy
    AllowDynamodbGSIQuery: aws_iam.ManagedPolicy

    def __init__(self, scope: Construct, id: str, environment: str):
        super().__init__(scope, id)

        stack = Stack.of(self)

        self.AllowSSMExecute = aws_iam.ManagedPolicy(
            self,
            "AllowSSMExecute",
            managed_policy_name=f"{id}-AllowSSMExecute",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            "ssm:SendCommand",
                            "ssmmessages:CreateDataChannel",
                            "ssmmessages:OpenDataChannel",
                            "ssmmessages:OpenControlChannel",
                            "ssmmessages:CreateControlChannel",
                            "ssm:GetCommandInvocation",
                            "ec2:DescribeInstances",
                        ],
                        resources=["*"],
                    )
                ]
            ),
        )

        self.AllowAssetLibraryAccess = aws_iam.ManagedPolicy(
            self,
            "AllowAssetLibraryAccess",
            managed_policy_name=f"{id}-AllowAssetLibraryAccess",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["lambda:InvokeFunction"],
                        resources=[
                            f"arn:{stack.partition}:lambda:{stack.region}:{stack.account}:function:cdf-assetlibrary-stage-LambdaFunction*"
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["cloudformation:DescribeStacks"],
                        resources=[
                            f"arn:{stack.partition}:cloudformation:{stack.region}:{stack.account}:stack/CDFDeploymentPipelineStack-SAM/*"
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["execute-api:Invoke", "execute-api:ManageConnections"],
                        resources=[
                            f"arn:{stack.partition}:execute-api:{stack.region}:{stack.account}:*"
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["apigateway:GET"],
                        resources=["arn:aws:apigateway:*::/restapis"],
                    ),
                ]
            ),
        )

        self.AllowAssetsWrite = aws_iam.ManagedPolicy(
            self,
            "AllowAssetsWrite",
            managed_policy_name=f"{id}-AllowAssetsWrite",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["s3:ListBucket"],
                        resources=["arn:aws:s3:::*"],
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
                        resources=[
                            f"arn:aws:s3:::scp-analytics-{environment}--assets/*"
                        ],
                    ),
                ]
            ),
        )

        self.AllowDynamodbGSIQuery = aws_iam.ManagedPolicy(
            self,
            "AllowDynamodbGSIQuery",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["dynamodb:Query"],
                        resources=[
                            f"arn:aws:dynamodb:{stack.region}:{stack.account}:table/globalMacVps/index/*"
                        ],
                    )
                ]
            ),
        )


class IntersectionsApiModule(Construct):
    @property
    def api_id(self):
        return self.__api.api.rest_api_id

    def __init__(
        self,
        scope: Construct,
        id: str,
        environment: str,
        vpc: aws_ec2.Vpc,
        sg: aws_ec2.SecurityGroup,
        cognito_user_pool_arn: str,
        instance_ids: str,  # TODO: Replace
        vps_table_name: str,
        intersections_table_name: Optional[str] = None,
        use_public_ips: Optional[bool] = False,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        # TODO: Move to using long name everywhere
        environment = Environment(short_name=environment).long_name

        self.__policies = Policies(self, f"{id}-Policies", environment=environment)

        # Common Lambda resources
        self.__api = ProxyApi(
            self,
            "Api",
            api_name=f"{id}-Api",
            # Encoded CSV files
            binary_media_types=["multipart/form-data"],
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

        # Create table if not exists
        if intersections_table_name is None:
            self.__dynamodb_table = aws_dynamodb.Table(
                self,
                "IntersectionsTable",
                table_name=f"{id}-PhaseSelectors",
                partition_key=aws_dynamodb.Attribute(
                    name="agency_id",
                    type=aws_dynamodb.AttributeType.STRING,
                ),
                sort_key=aws_dynamodb.Attribute(
                    name="serial_number",
                    type=aws_dynamodb.AttributeType.STRING,
                ),
            )
            intersections_table_name = self.__dynamodb_table.table_name
        else:
            self.__dynamodb_table = aws_dynamodb.Table.from_table_name(
                self, "IntersectionsTable", intersections_table_name
            )
        self.__vps_table_name = aws_dynamodb.Table.from_table_name(
            self, "globalMacVps", vps_table_name
        )
        self.__lambda_layer = LocalLambdaLayer(
            self,
            "IntersectionLayer",
            layer_name="IntersectionLayer",
            requirements_file=f"{LAMBDA_BASE_DIR}/requirements.txt",
        ).layer

        self.__lambda_kwargs = {
            "layers": [self.__lambda_layer],
            "vpc": vpc,
            "security_groups": [sg],
            "environment": {
                "VPS_TABLE_NAME": vps_table_name,
                "INTERSECTIONS_TABLE_NAME": intersections_table_name,
                "INSTANCE_IDS": instance_ids,
            },
        }

        # """
        # ENDPOINTS
        # """

        # /intersections
        intersections_resource = self.__api.add_root_resource("intersections")

        intersections_lambda = LocalLambda(
            self,
            "Intersections",
            base_dir=LAMBDA_BASE_DIR,
            function_name=f"{id}-Intersections",
            code_dir="intersections",
            # Can be very long if reading directly from device
            timeout=Duration.seconds(60),
            **self.__lambda_kwargs,
        )
        intersections_lambda.function.role.add_managed_policy(
            self.__policies.AllowSSMExecute
        )

        self.__dynamodb_table.grant_read_write_data(intersections_lambda.function)
        self.__vps_table_name.grant_read_data(intersections_lambda.function)
        intersections_lambda.function.role.add_managed_policy(
            self.__policies.AllowDynamodbGSIQuery
        )
        # GET
        self.__api.add_method(
            lambda_function=intersections_lambda.function,
            http_methods=["GET", "POST"],
            resource=intersections_resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )

        # /intersections/:intersection_name
        intersection_resource = intersections_resource.add_resource("{serialNumber}")

        intersection_lambda = LocalLambda(
            self,
            "Intersection",
            base_dir=LAMBDA_BASE_DIR,
            function_name=f"{id}-Intersection",
            code_dir="intersection",
            **self.__lambda_kwargs,
        )

        self.__dynamodb_table.grant_read_write_data(intersection_lambda.function)
        self.__vps_table_name.grant_read_data(intersection_lambda.function)
        intersection_lambda.function.role.add_managed_policy(
            self.__policies.AllowDynamodbGSIQuery
        )
        # GET, POST, PUT
        self.__api.add_method(
            lambda_function=intersection_lambda.function,
            http_methods=["POST", "GET", "PUT"],
            resource=intersection_resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )

        # /import

        self.__import_lambda_layer = LocalLambdaLayer(
            self,
            "ImportIntersectionLayer",
            layer_name="ImportIntersectionLayer",
            requirements_file=f"{LAMBDA_BASE_DIR}/import/requirements.txt",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
        ).layer

        import_resource = self.__api.add_root_resource("import")

        intersections_s3_bucket_name = f"scp-analytics-{environment}--assets"

        import_lambda = LocalLambda(
            self,
            "Import",
            base_dir=LAMBDA_BASE_DIR,
            function_name=f"{id}-Import",
            code_dir="import",
            environment={"S3_BUCKET": intersections_s3_bucket_name},
            layers=[self.__import_lambda_layer],
            runtime=aws_lambda.Runtime.PYTHON_3_9,
        )

        import_lambda.function.role.add_managed_policy(
            self.__policies.AllowAssetLibraryAccess
        )
        import_lambda.function.role.add_managed_policy(self.__policies.AllowAssetsWrite)

        # POST
        self.__api.add_method(
            lambda_function=import_lambda.function,
            http_methods=["POST"],
            resource=import_resource,
            authorizer=self.__auth,
            authorization_type=aws_apigateway.AuthorizationType.COGNITO,
        )

        # Scheduled job lambda
        scheduled_lambda = LocalLambda(
            self,
            "scheduledGetIntersections",
            base_dir=LAMBDA_BASE_DIR,
            function_name=f"{id}-scheduledGetIntersections",
            code_dir="scheduledJob",
            timeout=Duration.minutes(15),
            **self.__lambda_kwargs,
        )

        self.__dynamodb_table.grant_read_write_data(scheduled_lambda.function)
        self.__vps_table_name.grant_read_data(scheduled_lambda.function)
        scheduled_lambda.function.role.add_managed_policy(
            self.__policies.AllowDynamodbGSIQuery
        )
        scheduled_lambda.function.role.add_managed_policy(
            self.__policies.AllowSSMExecute
        )
        # event bridge
        rule = aws_events.Rule(
            self,
            "triggerScheduledGetIntersection",
            rule_name=f"{id}-ScheduledGetIntersection",
            description="Trigger ScheduledGetIntersection lambda function every hour",
            schedule=aws_events.Schedule.rate(Duration.hours(1)),
        )
        rule.add_target(aws_events_targets.LambdaFunction(scheduled_lambda.function))
