import os

from constructs import Construct
from src.elasticache import Elasticache
from src.fargate import FargateServices
from src.iam import CommonPolicies, CustomPolicy
from src.vehicle_manager import VehicleManager


class Services(Construct):
    def __init__(
        self,
        scope: "Construct",
        id: str,
        fargate_services: FargateServices,
        elasticache: Elasticache,
        common_policies: CommonPolicies,
    ) -> None:
        super().__init__(scope, id)
        common_env = {
            "REGION_NAME": os.environ["RegionName"],
            "AGENCY_NAME": os.environ["AgencyName"],
            "REDIS_URL": elasticache.cluster.attr_redis_endpoint_address,
            "REDIS_PORT": elasticache.cluster.attr_redis_endpoint_port,
        }

        vehicle_manager = VehicleManager(
            self,
            "VehicleManager",
            common_env=common_env,
            common_policies=common_policies,
            execution_role=fargate_services.execution_role,
            log_group=fargate_services.log_group,
        )

        # --- Services ---
        # GTFS Realtime API Poller
        fargate_services.add_service(
            name="GTFSRealtimeAPIPoller",
            image="gtt/tsp-gtfs-realtime:gtfs_realtime_api_poller-latest",
            environment=common_env,
            policies=[
                common_policies.AllowCDFAPIAccess,
                common_policies.AllowCDFAPIInvoke,
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowCDFDescribeStack,
                common_policies.AllowGetRestAPIs,
            ],
        )
        # Agency Manager
        fargate_services.add_service(
            name="AgencyManager",
            image="gtt/tsp-gtfs-realtime:agency_manager-latest",
            environment={
                **common_env,
                "VEHICLE_MANAGER_SUBNET": fargate_services.vpc.public_subnets[
                    0
                ].subnet_id,
                "VEHICLE_MANAGER_SECURITY_GROUP": fargate_services.security_group.security_group_id,
                "VEHICLE_MANAGER_CLUSTER": fargate_services.cluster.cluster_name,
                "VEHICLE_MANAGER_TASK_DEFINITION": vehicle_manager.task_definition.task_definition_arn,
                "VEHICLE_MANAGER_CONTAINER_NAME": vehicle_manager.task_definition.default_container.container_name,
            },
            policies=[
                common_policies.AllowCDFAPIAccess,
                common_policies.AllowCDFAPIInvoke,
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowCDFDescribeStack,
                common_policies.AllowGetRestAPIs,
                CustomPolicy(
                    self,
                    "AllowECSRunVehicleManagerTask",
                    actions=["ecs:RunTask", "iam:PassRole"],
                    resources=[
                        vehicle_manager.task_definition.task_definition_arn,
                        fargate_services.execution_role.role_arn,
                        vehicle_manager.task_definition.task_role.role_arn,
                    ],
                ),
            ],
        )
        # Data Aggregator
        fargate_services.add_service(
            name="DataAggregator",
            image="gtt/tsp-gtfs-realtime:data_aggregator-latest",
            environment={**common_env, "AWS_ENVIRONMENT": os.environ["Env"]},
            policies=[
                common_policies.AllowCDFAPIAccess,
                common_policies.AllowCDFAPIInvoke,
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowS3Access,
            ],
        )
        # Trip Delay Manager
        fargate_services.add_service(
            name="TripDelayManager",
            image="gtt/tsp-gtfs-realtime:trip_delay_manager-latest",
            environment={**common_env},
            policies=[
                common_policies.AllowCDFAPIAccess,
                common_policies.AllowCDFAPIInvoke,
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowCDFDescribeStack,
                common_policies.AllowGetRestAPIs,
            ],
        )
        # Static GTFS Poller Manager
        fargate_services.add_service(
            name="StaticGtfsPoller",
            image="gtt/tsp-gtfs-realtime:static_gtfs_poller-latest",
            environment={
                **common_env,
                "STATIC_GTFS_BUCKET_NAME": os.getenv("STATIC_GTFS_BUCKET_NAME"),
                "AURORA_SECRET_NAME": os.getenv("AURORA_SECRET_NAME"),
            },
            policies=[
                common_policies.AllowCDFAPIAccess,
                common_policies.AllowCDFAPIInvoke,
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowCDFDescribeStack,
                common_policies.AllowGetRestAPIs,
                common_policies.AllowStaticGtfsS3BucketAccess,
                common_policies.AllowAuroraAccess,
                CustomPolicy(
                    self,
                    "AllowEventBridgeInvoke",
                    actions=["events:PutEvents"],
                    resources=["*"],
                ),
            ],
            memory_limit_mib=1024,
        )

        # Schedule Adherence Manager
        fargate_services.add_service(
            name="ScheduleAdherenceManager",
            image="gtt/tsp-gtfs-realtime:schedule_adherence_manager-latest",
            environment={
                **common_env,
                "AURORA_SECRET_NAME": os.getenv("AURORA_SECRET_NAME"),
            },
            policies=[
                common_policies.AllowCDFAPIAccess,
                common_policies.AllowCDFAPIInvoke,
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowCDFDescribeStack,
                common_policies.AllowAuroraAccess,
                common_policies.AllowGetRestAPIs,
            ],
        )

        # Device Enabler
        fargate_services.add_service(
            name="DeviceActivationToggleService",
            image="gtt/tsp-gtfs-realtime:device_activation_toggle_service-latest",
            environment={**common_env},
            policies=[
                common_policies.AllowCDFAPIAccess,
                common_policies.AllowCDFAPIInvoke,
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowCDFDescribeStack,
                common_policies.AllowGetRestAPIs,
                common_policies.AllowIoTPublish,
            ],
        )
