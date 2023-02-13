import os
from typing import Optional, Sequence

from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

from .constants import prefix


class FargateExecutionRole(iam.Role):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(
            scope,
            id,
            role_name=f"{prefix}-{id}",
            description="Role to be assumed by fargate tasks when executing",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            **kwargs,
        )
        stack = Stack.of(self)
        self.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                "AmazonECSTaskExecutionRolePolicy",
                f"arn:{stack.partition}:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
            ),
        )
        self.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                "AmazonEC2ContainerRegistryReadOnly",
                f"arn:{stack.partition}:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
            ),
        )
        self.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                "AmazonRDSDataFullAccess",
                f"arn:{stack.partition}:iam::aws:policy/AmazonRDSDataFullAccess",
            )
        )


class CustomPolicy(iam.ManagedPolicy):
    def __init__(
        self,
        scope: Construct,
        id: str,
        actions: Sequence[str],
        resources: Sequence[str],
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            scope,
            id,
            managed_policy_name=f"{prefix}-{name or id}",
            document=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=actions,
                        resources=resources,
                    )
                ]
            ),
        )


class CommonPolicies(Construct):
    AllowCDFAPIAccess: iam.ManagedPolicy
    AllowCDFAPIInvoke: iam.ManagedPolicy
    AllowCDFDescribeStack: iam.ManagedPolicy
    AllowSSMAgentForECSExec: iam.ManagedPolicy
    AllowS3Access: iam.ManagedPolicy
    AllowIoTPublish: iam.ManagedPolicy
    AllowIoTSubscribe: iam.ManagedPolicy
    AllowStaticGtfsS3BucketAccess: iam.ManagedPolicy
    AllowGetRestAPIs: iam.ManagedPolicy
    AllowAuroraAccess: iam.ManagedPolicy

    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        stack = Stack.of(self)

        self.AllowCDFAPIAccess = CustomPolicy(
            self,
            "AllowCDFAPIAccess",
            actions=["execute-api:Invoke", "execute-api:ManageConnections"],
            resources=[
                f"arn:{stack.partition}:execute-api:us-east-1:{stack.account}:*"
            ],
        )

        self.AllowCDFAPIInvoke = CustomPolicy(
            self,
            "AllowCDFAPIInvoke",
            actions=["lambda:InvokeFunction"],
            resources=[
                f"arn:{stack.partition}:lambda:us-east-1:{stack.account}:function:cdf-assetlibrary-stage-LambdaFunction*"
            ],
        )

        self.AllowCDFDescribeStack = CustomPolicy(
            self,
            "AllowCDFDescribeStack",
            actions=["cloudformation:DescribeStacks"],
            resources=[
                f"arn:{stack.partition}:cloudformation:us-east-1:{stack.account}:stack/CDFDeploymentPipelineStack-SAM/*"
            ],
        )

        self.AllowSSMAgentForECSExec = CustomPolicy(
            self,
            "AllowSSMAgentForECSExec",
            actions=[
                "ssmmessages:CreateControlChannel",
                "ssmmessages:CreateDataChannel",
                "ssmmessages:OpenControlChannel",
                "ssmmessages:OpenDataChannel",
            ],
            resources=["*"],
        )

        self.AllowS3Access = CustomPolicy(
            self,
            "AllowS3Access",
            actions=["s3:*"],
            resources=[
                os.environ["RuntimeDeviceMessageBucketARN"],
                f"{os.environ['RuntimeDeviceMessageBucketARN']}:*",
            ],
        )

        self.AllowStaticGtfsS3BucketAccess = CustomPolicy(
            self,
            "AllowStaticGtfsS3BucketAccess",
            actions=["s3:*"],
            resources=[
                f"arn:aws:s3:::{os.environ['STATIC_GTFS_BUCKET_NAME']}",
                f"arn:aws:s3:::{os.environ['STATIC_GTFS_BUCKET_NAME']}/*",
            ],
        )

        self.AllowAuroraAccess = CustomPolicy(
            self,
            "AllowAuroraAccess",
            actions=[
                "aurora:*",
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret",
            ],
            resources=[
                "*",
            ],
        )

        self.AllowIoTPublish = CustomPolicy(
            self,
            "AllowIoTPublish",
            actions=["iot:Connect", "iot:Publish"],
            resources=[
                f"arn:{stack.partition}:iot:*:{stack.account}:client/*",
                f"arn:{stack.partition}:iot:*:{stack.account}:topic/*",
            ],
        )

        self.AllowIoTSubscribe = CustomPolicy(
            self,
            "AllowIoTSubscribe",
            actions=[
                "iot:Connect",
                "iot:Subscribe",
                "iot:Receive",
                "iot:DescribeEndpoint",
            ],
            resources=["*"],
        )

        self.AllowGetRestAPIs = CustomPolicy(
            self,
            "AllowGetRestAPIs",
            actions=["apigateway:GET"],
            resources=["arn:aws:apigateway:*::/restapis"],
        )
