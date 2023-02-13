from typing import Dict, Mapping, Sequence

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct

from .constants import prefix
from .iam import FargateExecutionRole


class Service(Construct):
    task_role: iam.Role
    task_definition: ecs.TaskDefinition
    service: ecs.FargateService

    def __init__(
        self,
        scope: Construct,
        id: str,
        cluster: ecs.Cluster,
        security_group: ec2.SecurityGroup,
        log_group: logs.LogGroup,
        image: str,
        tag: str,
        environment: Mapping[str, str],
        policies: Sequence[iam.ManagedPolicy],
        execution_role: iam.Role,
        public: bool,
        cpu: int = 256,
        memory_limit_mib: int = 512,
    ) -> None:
        super().__init__(scope, id)

        self.task_role = iam.Role(
            self,
            "TaskRole",
            role_name=f"{prefix}-{id}-TaskRole",
            managed_policies=policies,
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        self.task_definition = ecs.TaskDefinition(
            self,
            f"{id}-TaskDefinition",
            family=f"{prefix}-{id}-TaskDefinition",
            cpu=str(cpu),
            memory_mib=str(memory_limit_mib),
            network_mode=ecs.NetworkMode.AWS_VPC,
            compatibility=ecs.Compatibility.FARGATE,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.X86_64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
            execution_role=execution_role,
            task_role=self.task_role,
        )
        self.task_definition.add_container(
            "Container",
            container_name=f"{prefix}-{id}-Container",
            cpu=cpu,
            memory_limit_mib=memory_limit_mib,
            image=ecs.ContainerImage.from_ecr_repository(
                repository=ecr.Repository.from_repository_name(
                    self,
                    f"{id}-ECRRepo",
                    repository_name=image,
                ),
                tag=tag,
            ),
            essential=True,
            linux_parameters=ecs.LinuxParameters(
                self, f"{id}-LinuxParameters", init_process_enabled=True
            ),
            environment=environment,
            logging=ecs.LogDriver.aws_logs(
                log_group=log_group,
                stream_prefix=id,
            ),
        )
        self.service = ecs.FargateService(
            self,
            f"{id}-FargateService",
            service_name=f"{prefix}-{id}-FargateService",
            cluster=cluster,
            assign_public_ip=True,
            desired_count=1,
            enable_execute_command=True,
            task_definition=self.task_definition,
            min_healthy_percent=100,
            max_healthy_percent=200,
            security_groups=[security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnets=(
                    cluster.vpc.public_subnets
                    if public
                    else cluster.vpc.private_subnets
                )
            ),
        )


class FargateServices(Construct):
    vpc: ec2.Vpc
    cluster: ecs.Cluster
    security_group: ec2.SecurityGroup
    execution_role: FargateExecutionRole
    log_group: logs.LogGroup

    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc) -> None:
        super().__init__(scope, id)

        self.vpc = vpc

        self.cluster = ecs.Cluster(
            self,
            "FargateCluster",
            vpc=vpc,
            cluster_name=f"{prefix}-FargateCluster",
        )
        self.security_group = ec2.SecurityGroup(
            self,
            "FargateSecurityGroup",
            vpc=vpc,
            security_group_name=f"{prefix}-FargateSecurityGroup",
        )

        # Allow RDS connections
        # TODO: Reference RDS security group
        self.security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(5432),
        )

        self.execution_role = FargateExecutionRole(self, "FargateExecutionRole")

        self.log_group = logs.LogGroup(
            self, "LogGroup", log_group_name=f"{prefix}-FargateLogGroup"
        )

    def add_service(
        self,
        name: str,
        image: str,
        environment: Dict[str, str],
        policies: Sequence[iam.ManagedPolicy],
        public: bool = False,
        **kwargs,
    ) -> Service:
        image, tag = image.split(":")
        return Service(
            self,
            name,
            cluster=self.cluster,
            security_group=self.security_group,
            log_group=self.log_group,
            image=image,
            tag=tag,
            environment=environment,
            execution_role=self.execution_role,
            policies=policies,
            public=public,
            **kwargs,
        )
