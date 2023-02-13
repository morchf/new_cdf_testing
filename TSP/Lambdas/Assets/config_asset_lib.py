import os

# Config paramters for http requests
# BASE_URL comes from AWS Console API Gateway - AssetLibrary

BASE_URL = os.environ["CDF_URL"]
ACCEPT = "application/vnd.aws-cdf-v2.0+json"
CONTENT_TYPE = "application/vnd.aws-cdf-v2.0+json"

RT_RADIO_MESSAGE_CLUSTER_URL = "dev-cluster.ibjafd.0001.use1.cache.amazonaws.com"
RT_RADIO_MESSAGE_PORT = "6379"
