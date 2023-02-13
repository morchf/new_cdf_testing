import re
from datetime import timedelta

from airflow.providers.amazon.aws.sensors.s3_prefix import S3PrefixSensor

s3a = re.compile(r"s3a://(?P<bucket>.+?)/(?P<prefix>.+)")


class S3Service:
    def __init__(self, aws_conn_id):
        self.aws_conn_id = aws_conn_id

    def check_prefixes(self, prefixes):
        return [
            S3PrefixSensor(
                bucket_name=m["bucket"],
                prefix=m["prefix"],
                task_id=f"check_prefixes_{table}",
                timeout=timedelta(minutes=30).total_seconds(),
                aws_conn_id=self.aws_conn_id,
                execution_timeout=timedelta(minutes=30),
            )
            for table, prefix in prefixes.items()
            for m in s3a.finditer(prefix)
        ]
