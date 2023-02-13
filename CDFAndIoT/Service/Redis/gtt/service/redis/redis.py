import os

import boto3
import redis


class Redis(redis.Redis):
    """Redis subclass that will automatically find the redis host and port by
    envrionment variables or by otherwise finding the shared cluster in elasticache."""

    host: str
    port: int

    def __init__(self, host: str = None, port: int = None, **kwargs) -> None:
        self.host = host or os.getenv("REDIS_HOST") or os.getenv("REDIS_URL")
        self.port = host or os.getenv("REDIS_PORT")
        if (self.host is None) or (self.port is None):
            self.get_elasticache_connection()
        super().__init__(host=self.host, port=self.port, **kwargs)

    def get_elasticache_connection(self):
        res = boto3.client("elasticache").describe_cache_clusters(
            CacheClusterId="sharedcluster"
        )
        try:
            endpoint = res["CacheClusters"][0]["ConfigurationEndpoint"]
            self.host = endpoint["Address"]
            self.port = endpoint["Port"]
        except KeyError:
            raise ValueError(f"Invalid DescribeCacheClusters response: {res}")
