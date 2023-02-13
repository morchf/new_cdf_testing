import os

# Config paramters for http requests
# BASE_URL comes from AWS Console API Gateway - AssetLibrary

BASE_URL = os.environ["CDF_URL"]
ACCEPT = "application/vnd.aws-cdf-v2.0+json"
CONTENT_TYPE = "application/vnd.aws-cdf-v2.0+json"


SQS_REGION_NAME = "us-east-1"

# Elasticache cluster ID
CLUSTER_ID = "Enter Cluster ID here after Elasticache Cluster creation"

# Turn on/off logging
log = False
