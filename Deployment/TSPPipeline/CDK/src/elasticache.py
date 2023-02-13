from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticache as elasticache
from constructs import Construct

from .constants import prefix


class Elasticache(Construct):
    subnet_group: elasticache.CfnSubnetGroup
    security_group: ec2.SecurityGroup
    cluster: elasticache.CfnCacheCluster

    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc) -> None:
        super().__init__(scope, id)

        self.subnet_group = elasticache.CfnSubnetGroup(
            self,
            "ElasticacheSubnetGroup",
            description="Subnet Group for TSP Elasticache Cluster",
            cache_subnet_group_name=f"{prefix}-ElasticacheSubnetGroup",
            subnet_ids=vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids,
        )
        self.security_group = ec2.SecurityGroup(
            self,
            "ElasticacheSercurityGroup",
            vpc=vpc,
            security_group_name=f"{prefix}-ElasticacheSecurityGroup",
        )
        self.cluster = elasticache.CfnCacheCluster(
            self,
            "ElasticacheCluster",
            engine="redis",
            cache_node_type="cache.t2.micro",
            auto_minor_version_upgrade=True,
            cache_subnet_group_name=self.subnet_group.ref,
            num_cache_nodes=1,
            cluster_name=f"{prefix}-ElasticacheCluster",
            vpc_security_group_ids=[self.security_group.security_group_id],
        )

    def connect_security_group(self, security_group: ec2.SecurityGroup):
        self.security_group.add_ingress_rule(
            ec2.Peer.security_group_id(security_group.security_group_id),
            ec2.Port.tcp(6379),
        )
