List of resources used for intersection health monitoring:

1. API gateway : A new api gateway only for Intersection Health Monitoring.
2. Lambdas: Two lambdas, one to accommodate GET request, another one to store the hearbeat messages in redshift tables and S3 bucket.
3. Redshift table: To store the heartbeat messages.
4. S3 bucket: To store the heartbeat messages as a backup.
5. Kinesis Data Firehose: To aggregate the heartbeat messages and call the lambda
