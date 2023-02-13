#!/usr/bin/env python3

import os

import aws_cdk
from aws_cdk import Stack, Tags
from aws_cdk import aws_ec2 as ec2
from constructs import Construct
from services import Services
from src.constants import prefix
from src.elasticache import Elasticache
from src.fargate import FargateServices
from src.iam import CommonPolicies
from src.schedule_adherence import ScheduleAdherence
from src.test_server import TestServer


class TSPInCloudStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Env = os.getenv("Env")

        vpc = ec2.Vpc(self, "VPC", cidr="10.0.0.0/24")
        Tags.of(vpc).add("Name", f"{prefix}-{Env}-VPC")

        elasticache = Elasticache(self, "ElasticacheRedis", vpc=vpc)
        fargate_services = FargateServices(self, "FargateServices", vpc=vpc)
        elasticache.connect_security_group(fargate_services.security_group)
        common_policies = CommonPolicies(self, "CommonPolicies")

        if Env == "develop" or Env == "test":
            TestServer(
                self,
                "TestServer",
                fargate_services=fargate_services,
                common_policies=common_policies,
            )

        Services(
            self,
            "Services",
            fargate_services=fargate_services,
            elasticache=elasticache,
            common_policies=common_policies,
        )

        ScheduleAdherence(
            self,
            "ScheduleAdherence",
            common_policies=common_policies,
            vpc=vpc,
            subnets=fargate_services.vpc.private_subnets,
            sg=fargate_services.security_group,
            env={
                "REDIS_URL": elasticache.cluster.attr_redis_endpoint_address,
                "REDIS_PORT": elasticache.cluster.attr_redis_endpoint_port,
            },
        )


app = aws_cdk.App()
TSPInCloudStack(
    app,
    "TSPInCloudStack",
    env=aws_cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
)

app.synth()
