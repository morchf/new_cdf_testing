import os

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elasticloadbalancingv2
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as targets
from aws_cdk import aws_servicediscovery as servicediscovery
from constructs import Construct

from .fargate import FargateServices
from .iam import CommonPolicies


class TestServer(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        fargate_services: FargateServices,
        common_policies: CommonPolicies,
    ) -> None:
        super().__init__(scope, id)

        # GTFSRealtimeTestServer Service
        service = fargate_services.add_service(
            "GTFSRealtimeTestServer",
            "gtt/gtfs-realtime-test-server:latest",
            environment={
                "MQTT_TOPICS": "GTT/0537199e-e853-11ec-a8b8-f65b686c7d91/SVR/TSP/2101/+/RTRADIO/+"
            },
            policies=[
                common_policies.AllowSSMAgentForECSExec,
                common_policies.AllowIoTSubscribe,
            ],
            public=True,
        )
        service.task_definition.default_container.add_port_mappings(
            ecs.PortMapping(container_port=8080, host_port=8080)
        )

        # Allow inbound on port 8080
        fargate_services.security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(8080)
        )

        # Set up discovery service and private hosted zone
        dns_namespace = servicediscovery.PrivateDnsNamespace(
            self,
            "PrivateDNSNamespace",
            vpc=fargate_services.vpc,
            name="test-server.local",
        )
        discovery_service = servicediscovery.Service(
            self,
            "DiscoveryService",
            name="gtfs-realtime",
            namespace=dns_namespace,
            description="Discovery Service for the GTFS Realtime Test Server",
            dns_record_type=servicediscovery.DnsRecordType.A,
        )
        service.service.associate_cloud_map_service(
            service=discovery_service, container_port=8080
        )

        # Set up load balancer and route53 record on 'gtfs-realtime-test-server.{Env}gtt.com'
        lb_target_group = elasticloadbalancingv2.NetworkTargetGroup(
            self,
            "TargetGroup",
            port=8080,
            protocol=elasticloadbalancingv2.Protocol.TCP,
            target_group_name="gtfs-rt-test-server-tg-group",
            target_type=elasticloadbalancingv2.TargetType.IP,
            vpc=fargate_services.vpc,
        )
        service.service.attach_to_network_target_group(lb_target_group)
        load_balancer = elasticloadbalancingv2.NetworkLoadBalancer(
            self,
            "LoadBalancer",
            vpc=fargate_services.vpc,
            internet_facing=True,
            load_balancer_name="GTFSRealtimeTestServerELB",
            vpc_subnets=ec2.SubnetSelection(
                subnets=fargate_services.vpc.public_subnets
            ),
        )
        load_balancer.add_listener(
            "TestServerListener",
            port=80,
            protocol=elasticloadbalancingv2.Protocol.TCP,
            default_target_groups=[lb_target_group],
        )
        hosted_zone_name = os.getenv("HostedZoneName")
        route53.ARecord(
            self,
            "Route53Record",
            target=route53.RecordTarget.from_alias(
                targets.LoadBalancerTarget(load_balancer)
            ),
            record_name=f"gtfs-realtime-test-server.{hosted_zone_name}",
            zone=route53.HostedZone.from_lookup(
                self, "HostedZone", domain_name=hosted_zone_name
            ),
        )
