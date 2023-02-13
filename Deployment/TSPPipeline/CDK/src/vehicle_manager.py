from typing import Dict

from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct

from .constants import prefix
from .iam import CommonPolicies, FargateExecutionRole


class VehicleManager(Construct):
    """The vehicle manager is a special kind of fargate service, since we don't
    actually give it a service definition and rely on the Agency Manager to
    start instances of it instead. This will almost certainly change in the
    future to become consistent with the rest of the services, but for now it
    gets its own file"""

    task_definition: ecs.TaskDefinition

    def __init__(
        self,
        scope: Construct,
        id: str,
        common_env: Dict[str, str],
        common_policies: CommonPolicies,
        execution_role: FargateExecutionRole,
        log_group: logs.LogGroup,
    ) -> None:
        super().__init__(scope, id)

        task_role = iam.Role(
            self,
            "VehicleManager-TaskRole",
            role_name=f"{prefix}-VehicleManager-TaskRole",
            managed_policies=[
                common_policies.AllowCDFAPIAccess,
                common_policies.AllowCDFAPIInvoke,
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowGetRestAPIs,
                common_policies.AllowIoTPublish,
            ],
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        self.task_definition = ecs.TaskDefinition(
            self,
            "VehicleManager-TaskDefinition",
            family=f"{prefix}-VehicleManager-TaskDefinition",
            compatibility=ecs.Compatibility.FARGATE,
            cpu="256",
            memory_mib="512",
            network_mode=ecs.NetworkMode.AWS_VPC,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.X86_64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
            execution_role=execution_role,
            task_role=task_role,
        )

        self.task_definition.add_container(
            "Container",
            container_name=f"{prefix}-VehicleManager-Container",
            cpu=256,
            memory_limit_mib=512,
            image=ecs.ContainerImage.from_ecr_repository(
                repository=ecr.Repository.from_repository_name(
                    self,
                    "VehicleManagerECRRepo",
                    repository_name="gtt/tsp-gtfs-realtime",
                ),
                tag="vehicle_manager-latest",
            ),
            essential=True,
            linux_parameters=ecs.LinuxParameters(
                self, f"{id}-LinuxParameters", init_process_enabled=True
            ),
            environment=common_env,
            logging=ecs.LogDriver.aws_logs(
                log_group=log_group,
                stream_prefix=id,
            ),
        )
