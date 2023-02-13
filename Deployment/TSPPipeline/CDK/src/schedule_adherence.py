import os
from typing import Dict, List

from aws_cdk import aws_ec2, aws_events, aws_events_targets
from constructs import Construct
from gtt.constructs.cdk import LocalLambda, LocalLambdaLayer

from .constants import prefix, project_root_dir
from .iam import CommonPolicies

lambda_base_dir = project_root_dir / "TSP/ScheduleAdherence/Lambdas"


class ScheduleAdherence(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.Vpc,
        subnets: List[aws_ec2.Subnet],
        sg: aws_ec2.SecurityGroup,
        env: Dict[str, str],
        common_policies: CommonPolicies,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        static_gtfs_lambda_layer = LocalLambdaLayer(
            self,
            "StaticGtfsLambdaLayer",
            layer_name=f"{prefix}-{id}-StaticGtfs",
            requirements_file=lambda_base_dir / "StaticGtfs/requirements.txt",
        ).layer

        static_gtfs_lamda = LocalLambda(
            self,
            "StaticGtfsLambda",
            function_name=f"{prefix}-{id}-StaticGtfs",
            code_dir=lambda_base_dir / "StaticGtfs",
            layers=[static_gtfs_lambda_layer],
            vpc=vpc,
            vpc_subnets=aws_ec2.SubnetSelection(subnets=(subnets)),
            security_groups=[sg],
            environment=env,
        )

        # Invalidate event
        rule = aws_events.Rule(
            self,
            "InvalidateStaticGts",
            rule_name=f"{prefix}-{id}-InvalidateStaticGtfs",
            description="Invalidate Static GTFS",
            event_pattern=aws_events.EventPattern(source=["StaticGTFSPoller"]),
        )
        rule.add_target(aws_events_targets.LambdaFunction(static_gtfs_lamda.function))

        schedule_status_lambda_layer = LocalLambdaLayer(
            self,
            "ScheduleStatusLambdaLayer",
            layer_name=f"{prefix}",
            requirements_file=lambda_base_dir / "ScheduleStatus/requirements.txt",
        ).layer

        schedule_status_lambda = LocalLambda(
            self,
            "ScheduleStatusLambda",
            function_name=f"{prefix}-{id}-ScheduleStatus",
            code_dir=lambda_base_dir / "ScheduleStatus",
            layers=[schedule_status_lambda_layer],
            vpc=vpc,
            vpc_subnets=aws_ec2.SubnetSelection(subnets=(subnets)),
            security_groups=[sg],
            environment={**env, "AURORA_SECRET_NAME": os.getenv("AURORA_SECRET_NAME")},
        )

        schedule_status_lambda.function.role.add_managed_policy(
            common_policies.AllowAuroraAccess
        )
