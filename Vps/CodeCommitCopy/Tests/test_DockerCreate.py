import docker

dynamoDBregion = "us-east-1"
dynamoDBtable = "globalMacVps"
# docker run ubuntu /bin/echo 'Hello world'
client = docker.from_env()

# table = boto3.resource("dynamodb", region_name=dynamoDBregion).Table(dynamoDBtable)
# r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")

docker_image = "docker.pkg.github.com/gtt/dockersmartcity/smartcityvps:1.0"
client.login(
    "pruthvirajksuresh",
    "3ef13e7d46acf8bb291a96ae8b6044ba71c6520b",
    registry="http://docker.pkg.github.com",
)
client.images.pull(
    "docker.pkg.github.com/gtt/dockersmartcity/smartcityvps",
    tag="1.0",
    auth_config={
        "username": "pruthvirajksuresh",
        "password": "3ef13e7d46acf8bb291a96ae8b6044ba71c6520b",
    },
)
